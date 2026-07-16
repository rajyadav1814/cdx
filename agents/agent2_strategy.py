"""
CDX — Commercial Signal Intelligence Engine
Agent 2: Strategy Synthesis — "How to Play"

Takes Agent 1's HIGH/MEDIUM artists, enriches with audience fit scores
and cultural topics, then calls the LLM to produce strategic briefs,
brand category recommendations, and activation guidance.

The LLM receives only pre-computed scores and writes strategy narratives
interpreting that evidence. It does NOT invent or calculate numbers.
"""

import sys
import os
import json
import traceback
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv

# ─── Project root on path ────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from model_router import call_llm

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ─── DB writers (optional) ─────────────────────────────────────────────────────────────────
try:
    from db.writers import upsert_strategy_results
    _DB_ENABLED = True
except Exception as _db_err:
    print(f"  [agent2] DB writers unavailable ({_db_err}); CSV-only mode.")
    _DB_ENABLED = False

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT   = os.path.join(DATA_DIR, 'agent2_output.csv')

BRAND_CATEGORIES = ["Beverages", "Fashion", "Tech", "Sport", "Finance"]

# ─── Prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Strategy Synthesis Agent for the Commercial Signal \
Intelligence Engine (CSIE), built by Chromadata for Sony Music Latin.

Your role is to produce brand activation strategies for Latin music artists. \
You interpret pre-computed audience fit scores, cultural resonance data, and \
media signal data to advise Sony Music Latin's commercial team.

You never invent numbers, scores, or facts not present in the provided data. \
Every score was computed deterministically before this call. Your job is to \
translate that evidence into clear, actionable strategic recommendations.

Always respond with valid JSON only. No prose, no markdown, no code fences."""

USER_PROMPT_TEMPLATE = """You are building a brand activation strategy for a Latin \
music artist on behalf of Sony Music Latin's commercial team.

Here is the artist's pre-computed signal data:

{context_json}

Based solely on the data above, return a JSON object with exactly these fields:

{{
  "best_brand_category": "<one of: Beverages | Fashion | Tech | Sport | Finance>",
  "activation_pillars": ["<pillar 1>", "<pillar 2>", "<pillar 3>"],
  "recommended_channel": "<one of: Social-first | Live events | Digital-only | Co-branded content>",
  "sentiment_risk": "<none | low | medium | high — based on sentiment data provided>",
  "strategic_brief": "<4-5 sentences. Sentence 1: summarise the artist's cultural \
position and strongest audience fit score. Sentence 2: explain which brand category \
fits best and why, citing the fit score. Sentence 3: describe the 3 activation \
pillars and how they connect to the cultural topics. Sentence 4: state the \
recommended channel and justify it. Sentence 5 (if any risk): address the \
sentiment risk level and any mitigation.>"
}}

Field rules:
- best_brand_category: pick the category with the highest audience_fit score in the data
- activation_pillars: 3 short phrases (3-5 words each) grounded in the cultural_topics list
- recommended_channel: choose based on platform_primary in the audience data and genre
- sentiment_risk: "none" if all sentiments >= 0.6, "low" if min >= 0.4, "medium" if min >= 0.25, "high" if any < 0.25
- strategic_brief: cite actual score values, do not invent numbers

