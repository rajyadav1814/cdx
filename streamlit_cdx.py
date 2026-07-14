from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from model_router import call_llm, get_models_for_frontend


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
BRAND_DIR = PROJECT_ROOT / "web" / "public" / "brand"
FONT_DIR = PROJECT_ROOT / "web" / "public" / "fonts"

load_dotenv(PROJECT_ROOT / ".env")


BG_BASE = "#05050A"
BG_SURFACE = "#0D0D18"
BG_SURFACE_2 = "#12121F"
BG_SURFACE_3 = "#1A1A2E"
TEXT_PRIMARY = "#F0EEE8"
TEXT_SECONDARY = "#8A8A9A"
TEXT_MUTED = "#4A4A5E"
BORDER = "rgba(255,255,255,0.06)"
BORDER_HOVER = "rgba(255,255,255,0.10)"
BRAND_RED = "#CC1B1B"
BRAND_RED_LT = "#E83030"
BRAND_GOLD = "#D4A017"
AGENT_COLORS = {
    "agent1": "#1D9E75",
    "agent2": "#8B7FE8",
    "agent3": "#4A9EE8",
    "agent4": "#D4924A",
}

AGENTS = {
    "agent1": {
        "id": 1,
        "key": "agent1",
        "name": "Opportunity Discovery",
        "sub": "Where to Play",
        "color": AGENT_COLORS["agent1"],
        "has_chat": False,
    },
    "agent2": {
        "id": 2,
        "key": "agent2",
        "name": "Strategy Synthesis",
        "sub": "How to Play",
        "color": AGENT_COLORS["agent2"],
        "has_chat": True,
    },
    "agent3": {
        "id": 3,
        "key": "agent3",
        "name": "Audience-Fit",
        "sub": "Who to Play With",
        "color": AGENT_COLORS["agent3"],
        "has_chat": True,
    },
    "agent4": {
        "id": 4,
        "key": "agent4",
        "name": "ROI Forecast",
        "sub": "Is It Worth It?",
        "color": AGENT_COLORS["agent4"],
        "has_chat": True,
    },
}

AGENT_SUGGESTIONS = {
    "agent2": [
        "Which artist is the best fit for a beverage brand?",
        "What activation strategy do you recommend for the top artist?",
        "Which artist has the strongest cultural narrative?",
        "What are the sentiment risks I should know about?",
    ],
    "agent3": [
        "Which artist has the largest audience in Mexico?",
        "How confident are we in the audience data?",
        "Which artist best matches an 18-34 female demographic?",
        "Which markets have the strongest first-party data?",
    ],
    "agent4": [
        "Which artist gives the best ROI at $150K investment?",
        "Walk me through the optimistic scenario for the top artist.",
        "Which artists have risk flags I should be aware of?",
        "How do projections compare to past campaign actuals?",
    ],
}

AGENT_SYSTEM_PROMPTS = {
    "agent2": (
        "You are the Strategy Synthesis Agent for the Commercial Signal Intelligence "
        "Engine (CSIE), built by Chromadata for Sony Music Latin. Your role is to "
        "help brand strategists understand how specific artists can be activated "
        "commercially. Answer questions about brand partnerships, cultural fit, "
        "activation strategies, and campaign approaches. Always cite specific scores "
        "from the provided data. Keep responses to 3-5 sentences unless more detail "
        "is requested."
    ),
    "agent3": (
        "You are the Audience-Fit Agent for the Commercial Signal Intelligence Engine "
        "(CSIE), built by Chromadata for Sony Music Latin. Your role is to help brand "
        "and marketing teams understand the audiences behind each artist. Always "
        "clearly flag proxy vs first-party data. Never present a proxy estimate as a "
        "confirmed fact. Keep responses to 3-5 sentences unless more detail is "
        "requested."
    ),
    "agent4": (
        "You are the ROI Forecast Agent for the Commercial Signal Intelligence Engine "
        "(CSIE), built by Chromadata for Sony Music Latin. Your role is to help "
        "decision-makers understand the financial case for artist partnerships. All "
        "financial numbers were calculated in Python - you interpret, never invent. "
        "Always state the scenario when citing a figure. Keep responses to 3-5 "
        "sentences unless more detail is requested."
    ),
}

