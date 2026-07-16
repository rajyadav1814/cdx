"""
CDX — Commercial Signal Intelligence Engine
Agent 3: Audience-Fit — "Who to Play With"

Takes Agent 2's strategy recommendations, enriches with audience segment
data, enforces data confidence rules in code, then calls the LLM to
produce audience fit summaries and target market recommendations.

Data confidence is determined deterministically in Python — the LLM
cannot override it. The LLM receives only pre-computed data and writes
narratives interpreting that evidence.
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

# ─── DB writers & connection ──────────────────────────────────────────────────
from db.writers import upsert_audience_results
from db.readers import read_agent2
from db.connection import get_conn
_DB_ENABLED = True

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT   = os.path.join(DATA_DIR, 'agent3_output.csv')

# ─── Prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Audience-Fit Agent for the Commercial Signal \
Intelligence Engine (CSIE), built by Chromadata for Sony Music Latin.

Your role is to interpret pre-computed audience segment data and explain \
which fan segments are best matched to specific brand categories. You never \
invent numbers, reach estimates, or demographic facts not present in the data.

Data confidence levels are pre-determined by the system:
  HIGH   = 50%+ first-party data
  MEDIUM = 20-50% first-party data
  LOW    = less than 20% first-party data (proxy-only)

When confidence is LOW, you must explicitly flag this in your summary. \
Always respond with valid JSON only. No prose, no markdown, no code fences."""

USER_PROMPT_TEMPLATE = """You are evaluating the audience fit for a brand partnership \
on behalf of Sony Music Latin's commercial team.

Here is the pre-computed audience data for this artist:

{context_json}

Based solely on the data above, return a JSON object with exactly these fields:

{{
  "top_segment_1": "<market code from the data, e.g. MX>",
  "top_segment_2": "<market code from the data>",
  "audience_summary": "<3 sentences. Sentence 1: describe who the primary \
audience is (age, gender split, platform) in the top market, citing the \
estimated_reach figure. Sentence 2: explain why this audience fits the \
brand category, referencing the audience_fit_score and segment demographics. \
Sentence 3: if data_confidence is LOW, explicitly flag 'Note: audience data \
is proxy-estimated only — first-party validation recommended before \
campaign commitment.' Otherwise state the confidence level and what it means.>"
}}

Rules:
- top_segment_1 must be the market with the highest estimated_reach
- top_segment_2 must be the market with the second highest estimated_reach
- audience_summary must cite actual numbers from the data, not invented ones
- if data_confidence is LOW, the third sentence MUST include the proxy flag

Return JSON only. No explanation outside the JSON object."""


# ─── Data confidence rule (enforced in Python, not by LLM) ──────────────────
def compute_data_confidence(segments_df: pd.DataFrame) -> tuple[str, float, float]:
    """
    Returns (confidence_label, proxy_pct, firstparty_pct).
    This is deterministic — the LLM cannot override these values.
    """
    if len(segments_df) == 0:
        return "LOW", 100.0, 0.0

    total = len(segments_df)
    fp_count    = int((segments_df['source_type'] == 'first-party').sum())
    proxy_count = total - fp_count

    firstparty_pct = round(fp_count    / total * 100, 1)
    proxy_pct      = round(proxy_count / total * 100, 1)

    if firstparty_pct >= 50:
        confidence = "HIGH"
    elif proxy_pct > 80:
        confidence = "LOW"
    else:
        confidence = "MEDIUM"

    return confidence, proxy_pct, firstparty_pct


