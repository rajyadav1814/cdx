import sys, os
import json
import subprocess
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from model_router import call_llm, get_models_for_frontend

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

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
    for provider_id, config in MODEL_REGISTRY['providers'].items():
        for model in config['models']:
            if model['id'] == model_id:
                env_key = config.get('env_key', '')
                api_key = os.environ.get(env_key, '')
                placeholder = ('your_anthropic_key_here', 'your_openai_key_here')
                if api_key and api_key not in placeholder:
                    return provider_id, model['label']
                return None, provider_id
    return None, None

def get_model_label(model_id):
    for config in MODEL_REGISTRY['providers'].values():
        for model in config['models']:
            if model['id'] == model_id:
                return model['label']
    return model_id

# ─── request handler ───────────────────────────────────────────────────────────

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/models")
def api_models():
    return get_models_for_frontend()

@app.get("/api/summary")
def api_summary():
    summary_path = os.path.join(DATA_DIR, 'pipeline_summary.json')
    if os.path.exists(summary_path):
        try:
            with open(summary_path) as f:
                return json.load(f)
        except Exception:
            pass
    return get_default_summary()

@app.get("/api/agent1")
def api_agent1():
    return read_csv_as_json('agent1_output.csv')

@app.get("/api/agent2")
def api_agent2():
    return read_csv_as_json('agent2_output.csv')

@app.get("/api/agent3")
def api_agent3():
    return read_csv_as_json('agent3_output.csv')

@app.get("/api/agent4")
def api_agent4():
    return read_csv_as_json('agent4_output.csv')

@app.get("/api/roi_scenarios")
def api_roi_scenarios():
    return read_csv_as_json('roi_scenarios_detail.csv')

@app.get("/api/pipeline_status")
def api_pipeline_status():
    global _pipeline_process, _pipeline_status, _pipeline_last_run
    if _pipeline_process is None:
        return {'status': 'idle', 'last_run': None}
    poll = _pipeline_process.poll()
    if poll is None:
        return {'status': 'running', 'last_run': None}
    elif poll == 0:
        _pipeline_status = 'complete'
        return {'status': 'complete', 'last_run': _pipeline_last_run}
    else:
        _pipeline_status = 'error'
        return {'status': 'error', 'last_run': _pipeline_last_run, 'exit_code': poll}

@app.get("/api/chat/clear")
def api_chat_clear(session_id: str = ''):
    if session_id and session_id in _sessions:
        del _sessions[session_id]
    return {'status': 'cleared', 'session_id': session_id}

@app.post("/api/run_pipeline")
def api_run_pipeline():
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
    return {'status': 'started', 'timestamp': _pipeline_last_run}

class ChatPayload(BaseModel):
    message: str = ""
    model_id: str = None
    artist_filter: str = ""
    session_id: str = None

@app.post("/api/chat/{agent_key}")
def api_chat(agent_key: str, payload: ChatPayload):
    if agent_key not in ('agent2', 'agent3', 'agent4'):
        raise HTTPException(status_code=404, detail="Agent not found")

    message = payload.message.strip()
    model_id = payload.model_id or os.environ.get('DEFAULT_AGENT_MODEL', 'claude-sonnet-4-6')
    artist_filter = payload.artist_filter.strip() or None
    session_id = payload.session_id or str(uuid.uuid4())

    if not message:
        return {
            'reply': 'Please enter a message.',
            'agent': agent_key,
            'session_id': session_id,
            'timestamp': now_iso(),
        }

    if session_id not in _sessions:
        _sessions[session_id] = {
            'history': [],
            'created_at': now_iso(),
            'last_used': now_iso(),
        }
    session = _sessions[session_id]
    session['last_used'] = now_iso()

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
        return {
            'reply':    reply_msg,
            'error':    'model_unavailable',
            'agent':    agent_key,
            'model_id': model_id,
            'session_id': session_id,
            'timestamp': now_iso(),
        }
    model_label = model_label_or_provider

    context_data = load_agent_context(agent_key, artist_filter)
    system_prompt = (
        AGENT_SYSTEM_PROMPTS[agent_key] +
        f"\n\nData context:\n{json.dumps(context_data, indent=2, default=str)}"
    )

    history = session['history']
    history.append({'role': 'user', 'content': message})
    while len(history) > MAX_SESSION_MESSAGES:
        history = history[2:]
    session['history'] = history

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
        return {
            'reply':         'I encountered an error. Please try again or select a different model.',
            'error':         str(exc),
            'agent':         agent_key,
            'model_id':      model_id,
            'session_id':    session_id,
            'message_count': len(session['history']),
            'timestamp':     ts,
        }

    history.append({'role': 'assistant', 'content': reply_text})
    session['history'] = history

    return {
        'reply':         reply_text,
        'agent':         agent_key,
        'model_id':      model_id,
        'provider':      provider,
        'model_label':   model_label,
        'artist_context': artist_filter,
        'session_id':    session_id,
        'message_count': len(history),
        'timestamp':     now_iso(),
    }

@app.get("/{full_path:path}")
def serve_static(full_path: str):
    if full_path == "":
        full_path = "index.html"
        
    filepath = os.path.normpath(os.path.join(WEB_DIST, full_path))
    if not filepath.startswith(os.path.realpath(WEB_DIST)):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not os.path.isfile(filepath):
        filepath = os.path.join(WEB_DIST, 'index.html')

    if os.path.isfile(filepath):
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail="Not Found")

if __name__ == '__main__':
    import uvicorn
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CDX — Commercial Signal Intelligence Engine (CSIE)
Chromadata × Sony Music Latin (FastAPI Edition)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API server:   http://localhost:8000/api/
Static files: ~/cdx/web/dist/ (production build)

Development workflow:
  Terminal 1: python3 main.py   ← FastAPI on :8000
  Terminal 2: cd web && npm run dev   ← React on :5173
  Browser:    http://localhost:5173
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)