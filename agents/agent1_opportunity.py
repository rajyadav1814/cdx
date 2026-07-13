"""
CDX — Commercial Signal Intelligence Engine
Agent 1: Opportunity Discovery — "Where to Play"

Identifies the top 10 emerging artists by momentum_score,
calls the LLM to produce opportunity narratives and classifications,
and writes results to data/agent1_output.csv.

The LLM receives only pre-computed scores and writes narratives
interpreting that evidence. It does NOT invent or calculate numbers.
"""

import sys
import os
import json
import traceback
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# ─── Project root on path ────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from model_router import call_llm

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT   = os.path.join(DATA_DIR, 'agent1_output.csv')

# ─── Prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Opportunity Discovery Agent for the Commercial Signal \
Intelligence Engine (CSIE), built by Chromadata for Sony Music Latin.

Your role is to identify and explain commercial partnership opportunities for brands \
wanting to align with Latin music artists. You interpret pre-computed data signals — \
you never invent numbers, estimates, or facts not present in the data provided.

Every score in the context was computed deterministically before you were called. \
Your job is to write clear, evidence-based narratives that explain what the scores mean \
for a brand partnership decision.

Always respond with valid JSON only. No prose, no markdown, no code fences."""

USER_PROMPT_TEMPLATE = """You are evaluating a Latin music artist for brand partnership \
opportunities on behalf of Sony Music Latin's commercial team.

Here is the artist's pre-computed signal data:

{scores_json}

Based solely on the scores and metadata above, return a JSON object with exactly these fields:

{{
  "opportunity_class": "HIGH" | "MEDIUM" | "WATCH",
  "top_territory_1": "<territory code>",
  "top_territory_2": "<territory code>",
  "narrative": "<3 sentences. Sentence 1: explain momentum and chart presence citing \
the momentum_score and cross_platform_score. Sentence 2: explain narrative/cultural \
resonance citing narrative_resonance_score and cultural reach. Sentence 3: state the \
commercial recommendation and risk level citing risk_flag_score.>"
}}

Classification guide (use the scores, not your own knowledge):
  HIGH:  momentum_score >= 40 OR (cross_platform_score >= 80 AND risk_flag_score <= 10)
  MEDIUM: momentum_score >= 25 OR cross_platform_score >= 60
  WATCH:  everything else, or risk_flag_score > 40

