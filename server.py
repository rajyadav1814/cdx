import sys, os
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
from model_router import call_llm, get_models_for_frontend
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

import json
import subprocess
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

import pandas as pd

DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
WEB_DIST = os.path.join(PROJECT_ROOT, 'web', 'dist')
PORT = int(os.environ.get('PORT', 8000))

# ─── model registry (loaded once at startup) ───────────────────────────────────
with open(os.path.join(PROJECT_ROOT, 'models.json')) as _f:
    MODEL_REGISTRY = json.load(_f)

# ─── pipeline state ────────────────────────────────────────────────────────────
_pipeline_process = None
_pipeline_status = 'idle'
_pipeline_last_run = None

# ─── session store ─────────────────────────────────────────────────────────────
# session_id → { 'history': [...], 'created_at': ISO, 'last_used': ISO }
_sessions = {}
MAX_SESSION_MESSAGES = 20

# ─── content type map ──────────────────────────────────────────────────────────
CONTENT_TYPES = {
    '.html':  'text/html',
    '.js':    'application/javascript',
    '.css':   'text/css',
    '.json':  'application/json',
    '.png':   'image/png',
    '.svg':   'image/svg+xml',
    '.ico':   'image/x-icon',
    '.woff2': 'font/woff2',
    '.woff':  'font/woff',
}

# ─── agent system prompts ──────────────────────────────────────────────────────
AGENT_SYSTEM_PROMPTS = {
    'agent2': (
        "You are the Strategy Synthesis Agent for the Commercial Signal Intelligence "
        "Engine (CSIE), built by Chromadata for Sony Music Latin. Your role is to "
        "help brand strategists understand how specific artists can be activated "
        "commercially. Answer questions about brand partnerships, cultural fit, "
        "activation strategies, and campaign approaches. Always cite specific scores "
        "from the provided data. Keep responses to 3-5 sentences unless more detail "
        "is requested."
    ),
    'agent3': (
        "You are the Audience-Fit Agent for the Commercial Signal Intelligence Engine "
        "(CSIE), built by Chromadata for Sony Music Latin. Your role is to help brand "
        "and marketing teams understand the audiences behind each artist. Always "
        "clearly flag proxy vs first-party data. Never present a proxy estimate as a "
        "confirmed fact. Keep responses to 3-5 sentences unless more detail is "
        "requested."
    ),
    'agent4': (
        "You are the ROI Forecast Agent for the Commercial Signal Intelligence Engine "
        "(CSIE), built by Chromadata for Sony Music Latin. Your role is to help "
        "decision-makers understand the financial case for artist partnerships. All "
        "financial numbers were calculated in Python — you interpret, never invent. "
        "Always state the scenario when citing a figure. Keep responses to 3-5 "
        "sentences unless more detail is requested."
    ),
}

# ─── agent CSV config: [agent_outputs, scores, supplemental] ──────────────────
AGENT_CSVS = {
    'agent2': ['agent2_output.csv', 'scores_weekly.csv',      'media_mentions.csv'],
    'agent3': ['agent3_output.csv', 'scores_weekly.csv',      'audience_segments.csv'],
    'agent4': ['agent4_output.csv', 'roi_scenarios_detail.csv', 'client_campaigns.csv'],
}


# ─── helpers ───────────────────────────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_csv_as_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    try:
        df = pd.read_csv(path)
        return json.loads(df.to_json(orient='records'))
    except Exception:
        return []


def load_agent_context(agent_key, artist_filter=None):
    """
    Load agent CSVs into a structured context_data dict ready for JSON injection.
    Returns: { agent_outputs, scores, supplemental, artist_filter, generated_for }
    """
    csvs = AGENT_CSVS.get(agent_key, ['', '', ''])

    def load_df(filename):
        if not filename:
            return pd.DataFrame()
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            return pd.DataFrame()
        try:
            df = pd.read_csv(path)
            if artist_filter:
                name_col = next(
                    (c for c in df.columns if c.lower() in ('artist_name', 'artist')),
                    None
                )
                if name_col:
                    df = df[df[name_col].str.lower() == artist_filter.lower()]
            return df
        except Exception:
            return pd.DataFrame()

    df_agent  = load_df(csvs[0])
    df_scores = load_df(csvs[1])
    df_extra  = load_df(csvs[2])

    return {
        'agent_outputs': df_agent.to_dict(orient='records'),
        'scores':        df_scores.to_dict(orient='records'),
        'supplemental':  df_extra.to_dict(orient='records'),
        'artist_filter': artist_filter or 'all artists',
        'generated_for': 'Sony Music Latin — CSIE',
    }