Return JSON only. No explanation outside the JSON object."""


def build_strategy_context(
    agent1_row: pd.Series,
    scores_df: pd.DataFrame,
    media_df: pd.DataFrame,
    artist_row: pd.Series,
) -> dict:
    """Assemble all signal data for one artist into the LLM context dict."""
    aid = agent1_row['artist_id']

    # ── Audience fit scores (averaged across territories) ─────────────────
    artist_scores = scores_df[scores_df['artist_id'] == aid]
    fit_scores = {}
    for cat in BRAND_CATEGORIES:
        col = f"audience_fit_{cat.lower()}"
        if col in artist_scores.columns and len(artist_scores) > 0:
            fit_scores[cat] = round(float(artist_scores[col].mean()), 2)
        else:
            fit_scores[cat] = 0.0

    best_category = max(fit_scores, key=fit_scores.__getitem__)
    best_fit_score = fit_scores[best_category]

    # Narrative resonance (single value per artist)
    narrative_res = 0.0
    if len(artist_scores) > 0:
        narrative_res = round(float(artist_scores['narrative_resonance_score'].iloc[0]), 2)

    # ── Cultural topics (deduplicated union across all mentions) ──────────
    artist_media = media_df[media_df['artist_id'] == aid]
    all_topics: set[str] = set()
    sentiments: list[float] = []
    for _, m in artist_media.iterrows():
        if pd.notna(m.get('cultural_topics')):
            for t in str(m['cultural_topics']).split(','):
                t = t.strip()
                if t:
                    all_topics.add(t)
        if pd.notna(m.get('sentiment_score')):
            sentiments.append(float(m['sentiment_score']))

    min_sentiment = round(min(sentiments), 3) if sentiments else 1.0
    avg_sentiment = round(sum(sentiments) / len(sentiments), 3) if sentiments else 1.0

    # Primary platform from audience segments (mode across segments)
    platform_primary = "Spotify"
    if 'platform_primary' in scores_df.columns:
        pass  # not in scores_weekly; will use genre inference below

    return {
        "artist_id":    aid,
        "artist_name":  artist_row['name'],
        "country":      artist_row['country'],
        "genre":        artist_row['genre'],
        "label":        artist_row['label'],
        "opportunity_class":   str(agent1_row['opportunity_class']),
        "top_territory_1":     str(agent1_row['top_territory_1']),
        "top_territory_2":     str(agent1_row['top_territory_2']),
        "narrative_resonance_score": narrative_res,
        "audience_fit_scores": fit_scores,
        "best_brand_category": best_category,
        "best_fit_score":      best_fit_score,
        "cultural_topics":     sorted(all_topics),
        "sentiment": {
            "min_score":  min_sentiment,
            "avg_score":  avg_sentiment,
            "n_mentions": len(sentiments),
        },
    }


def call_agent_llm(context: dict) -> dict:
    """Call the LLM. Falls back to gpt-4o-mini if default model fails."""
    messages = [{"role": "user", "content": USER_PROMPT_TEMPLATE.format(
        context_json=json.dumps(context, indent=2, ensure_ascii=False)
    )}]

    try:
        result = call_llm(
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            max_tokens=600,
        )
    except Exception:
        result = call_llm(
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            model_id="gpt-4o-mini",
            max_tokens=600,
        )

    raw = result["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def run_agent(run_id: str | None = None) -> list[dict]:
    """Main entry point. Returns list of result dicts."""
    print("━" * 60)
    print("  CSIE — Agent 2: Strategy Synthesis")
    print("━" * 60)

    # ── Load data ──────────────────────────────────────────────────
    print("Loading data...")
    df_agent1  = pd.read_csv(os.path.join(DATA_DIR, 'agent1_output.csv'))
    df_scores  = pd.read_csv(os.path.join(DATA_DIR, 'scores_weekly.csv'))
    df_media   = pd.read_csv(os.path.join(DATA_DIR, 'media_mentions.csv'))
    df_artists = pd.read_csv(os.path.join(DATA_DIR, 'artists.csv'))

    # Filter to most recent scoring week
    latest_week = df_scores['week_date'].max()
    df_scores = df_scores[df_scores['week_date'] == latest_week].copy()

    # Only HIGH and MEDIUM artists from Agent 1
    eligible = df_agent1[df_agent1['opportunity_class'].isin(['HIGH', 'MEDIUM'])].copy()
    print(f"  {len(eligible)} artists eligible (HIGH or MEDIUM from Agent 1)")

    results = []
    generated_at = datetime.now(timezone.utc).isoformat(timespec='seconds')

    for _, a1_row in eligible.iterrows():
        aid  = a1_row['artist_id']
        name = a1_row['artist_name']
        rank = int(a1_row['rank'])

        print(f"\n  [{rank:2d}] {name} ...", end=" ", flush=True)

        artist_rows = df_artists[df_artists['artist_id'] == aid]
        if len(artist_rows) == 0:
            print("✗ not found in artists.csv")
            continue
        artist_row = artist_rows.iloc[0]

        context = build_strategy_context(a1_row, df_scores, df_media, artist_row)

        # Deterministic fallback values from context
        best_cat   = context["best_brand_category"]
        best_score = context["best_fit_score"]
        llm_status = "ok"
        pillars    = ["Cultural resonance", "Digital engagement", "Regional reach"]
        channel    = "Social-first"
        sentiment_risk = "none"
        brief      = "LLM unavailable"

        try:
            llm = call_agent_llm(context)
            best_cat       = llm.get("best_brand_category", best_cat)
            raw_pillars    = llm.get("activation_pillars", pillars)
            pillars        = raw_pillars if isinstance(raw_pillars, list) else pillars
            channel        = llm.get("recommended_channel", channel)
            sentiment_risk = llm.get("sentiment_risk", "none")
            brief          = llm.get("strategic_brief", "").strip()
            # best_score stays from our deterministic calc — LLM can't change it
            print(f"✓ [{best_cat}] / {channel}")
        except json.JSONDecodeError as e:
            llm_status = "parse_error"
            print(f"✗ JSON parse error: {e}")
        except Exception as e:
            llm_status = "failed"
            print(f"✗ {type(e).__name__}: {e}")
            traceback.print_exc()

        results.append({
            "artist_id":           aid,
            "artist_name":         name,
            "best_brand_category": best_cat,
            "brand_fit_score":     round(best_score, 2),
            "activation_pillar_1": pillars[0] if len(pillars) > 0 else "",
            "activation_pillar_2": pillars[1] if len(pillars) > 1 else "",
            "activation_pillar_3": pillars[2] if len(pillars) > 2 else "",
            "recommended_channel": channel,
            "strategic_brief":     brief,
            "sentiment_risk":      sentiment_risk,
            "llm_status":          llm_status,
            "generated_at":        generated_at,
        })

    # ── Write CSV ──────────────────────────────────────────────────
    df_out = pd.DataFrame(results, columns=[
        "artist_id", "artist_name", "best_brand_category", "brand_fit_score",
        "activation_pillar_1", "activation_pillar_2", "activation_pillar_3",
        "recommended_channel", "strategic_brief", "sentiment_risk",
        "llm_status", "generated_at",
    ])
    df_out.to_csv(OUTPUT, index=False)
    print(f"\n  Written {len(df_out)} rows → {OUTPUT}")

    # ── Write to DB ────────────────────────────────────────────────
    if _DB_ENABLED and run_id:
        try:
            upsert_strategy_results(run_id, results)
            print(f"  [DB] strategy results saved for run {run_id}")
        except Exception as _e:
            print(f"  [DB] failed to save results: {_e}")


    # ── Console summary ────────────────────────────────────────────
    print("\n" + "━" * 78)
    print(f"  {'Artist':<26} {'Category':<12} {'Fit':>5}  {'Channel':<22} {'Risk'}")
    print("  " + "─" * 74)
    for r in results:
        print(
            f"  {r['artist_name']:<26} {r['best_brand_category']:<12} "
            f"{r['brand_fit_score']:>5.1f}  {r['recommended_channel']:<22} "
            f"{r['sentiment_risk']}"
        )
    print("━" * 78)

    return results


if __name__ == "__main__":
    run_agent()