Return JSON only. No explanation outside the JSON object."""


def build_scores_context(artist_row: pd.Series, scores_df: pd.DataFrame) -> dict:
    """Build the context dict passed to the LLM for one artist."""
    aid = artist_row['artist_id']

    # All score rows for this artist
    artist_scores = scores_df[scores_df['artist_id'] == aid]

    # Average scores across territories (single-value scores)
    avg_momentum      = round(float(artist_scores['momentum_score'].mean()), 2)
    cross_platform    = round(float(artist_scores['cross_platform_score'].iloc[0]), 2)
    narrative_res     = round(float(artist_scores['narrative_resonance_score'].iloc[0]), 2)
    risk_flag         = round(float(artist_scores['risk_flag_score'].iloc[0]), 2)

    # Top 2 territories by territory_fit_score
    ter_fit = (
        artist_scores[artist_scores['territory_fit_score'] > 0]
        .sort_values('territory_fit_score', ascending=False)
    )
    territories = ter_fit['territory'].tolist()
    top_terr_1 = territories[0] if len(territories) > 0 else "MX"
    top_terr_2 = territories[1] if len(territories) > 1 else "CO"

    top_2_terr_details = []
    for terr in [top_terr_1, top_terr_2]:
        row = artist_scores[artist_scores['territory'] == terr]
        if len(row) > 0:
            top_2_terr_details.append({
                "territory":          terr,
                "territory_fit_score": round(float(row['territory_fit_score'].iloc[0]), 2),
                "momentum_score":      round(float(row['momentum_score'].iloc[0]), 2),
            })

    return {
        "artist_id":                  aid,
        "artist_name":                artist_row['name'],
        "country":                    artist_row['country'],
        "genre":                      artist_row['genre'],
        "label":                      artist_row['label'],
        "spotify_monthly_listeners":  int(artist_row['spotify_monthly_listeners']),
        "scores": {
            "momentum_score":              avg_momentum,
            "cross_platform_score":        cross_platform,
            "narrative_resonance_score":   narrative_res,
            "risk_flag_score":             risk_flag,
        },
        "top_territories": top_2_terr_details,
    }


def call_agent_llm(context: dict) -> dict:
    """Call the LLM with the scores context. Returns parsed JSON dict.
    Tries the default model first; falls back to gpt-4o-mini if it fails."""
    user_msg = USER_PROMPT_TEMPLATE.format(
        scores_json=json.dumps(context, indent=2, ensure_ascii=False)
    )
    messages = [{"role": "user", "content": user_msg}]

    # Try default model, fall back to gpt-4o-mini on any error
    try:
        result = call_llm(
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            max_tokens=400,
        )
    except Exception:
        result = call_llm(
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            model_id="gpt-4o-mini",
            max_tokens=400,
        )
    raw = result["text"].strip()

    # Strip markdown code fences if the LLM added them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def run_agent() -> list[dict]:
    """Main entry point. Returns list of result dicts."""
    print("━" * 60)
    print("  CSIE — Agent 1: Opportunity Discovery")
    print("━" * 60)

    # ── Load data ──────────────────────────────────────────────────
    print("Loading data...")
    df_scores  = pd.read_csv(os.path.join(DATA_DIR, 'scores_weekly.csv'))
    df_artists = pd.read_csv(os.path.join(DATA_DIR, 'artists.csv'))

    # Filter to most recent week
    latest_week = df_scores['week_date'].max()
    df_scores = df_scores[df_scores['week_date'] == latest_week].copy()
    print(f"  Scoring week: {latest_week}  |  {len(df_scores)} rows")

    # ── Rank top 10 artists by average momentum_score ─────────────
    artist_momentum = (
        df_scores.groupby('artist_id')['momentum_score']
        .mean()
        .reset_index()
        .sort_values('momentum_score', ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    print(f"  Top 10 artists identified by momentum_score")

    # ── Process each artist ────────────────────────────────────────
    results = []
    generated_at = datetime.utcnow().isoformat(timespec='seconds') + 'Z'

    for rank_idx, row in artist_momentum.iterrows():
        aid   = row['artist_id']
        rank  = rank_idx + 1
        artist_row = df_artists[df_artists['artist_id'] == aid].iloc[0]
        name  = artist_row['name']

        print(f"\n  [{rank:2d}/10] {name} ...", end=" ", flush=True)

        # Build context
        context = build_scores_context(artist_row, df_scores)

        # Derive top territories from context for output row (fallback values)
        top_t1 = context["top_territories"][0]["territory"] if context["top_territories"] else "MX"
        top_t2 = context["top_territories"][1]["territory"] if len(context["top_territories"]) > 1 else "CO"

        # Call LLM
        llm_status = "ok"
        opp_class  = "MEDIUM"
        narrative  = "LLM unavailable"
        out_t1     = top_t1
        out_t2     = top_t2

        try:
            llm_result = call_agent_llm(context)
            opp_class  = llm_result.get("opportunity_class", "MEDIUM").upper()
            out_t1     = llm_result.get("top_territory_1", top_t1)
            out_t2     = llm_result.get("top_territory_2", top_t2)
            narrative  = llm_result.get("narrative", "").strip()
            print(f"✓ [{opp_class}]")
        except json.JSONDecodeError as e:
            llm_status = "parse_error"
            print(f"✗ JSON parse error: {e}")
        except Exception as e:
            llm_status = "failed"
            print(f"✗ {type(e).__name__}: {e}")
            traceback.print_exc()

        results.append({
            "artist_id":          aid,
            "artist_name":        name,
            "rank":               rank,
            "momentum_score":     round(float(context["scores"]["momentum_score"]), 2),
            "cross_platform_score": round(float(context["scores"]["cross_platform_score"]), 2),
            "risk_flag_score":    round(float(context["scores"]["risk_flag_score"]), 2),
            "opportunity_class":  opp_class,
            "top_territory_1":    out_t1,
            "top_territory_2":    out_t2,
            "narrative":          narrative,
            "llm_status":         llm_status,
            "generated_at":       generated_at,
        })

    # ── Write CSV ──────────────────────────────────────────────────
    df_out = pd.DataFrame(results, columns=[
        "artist_id", "artist_name", "rank", "momentum_score",
        "cross_platform_score", "risk_flag_score", "opportunity_class",
        "top_territory_1", "top_territory_2", "narrative",
        "llm_status", "generated_at",
    ])
    df_out.to_csv(OUTPUT, index=False)
    print(f"\n  Written {len(df_out)} rows → {OUTPUT}")

    # ── Console summary table ──────────────────────────────────────
    print("\n" + "━" * 74)
    print(f"  {'Rank':<5} {'Artist':<26} {'Class':<8} {'Mom':>5} {'XPlt':>5}  {'Territories'}")
    print("  " + "─" * 70)
    for r in results:
        terrs = f"{r['top_territory_1']}, {r['top_territory_2']}"
        print(
            f"  {r['rank']:<5} {r['artist_name']:<26} "
            f"{r['opportunity_class']:<8} "
            f"{r['momentum_score']:>5.1f} "
            f"{r['cross_platform_score']:>5.1f}  "
            f"{terrs}"
        )
    print("━" * 74)

    return results


if __name__ == "__main__":
    run_agent()