AGENT_CSVS = {
    "agent1": ["agent1_output.csv", "scores_weekly.csv", ""],
    "agent2": ["agent2_output.csv", "scores_weekly.csv", "media_mentions.csv"],
    "agent3": ["agent3_output.csv", "scores_weekly.csv", "audience_segments.csv"],
    "agent4": ["agent4_output.csv", "roi_scenarios_detail.csv", "client_campaigns.csv"],
}

MAX_SESSION_MESSAGES = 20


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_font(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "font/woff2" if path.suffix.lower() == ".woff2" else "font/woff"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"url(data:{mime};base64,{payload}) format('{path.suffix.lstrip('.')}')"


def _font_face_css() -> str:
    faces = []
    satoshi_files = [
        ("Satoshi", "400", "normal", "Satoshi-Regular.woff2"),
        ("Satoshi", "500", "normal", "Satoshi-Medium.woff2"),
        ("Satoshi", "700", "normal", "Satoshi-Bold.woff2"),
        ("Satoshi", "900", "normal", "Satoshi-Black.woff2"),
    ]
    for family, weight, style, filename in satoshi_files:
        src = _read_font(FONT_DIR / filename)
        if src:
            faces.append(
                f"""
                @font-face {{
                    font-family: '{family}';
                    src: {src};
                    font-weight: {weight};
                    font-style: {style};
                    font-display: swap;
                }}
                """
            )
    return "\n".join(faces)


def configure_page(page_title: str) -> None:
    st.set_page_config(
        page_title=page_title,
        page_icon=str(BRAND_DIR / "chromadata-icon.png") if (BRAND_DIR / "chromadata-icon.png").exists() else None,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=JetBrains+Mono:wght@400;700&display=swap');
        {_font_face_css()}

        :root {{
            --bg-base: {BG_BASE};
            --bg-surface: {BG_SURFACE};
            --bg-surface2: {BG_SURFACE_2};
            --bg-surface3: {BG_SURFACE_3};
            --text-primary: {TEXT_PRIMARY};
            --text-secondary: {TEXT_SECONDARY};
            --text-muted: {TEXT_MUTED};
            --border-color: {BORDER};
            --border-hover: {BORDER_HOVER};
            --brand-red: {BRAND_RED};
            --brand-red-lt: {BRAND_RED_LT};
            --brand-gold: {BRAND_GOLD};
            --agent-green: {AGENT_COLORS["agent1"]};
            --agent-purple: {AGENT_COLORS["agent2"]};
            --agent-blue: {AGENT_COLORS["agent3"]};
            --agent-amber: {AGENT_COLORS["agent4"]};
        }}

        html, body, [data-testid="stAppViewContainer"] {{
            background: var(--bg-base);
            color: var(--text-primary);
            font-family: 'DM Sans', system-ui, sans-serif;
            font-size: 1.1rem !important;
        }}

        section.main > div {{
            padding-top: 1rem;
        }}

        div[data-testid="stSidebar"] {{
            background: var(--bg-surface);
            border-right: 1px solid var(--border-color);
        }}

        div[data-testid="stHeader"] {{
            background: transparent;
        }}

        div[data-testid="stToolbar"] {{
            right: 1rem;
        }}

        .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
            font-family: 'Satoshi', 'DM Sans', system-ui, sans-serif;
            letter-spacing: -0.02em;
            color: var(--text-primary);
        }}

        .stApp, .stApp p, .stApp li, .stApp label, .stApp span {{
            color: var(--text-primary);
            font-size: 1.1rem !important;
        }}

        [data-testid="stMetric"] {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 2px;
            padding: 0.75rem 0.9rem;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--text-muted);
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--text-primary);
            font-family: 'JetBrains Mono', ui-monospace, monospace;
        }}

        .cdx-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 2px;
            padding: 1rem;
        }}

        .cdx-card:hover {{
            border-color: var(--border-hover);
        }}

        .cdx-card-title {{
            font-family: 'Satoshi', 'DM Sans', sans-serif;
            font-weight: 700;
            font-size: 1.05rem;
            margin: 0;
        }}

        .cdx-label {{
            color: var(--text-muted);
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-weight: 600;
        }}

        .cdx-mono {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
        }}

        .cdx-subtle {{
            color: var(--text-secondary);
        }}

        .cdx-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.25rem 0.55rem;
            border-radius: 2px;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            font-weight: 700;
            border: 1px solid transparent;
        }}

        .cdx-pill.green {{ background: rgba(29, 158, 117, 0.12); color: {AGENT_COLORS["agent1"]}; }}
        .cdx-pill.purple {{ background: rgba(139, 127, 232, 0.12); color: {AGENT_COLORS["agent2"]}; }}
        .cdx-pill.blue {{ background: rgba(74, 158, 232, 0.12); color: {AGENT_COLORS["agent3"]}; }}
        .cdx-pill.gold {{ background: rgba(212, 160, 23, 0.12); color: {AGENT_COLORS["agent4"]}; }}
        .cdx-pill.red {{ background: rgba(204, 27, 27, 0.12); color: {BRAND_RED}; }}
        .cdx-pill.muted {{ background: var(--bg-surface3); color: var(--text-muted); }}

        .cdx-row {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        .cdx-divider {{
            border-top: 1px solid var(--border-color);
            margin: 1rem 0;
        }}

        .cdx-bubble {{
            border: 1px solid var(--border-color);
            background: var(--bg-surface2);
            border-radius: 2px;
            padding: 0.85rem 0.95rem;
            margin-bottom: 0.7rem;
        }}

        .cdx-bubble.user {{
            background: rgba(204, 27, 27, 0.08);
            border-color: rgba(204, 27, 27, 0.16);
        }}

        .cdx-bubble.assistant {{
            background: var(--bg-surface);
        }}

        .cdx-chat-meta {{
            color: var(--text-muted);
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.35rem;
        }}

        .cdx-progress-wrap {{
            width: 100%;
            height: 6px;
            background: var(--bg-surface3);
            border-radius: 999px;
            overflow: hidden;
        }}

        .cdx-progress-bar {{
            height: 100%;
            border-radius: 999px;
        }}

        .stButton > button {{
            background: var(--bg-surface);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 2px;
        }}

        .stButton > button:hover {{
            border-color: var(--border-hover);
        }}

        .stButton > button[kind="primary"] {{
            background: {BRAND_RED};
            color: white;
            border-color: {BRAND_RED};
        }}

        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {{
            background: var(--bg-surface);
            color: var(--text-primary);
            border-color: var(--border-color);
            border-radius: 2px;
        }}

        .stDataFrame, [data-testid="stDataFrame"] {{
            border: 1px solid var(--border-color);
            border-radius: 2px;
            overflow: hidden;
        }}

        [data-testid="stDataFrame"] div[role="grid"] {{
            background: var(--bg-surface);
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.35rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            background: var(--bg-surface);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            border-radius: 2px;
        }}

        .stTabs [aria-selected="true"] {{
            background: rgba(204, 27, 27, 0.12);
            color: var(--text-primary);
            border-color: rgba(204, 27, 27, 0.28);
        }}

        ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg-base); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border-color); border-radius: 2px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--border-hover); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_default_summary() -> dict:
    return {
        "run_timestamp": None,
        "artists_processed": 0,
        "agent1": {
            "high_opportunities": 0,
            "medium_opportunities": 0,
            "watch_opportunities": 0,
            "top_artist": "",
        },
        "agent2": {
            "best_brand_category_distribution": {},
            "most_common_channel": "",
            "briefs_generated": 0,
        },
        "agent3": {
            "avg_reach": 0,
            "high_confidence_pct": 0,
            "medium_confidence_pct": 0,
            "low_confidence_pct": 0,
        },
        "agent4": {
            "avg_base_roi": 0,
            "highest_roi_artist": "",
            "highest_roi_multiple": 0,
            "total_projected_revenue": 0,
        },
    }