def build_audience_context(
    a2_row: pd.Series,
    segments_df: pd.DataFrame,
    fit_df: pd.DataFrame,
    artist_row: pd.Series,
) -> dict:
    """Assemble audience context for one artist."""
    aid           = a2_row['artist_id']
    best_category = str(a2_row['best_brand_category'])

    # ── Audience segments for this artist ─────────────────────────
    artist_segs = segments_df[segments_df['artist_id'] == aid].copy()

    # ── Data confidence (deterministic) ───────────────────────────
    confidence, proxy_pct, fp_pct = compute_data_confidence(artist_segs)

    # ── Reach aggregation ─────────────────────────────────────────
    total_reach = int(artist_segs['estimated_reach'].sum()) if len(artist_segs) > 0 else 0

    # Sort markets by reach
    market_reach = (
        artist_segs.groupby('market')['estimated_reach'].sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    primary_market   = market_reach.iloc[0]['market'] if len(market_reach) > 0 else "MX"
    secondary_market = market_reach.iloc[1]['market'] if len(market_reach) > 1 else "CO"

    # Primary platform in primary market
    primary_market_segs = artist_segs[artist_segs['market'] == primary_market]
    if len(primary_market_segs) > 0:
        platform_mode = primary_market_segs['platform_primary'].mode()
        primary_platform = str(platform_mode.iloc[0]) if len(platform_mode) > 0 else "Spotify"
    else:
        primary_platform = "Spotify"

    # ── Audience fit score for the best category ──────────────────
    fit_score = 0.0
    if fit_df is not None and not fit_df.empty:
        artist_fits = fit_df[(fit_df['artist_id'] == aid) & (fit_df['brand_category'] == best_category)]
        if not artist_fits.empty:
            fit_score = round(float(artist_fits['fit_score'].mean()), 2)

    # ── Build segment detail list for LLM ─────────────────────────
    seg_details = []
    for _, seg in artist_segs.iterrows():
        seg_details.append({
            "market":           str(seg['market']),
            "segment_name":     str(seg['segment_name']),
            "age_range":        str(seg['age_range']),
            "gender_split_f":   int(seg['gender_split_f']),
            "gender_split_m":   int(seg['gender_split_m']),
            "platform_primary": str(seg['platform_primary']),
            "estimated_reach":  int(seg['estimated_reach']),
            "source_type":      str(seg['source_type']),
        })

    return {
        "artist_id":           aid,
        "artist_name":         artist_row['name'],
        "genre":               artist_row['genre'],
        "best_brand_category": best_category,
        "audience_fit_score":  fit_score,
        "data_confidence":     confidence,
        "proxy_pct":           proxy_pct,
        "firstparty_pct":      fp_pct,
        "total_reach":         total_reach,
        "primary_market":      primary_market,
        "secondary_market":    secondary_market,
        "primary_platform":    primary_platform,
        "segments":            seg_details,
        "recommended_channel": str(a2_row.get('recommended_channel', '')),
        "activation_pillars": [
            str(a2_row.get('activation_pillar_1', '')),
            str(a2_row.get('activation_pillar_2', '')),
            str(a2_row.get('activation_pillar_3', '')),
        ],
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
            max_tokens=500,
        )
    except Exception:
        result = call_llm(
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            model_id="gpt-4o-mini",
            max_tokens=500,
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
    print("  CSIE — Agent 3: Audience-Fit")
    print("━" * 60)

    # ── Load data ──────────────────────────────────────────────────
    print("Loading data...")
    df_agent2 = pd.DataFrame(read_agent2(run_id))
    with get_conn() as conn:
        df_segs    = pd.read_sql("SELECT * FROM audience_segments", conn)
        df_scores  = pd.read_sql("SELECT * FROM scores_weekly", conn)
        df_artists = pd.read_sql("SELECT * FROM artists", conn)
        df_fit     = pd.read_sql("""
            SELECT sw.artist_id, sw.week_date, saf.brand_category, saf.fit_score
            FROM score_audience_fit saf
            JOIN scores_weekly sw ON sw.id = saf.scores_weekly_id
        """, conn)

    latest_week = df_scores['week_date'].max()
    df_fit = df_fit[df_fit['week_date'] == latest_week].copy()

    print(f"  {len(df_agent2)} artists from Agent 2")

    results = []
    generated_at = datetime.now(timezone.utc).isoformat(timespec='seconds')

    for _, a2_row in df_agent2.iterrows():
        aid  = a2_row['artist_id']
        name = a2_row['artist_name']

        print(f"\n  {name} ...", end=" ", flush=True)

        artist_rows = df_artists[df_artists['artist_id'] == aid]
        if len(artist_rows) == 0:
            print("✗ not found in artists.csv")
            continue
        artist_row = artist_rows.iloc[0]

        context = build_audience_context(a2_row, df_segs, df_fit, artist_row)

        # Deterministic values — LLM cannot override these
        confidence    = context["data_confidence"]
        proxy_pct     = context["proxy_pct"]
        fp_pct        = context["firstparty_pct"]
        total_reach   = context["total_reach"]
        primary_mkt   = context["primary_market"]
        secondary_mkt = context["secondary_market"]
        primary_plat  = context["primary_platform"]
        fit_score     = context["audience_fit_score"]
        best_cat      = context["best_brand_category"]

        llm_status = "ok"
        summary    = "LLM unavailable"

        try:
            llm = call_agent_llm(context)
            # LLM may suggest different top segments — accept if valid markets
            valid_markets = {s["market"] for s in context["segments"]}
            llm_seg1 = llm.get("top_segment_1", primary_mkt)
            llm_seg2 = llm.get("top_segment_2", secondary_mkt)
            if llm_seg1 in valid_markets:
                primary_mkt = llm_seg1
            if llm_seg2 in valid_markets:
                secondary_mkt = llm_seg2
            summary = llm.get("audience_summary", "").strip()
            print(f"✓ [{confidence}] {primary_mkt}/{secondary_mkt}")
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
            "best_brand_category": best_cat,
            "total_reach":        total_reach,
            "primary_market":     primary_mkt,
            "secondary_market":   secondary_mkt,
            "primary_platform":   primary_plat,
            "audience_fit_score": fit_score,
            "data_confidence":    confidence,
            "proxy_pct":          proxy_pct,
            "firstparty_pct":     fp_pct,
            "audience_summary":   summary,
            "llm_status":         llm_status,
            "generated_at":       generated_at,
        })

    # ── Write to DB ────────────────────────────────────────────────
    if run_id:
        try:
            upsert_audience_results(run_id, results)
            print(f"\n  [DB] audience results saved for run {run_id}")
        except Exception as _e:
            print(f"\n  [DB] failed to save results: {_e}")
            raise

    # ── Console summary ────────────────────────────────────────────
    print("\n" + "━" * 80)
    print(f"  {'Artist':<26} {'Category':<10} {'Reach':>12}  {'Markets':<12} {'Conf':<8} {'Proxy%':>6}")
    print("  " + "─" * 76)
    for r in results:
        reach_m = f"{r['total_reach']/1_000_000:.1f}M"
        markets = f"{r['primary_market']}/{r['secondary_market']}"
        print(
            f"  {r['artist_name']:<26} {r['best_brand_category']:<10} "
            f"{reach_m:>12}  {markets:<12} {r['data_confidence']:<8} "
            f"{r['proxy_pct']:>5.0f}%"
        )
    print("━" * 80)

    return results


if __name__ == "__main__":
    run_agent()