def get_default_summary():
    return {
        "run_timestamp": None,
        "artists_processed": 0,
        "agent1": {
            "high_opportunities": 0,
            "medium_opportunities": 0,
            "watch_opportunities": 0,
            "top_artist": ""
        },
        "agent2": {
            "best_brand_category_distribution": {},
            "most_common_channel": "",
            "briefs_generated": 0
        },
        "agent3": {
            "avg_reach": 0,
            "high_confidence_pct": 0,
            "medium_confidence_pct": 0,
            "low_confidence_pct": 0
        },
        "agent4": {
            "avg_base_roi": 0,
            "highest_roi_artist": "",
            "highest_roi_multiple": 0,
            "total_projected_revenue": 0
        }
    }


def validate_model(model_id):
    """
    Returns (provider_id, model_label) if model exists and its API key is configured.
    Returns (None, provider_id) if model exists but API key is missing.
    Returns (None, None) if model_id is not in the registry at all.
    """
    for provider_id, config in MODEL_REGISTRY['providers'].items():
        for model in config['models']:
            if model['id'] == model_id:
                env_key = config.get('env_key', '')
                api_key = os.environ.get(env_key, '')
                placeholder = ('your_anthropic_key_here', 'your_openai_key_here')
                if api_key and api_key not in placeholder:
                    return provider_id, model['label']
                return None, provider_id   # key missing
    return None, None  # unknown model_id


def get_model_label(model_id):
    """Look up display label for a model_id. Returns model_id if not found."""
    for config in MODEL_REGISTRY['providers'].values():
        for model in config['models']:
            if model['id'] == model_id:
                return model['label']
    return model_id


# ─── request handler ───────────────────────────────────────────────────────────

class CSIEHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Suppress default access log noise; print clean lines
        pass

    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({'error': message}, status)

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # ── OPTIONS preflight ──────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    # ── GET ────────────────────────────────────────────────────────────────────
    def do_GET(self):
        path = self.path.split('?')[0]
        query = self.path[len(path):]

        if path.startswith('/api/'):
            self.handle_api_get(path, query)
        else:
            self.serve_static(path)

    # ── POST ───────────────────────────────────────────────────────────────────
    def do_POST(self):
        path = self.path.split('?')[0]
        body = self.read_body()

        if path == '/api/run_pipeline':
            self.api_run_pipeline()
        elif path in ('/api/chat/agent2', '/api/chat/agent3', '/api/chat/agent4'):
            agent_key = path.split('/')[-1]
            self.api_chat(agent_key, body)
        else:
            self.send_error_json('Not found', 404)

    # ── static file serving ───────────────────────────────────────────────────
    def serve_static(self, path):
        if path == '/':
            filepath = os.path.join(WEB_DIST, 'index.html')
        else:
            # Strip leading slash, resolve safely within WEB_DIST
            rel = path.lstrip('/')
            filepath = os.path.normpath(os.path.join(WEB_DIST, rel))
            # Security: ensure resolved path stays within WEB_DIST
            if not filepath.startswith(os.path.realpath(WEB_DIST)):
                self.send_error_json('Forbidden', 403)
                return

        if not os.path.isfile(filepath):
            # SPA fallback
            filepath = os.path.join(WEB_DIST, 'index.html')

        ext = os.path.splitext(filepath)[1].lower()
        content_type = CONTENT_TYPES.get(ext, 'application/octet-stream')

        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_cors()
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error_json(f'Error serving file: {e}', 500)

    # ── API GET dispatch ──────────────────────────────────────────────────────
    def handle_api_get(self, path, query):
        if path == '/api/models':
            self.send_json(get_models_for_frontend())

        elif path == '/api/summary':
            summary_path = os.path.join(DATA_DIR, 'pipeline_summary.json')
            if os.path.exists(summary_path):
                try:
                    with open(summary_path) as f:
                        self.send_json(json.load(f))
                except Exception:
                    self.send_json(get_default_summary())
            else:
                self.send_json(get_default_summary())

        elif path == '/api/agent1':
            self.send_json(read_csv_as_json('agent1_output.csv'))

        elif path == '/api/agent2':
            self.send_json(read_csv_as_json('agent2_output.csv'))

        elif path == '/api/agent3':
            self.send_json(read_csv_as_json('agent3_output.csv'))

        elif path == '/api/agent4':
            self.send_json(read_csv_as_json('agent4_output.csv'))

        elif path == '/api/roi_scenarios':
            self.send_json(read_csv_as_json('roi_scenarios_detail.csv'))

        elif path == '/api/pipeline_status':
            self.api_pipeline_status()

        elif path == '/api/chat/clear':
            # parse session_id from query string
            session_id = ''
            for part in query.lstrip('?').split('&'):
                if part.startswith('session_id='):
                    session_id = part[len('session_id='):]
            if session_id and session_id in _sessions:
                del _sessions[session_id]
            self.send_json({'status': 'cleared', 'session_id': session_id})

        else:
            self.send_error_json('Not found', 404)

    # ── pipeline endpoints ────────────────────────────────────────────────────
    def api_run_pipeline(self):
        global _pipeline_process, _pipeline_status, _pipeline_last_run
        venv_python = os.path.join(PROJECT_ROOT, 'venv', 'bin', 'python3')
        script = os.path.join(PROJECT_ROOT, 'agents', 'run_all_agents.py')
        _pipeline_process = subprocess.Popen(
            [venv_python, script],
            cwd=PROJECT_ROOT,
            env={**os.environ, 'PYTHONPATH': PROJECT_ROOT}
        )
        _pipeline_status = 'running'
        _pipeline_last_run = now_iso()
        self.send_json({'status': 'started', 'timestamp': _pipeline_last_run})

    def api_pipeline_status(self):
        global _pipeline_process, _pipeline_status, _pipeline_last_run
        if _pipeline_process is None:
            self.send_json({'status': 'idle', 'last_run': None})
            return
        poll = _pipeline_process.poll()
        if poll is None:
            self.send_json({'status': 'running', 'last_run': None})
        elif poll == 0:
            _pipeline_status = 'complete'
            self.send_json({'status': 'complete', 'last_run': _pipeline_last_run})
        else:
            _pipeline_status = 'error'
            self.send_json({'status': 'error', 'last_run': _pipeline_last_run,
                            'exit_code': poll})

    # ── chat endpoint ─────────────────────────────────────────────────────────
    def api_chat(self, agent_key, body):
        # Step 1 — parse body
        message       = body.get('message', '').strip()
        model_id      = (body.get('model_id') or
                         os.environ.get('DEFAULT_AGENT_MODEL', 'claude-sonnet-4-6'))
        artist_filter = body.get('artist_filter', '').strip() or None
        session_id    = body.get('session_id') or str(uuid.uuid4())

        if not message:
            self.send_json({
                'reply': 'Please enter a message.',
                'agent': agent_key,
                'session_id': session_id,
                'timestamp': now_iso(),
            })
            return

        # Step 2 — get or create session
        if session_id not in _sessions:
            _sessions[session_id] = {
                'history': [],
                'created_at': now_iso(),
                'last_used': now_iso(),
            }
        session = _sessions[session_id]
        session['last_used'] = now_iso()

        # Step 3 — validate model
        provider, model_label_or_provider = validate_model(model_id)
        if provider is None:
            if model_label_or_provider:
                reply_msg = (
                    f"That model is not available. Check your API key for "
                    f"{model_label_or_provider} in ~/cdx/.env and restart the server."
                )
            else:
                reply_msg = (
                    "That model is not available. Check your API key in "
                    "~/cdx/.env and restart the server."
                )
            self.send_json({
                'reply':    reply_msg,
                'error':    'model_unavailable',
                'agent':    agent_key,
                'model_id': model_id,
                'session_id': session_id,
                'timestamp': now_iso(),
            })
            return
        model_label = model_label_or_provider  # valid path: this is the label

        # Step 4 — load and filter CSVs
        context_data = load_agent_context(agent_key, artist_filter)

        # Step 5 — build system prompt
        system_prompt = (
            AGENT_SYSTEM_PROMPTS[agent_key] +
            f"\n\nData context:\n{json.dumps(context_data, indent=2, default=str)}"
        )

        # Step 6 — append user message and trim history
        history = session['history']
        history.append({'role': 'user', 'content': message})
        while len(history) > MAX_SESSION_MESSAGES:
            history = history[2:]  # drop oldest user+assistant pair
        session['history'] = history

        # Step 7 — call LLM
        try:
            llm_result = call_llm(
                system_prompt=system_prompt,
                messages=history,
                model_id=model_id,
                max_tokens=800,
            )
            reply_text = llm_result['text']
        except Exception as exc:
            ts = now_iso()
            print(f"[{ts}] chat/{agent_key} LLM error: {exc}")
            self.send_json({
                'reply':         'I encountered an error. Please try again or select a different model.',
                'error':         str(exc),
                'agent':         agent_key,
                'model_id':      model_id,
                'session_id':    session_id,
                'message_count': len(session['history']),
                'timestamp':     ts,
            })
            return

        # Step 8 — append assistant reply
        history.append({'role': 'assistant', 'content': reply_text})
        session['history'] = history

        # Steps 9-10 — return response
        self.send_json({
            'reply':         reply_text,
            'agent':         agent_key,
            'model_id':      model_id,
            'provider':      provider,
            'model_label':   model_label,
            'artist_context': artist_filter,
            'session_id':    session_id,
            'message_count': len(history),
            'timestamp':     now_iso(),
        })


# ─── entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CDX — Commercial Signal Intelligence Engine (CSIE)
Chromadata × Sony Music Latin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API server:   http://localhost:8000/api/
Static files: ~/cdx/web/dist/ (production build)

Development workflow:
  Terminal 1: python3 web/server.py   ← API on :8000
  Terminal 2: cd web && npm run dev   ← React on :5173
  Browser:    http://localhost:5173
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    server = HTTPServer(('', PORT), CSIEHandler)
    print(f'Listening on http://localhost:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
        server.server_close()