@st.cache_data(ttl=30)
def load_summary() -> dict:
    summary_path = DATA_DIR / "pipeline_summary.json"
    if summary_path.exists():
        try:
            return json.loads(summary_path.read_text())
        except Exception:
            pass
    return get_default_summary()


@st.cache_data(ttl=30)
def load_csv_df(filename: str) -> pd.DataFrame:
    if not filename:
        return pd.DataFrame()
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def load_agent_dataframe(agent_key: str) -> pd.DataFrame:
    return load_csv_df(AGENT_CSVS.get(agent_key, [""])[0])


def load_support_dataframe(agent_key: str) -> pd.DataFrame:
    return load_csv_df(AGENT_CSVS.get(agent_key, ["", ""])[1])


def load_extra_dataframe(agent_key: str) -> pd.DataFrame:
    return load_csv_df(AGENT_CSVS.get(agent_key, ["", "", ""])[2])


def load_models() -> dict:
    return get_models_for_frontend()


def get_available_models(provider_id: str | None = None) -> list[dict]:
    providers = load_models().get("providers", {})
    if provider_id:
        return providers.get(provider_id, {}).get("models", [])
    models = []
    for provider in providers.values():
        models.extend(provider.get("models", []))
    return models


def get_default_model_id(provider_id: str | None = None) -> str | None:
    providers = load_models().get("providers", {})
    if provider_id and provider_id in providers:
        models = providers[provider_id].get("models", [])
        default = next((m for m in models if m.get("default")), None)
        if default:
            return default["id"]
        if models:
            return models[0]["id"]
        return None
    for provider in providers.values():
        models = provider.get("models", [])
        default = next((m for m in models if m.get("default")), None)
        if default:
            return default["id"]
        if models:
            return models[0]["id"]
    return None


def format_date(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(str(iso).replace("Z", "+00:00")).strftime("%b %d, %H:%M")
    except Exception:
        return str(iso)


def format_number(value, digits: int = 0) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return "—"


def format_reach(value) -> str:
    try:
        n = float(value)
    except Exception:
        return "—"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:.0f}"


def format_currency(value) -> str:
    try:
        return f"${float(value):,.0f}"
    except Exception:
        return "—"


def bar_width(value: float, max_value: float = 100.0) -> float:
    if max_value <= 0:
        return 0.0
    return max(0.0, min(100.0, (float(value) / max_value) * 100.0))


def pill_html(label: str, tone: str = "muted") -> str:
    return f'<span class="cdx-pill {tone}">{label}</span>'


def card_html(title: str, body: str = "", label: str | None = None, tone: str = "muted") -> str:
    label_html = f'<div class="cdx-label" style="margin-bottom:0.4rem;">{label}</div>' if label else ""
    body_html = f'<div class="cdx-subtle" style="margin-top:0.45rem; line-height:1.55;">{body}</div>' if body else ""
    return f"""
    <div class="cdx-card">
        {label_html}
        <h3 class="cdx-card-title">{title}</h3>
        {body_html}
    </div>
    """


def metric_card(label: str, value: str, helper: str | None = None) -> None:
    st.metric(label, value, help=helper)


def section_header(title: str, subtitle: str | None = None, accent: str | None = None) -> None:
    title_html = title
    if accent:
        title_html = f'<span style="color:{accent}">{title}</span>'
    st.markdown(f'<div class="cdx-label">{subtitle or ""}</div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='margin-top:0.1rem;'>{title_html}</h2>", unsafe_allow_html=True)


def render_brand_image() -> None:
    icon_path = BRAND_DIR / "sonymusiclatin_icon.jpeg"
    if icon_path.exists():
        st.image(str(icon_path), width=34)


def load_agent_context(agent_key: str, artist_filter: str | None = None) -> dict:
    csvs = AGENT_CSVS.get(agent_key, ["", "", ""])

    def _load_df(filename: str) -> pd.DataFrame:
        if not filename:
            return pd.DataFrame()
        df = load_csv_df(filename)
        if df.empty or not artist_filter:
            return df
        name_col = next((c for c in df.columns if c.lower() in ("artist_name", "artist")), None)
        if not name_col:
            return df
        return df[df[name_col].astype(str).str.lower() == artist_filter.lower()]

    df_agent = _load_df(csvs[0])
    df_scores = _load_df(csvs[1])
    df_extra = _load_df(csvs[2])

    return {
        "agent_outputs": df_agent.to_dict(orient="records"),
        "scores": df_scores.to_dict(orient="records"),
        "supplemental": df_extra.to_dict(orient="records"),
        "artist_filter": artist_filter or "all artists",
        "generated_for": "Sony Music Latin - CSIE",
    }


def send_chat_message(
    agent_key: str,
    message: str,
    model_id: str | None,
    artist_filter: str | None = None,
) -> dict:
    trimmed = message.strip()
    if not trimmed:
        return {
            "reply": "Please enter a message.",
            "agent": agent_key,
            "timestamp": now_iso(),
            "error": "empty_message",
        }

    history_key = f"cdx_chat_history_{agent_key}"
    session_id_key = f"cdx_chat_session_{agent_key}"

    if history_key not in st.session_state:
        st.session_state[history_key] = []
    if session_id_key not in st.session_state:
        st.session_state[session_id_key] = str(uuid.uuid4())

    history = st.session_state[history_key]
    session_id = st.session_state[session_id_key]

    history.append({"role": "user", "content": trimmed})
    history[:] = history[-MAX_SESSION_MESSAGES:]

    context_data = load_agent_context(agent_key, artist_filter)
    system_prompt = (
        AGENT_SYSTEM_PROMPTS[agent_key]
        + "\n\nData context:\n"
        + json.dumps(context_data, indent=2, default=str)
    )

    llm_result = call_llm(
        system_prompt=system_prompt,
        messages=history,
        model_id=model_id,
        max_tokens=800,
    )

    reply_text = llm_result["text"]
    history.append({"role": "assistant", "content": reply_text})
    history[:] = history[-MAX_SESSION_MESSAGES:]
    st.session_state[history_key] = history
    st.session_state[session_id_key] = session_id

    return {
        "reply": reply_text,
        "agent": agent_key,
        "model_id": llm_result.get("model", model_id),
        "provider": llm_result.get("provider"),
        "artist_context": artist_filter,
        "session_id": session_id,
        "timestamp": now_iso(),
    }


def clear_chat(agent_key: str) -> None:
    history_key = f"cdx_chat_history_{agent_key}"
    session_id_key = f"cdx_chat_session_{agent_key}"
    st.session_state[history_key] = []
    st.session_state[session_id_key] = str(uuid.uuid4())


def get_chat_history(agent_key: str) -> list[dict]:
    return st.session_state.get(f"cdx_chat_history_{agent_key}", [])


def get_chat_session_id(agent_key: str) -> str:
    return st.session_state.get(f"cdx_chat_session_{agent_key}", "")


def ensure_focus_key(agent_key: str) -> str:
    key = f"cdx_artist_focus_{agent_key}"
    st.session_state.setdefault(key, None)
    return key


def render_chat_panel(
    agent_key: str,
    accent_color: str,
    artist_options: list[str],
    suggested_questions: list[str],
    agent_name: str,
    agent_sub: str,
    initial_message: str | None = None,
) -> tuple[str | None, str | None]:
    focus_key = ensure_focus_key(agent_key)
    artist_filter_key = f"cdx_artist_filter_{agent_key}"
    model_key = f"cdx_model_{agent_key}"
    provider_key = f"cdx_provider_{agent_key}"
    prompt_key = f"cdx_prompt_{agent_key}"

    st.markdown(
        f"""
        <div class="cdx-card" style="border-top: 3px solid {accent_color}; margin-bottom: 0.9rem;">
            <div class="cdx-label">Agent {AGENTS[agent_key]['id']}</div>
            <h3 class="cdx-card-title" style="margin-top: 0.15rem;">{agent_name}</h3>
            <div class="cdx-subtle">{agent_sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    providers = load_models().get("providers", {})
    provider_ids = list(providers.keys())
    if not provider_ids:
        st.warning("No models are configured. Add an API key to `.env` and restart the app.")
        return None, None

    provider_label_map = {pid: providers[pid].get("label", pid) for pid in provider_ids}
    selected_provider = st.radio(
        "Provider",
        options=provider_ids,
        format_func=lambda pid: provider_label_map[pid],
        horizontal=True,
        key=provider_key,
        label_visibility="collapsed",
    )

    models = providers[selected_provider].get("models", [])
    if not models:
        st.warning("No models are available for the selected provider.")
        return None, None

    model_choices = [m["id"] for m in models]
    model_labels = {m["id"]: f"{m['label']} - {m.get('description', '')} ({m.get('tier', '')})" for m in models}
    default_model = next((m["id"] for m in models if m.get("default")), model_choices[0])
    current_model = st.session_state.get(model_key, default_model)
    if current_model not in model_choices:
        current_model = default_model
    selected_model = st.selectbox(
        "Model",
        options=model_choices,
        format_func=lambda mid: model_labels[mid],
        index=model_choices.index(current_model),
        key=model_key,
        label_visibility="collapsed",
    )

    artist_select_options = ["All artists"] + artist_options
    default_artist = st.session_state.get(artist_filter_key, "All artists")
    if default_artist not in artist_select_options:
        default_artist = "All artists"
    selected_artist = st.selectbox(
        "Artist filter",
        options=artist_select_options,
        index=artist_select_options.index(default_artist),
        key=artist_filter_key,
    )
    artist_filter = None if selected_artist == "All artists" else selected_artist
    st.session_state[focus_key] = artist_filter

    if initial_message and not get_chat_history(agent_key):
        st.session_state[prompt_key] = initial_message

    left, right = st.columns([1, 1])
    with left:
        if st.button("Clear conversation", key=f"clear_{agent_key}"):
            clear_chat(agent_key)
            st.rerun()
    with right:
        st.caption(f"Session: {get_chat_session_id(agent_key) or 'new'}")

    history = get_chat_history(agent_key)
    if not history:
        st.info("Ask a question to start the conversation.")

    for message in history:
        role = message.get("role", "assistant")
        bubble_class = "user" if role == "user" else "assistant"
        meta = "You" if role == "user" else "Agent"
        content = message.get("content", "")
        st.markdown(
            f"""
            <div class="cdx-bubble {bubble_class}">
                <div class="cdx-chat-meta">{meta}</div>
                <div style="white-space: pre-wrap; line-height: 1.6;">{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    prompt_value = st.text_area(
        "Message",
        value=st.session_state.get(prompt_key, ""),
        key=prompt_key,
        placeholder=f"Ask {agent_name}…",
        height=100,
        label_visibility="collapsed",
    )

    send_col, continue_col = st.columns([1, 1])
    send_clicked = send_col.button(
        "Send",
        key=f"send_{agent_key}",
        type="primary",
        width="stretch",
    )

    if continue_col.button("Continue", key=f"continue_{agent_key}", width="stretch"):
        target = {
            "agent2": "pages/3_Agent_3_Audience.py",
            "agent3": "pages/4_Agent_4_ROI.py",
            "agent4": "streamlit_app.py",
        }.get(agent_key)
        if target and hasattr(st, "switch_page"):
            st.switch_page(target)

    if send_clicked:
        if not prompt_value.strip():
            st.warning("Type a message first.")
        else:
            with st.spinner("Thinking..."):
                result = send_chat_message(agent_key, prompt_value, selected_model, artist_filter)
            st.session_state[prompt_key] = ""
            st.success(f"Reply received from {result.get('model_id', selected_model)}")
            st.rerun()

    return selected_model, artist_filter


def run_pipeline() -> dict:
    script = PROJECT_ROOT / "agents" / "run_all_agents.py"
    subprocess.Popen(
        [sys.executable, str(script)],
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )
    return {"status": "started", "timestamp": now_iso()}


def render_progress_bar(value: float, max_value: float, color: str, label: str | None = None) -> None:
    width = bar_width(value, max_value)
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:0.6rem;">
            {f'<div class="cdx-label" style="min-width:70px; color:{color};">{label}</div>' if label else ''}
            <div class="cdx-progress-wrap">
                <div class="cdx-progress-bar" style="width:{width}%; background:{color};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

