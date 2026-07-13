"""
CDX — Commercial Signal Intelligence Engine
Agent 4: ROI Forecast — "Is It Worth It?"

Builds three investment scenarios (conservative / base / optimistic) using
deterministic Python math from historical campaign data, then calls the LLM
to produce investment narratives and recommendations.

ALL financial calculations are done in Python before the LLM is called.
The LLM interprets and narrates pre-computed numbers only.
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

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT        = os.path.join(DATA_DIR, 'agent4_output.csv')
OUTPUT_DETAIL = os.path.join(DATA_DIR, 'roi_scenarios_detail.csv')

REFERENCE_BUDGET = 150_000

# ─── Prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the ROI Forecast Agent for the Commercial Signal \
Intelligence Engine (CSIE), built by Chromadata for Sony Music Latin.

Your role is to interpret pre-computed financial scenarios and produce clear \
investment recommendations for brand partnership decisions. All ROI figures, \
revenue projections, conversion estimates, and reach numbers were calculated \
deterministically in Python before this call. You never invent, recalculate, \
or modify these numbers.

You explain what the numbers mean for a brand decision-maker. Be direct and \
commercially specific. Flag risks when the data supports it.

Always respond with valid JSON only. No prose, no markdown, no code fences."""

USER_PROMPT_TEMPLATE = """You are producing an investment recommendation for a \
brand considering a partnership with a Latin music artist.

Reference budget: USD {budget:,}
All financial projections below were calculated by the CSIE scoring system \
using historical campaign data. Do not recalculate or modify any figures.

Artist and scenario data:

{context_json}

Based solely on the data above, return a JSON object with exactly these fields:

{{
  "recommended_scenario": "conservative" | "base" | "optimistic",
  "investment_narrative": "<3 sentences. Sentence 1: state the base case ROI \
of {base_roi:.2f}x and projected revenue of USD {base_revenue:,.0f} and what \
that means for a brand at this budget level. Sentence 2: explain why you \
recommend the stated scenario, citing the specific ROI figure for that scenario \
and the artist's momentum_score and cross_platform_score. Sentence 3: frame \
the risk — if risk_flag_score > 60 call it out explicitly, otherwise state the \
confidence level based on data_confidence.>",
  "assumption_1": "<specific, testable assumption the forecast depends on>",
  "assumption_2": "<specific, testable assumption the forecast depends on>",
  "assumption_3": "<specific, testable assumption the forecast depends on>",
  "risk_flag": "none" | "low" | "medium" | "high"
}}

Scenario recommendation guide:
  - Recommend "optimistic" only if cross_platform_score > 80 AND risk_flag_score < 20
  - Recommend "conservative" if data_confidence is LOW or risk_flag_score > 40
  - Otherwise recommend "base"

risk_flag guide:
  - "none":   risk_flag_score == 0 AND data_confidence == HIGH
  - "low":    risk_flag_score <= 20 OR data_confidence == MEDIUM
  - "medium": risk_flag_score <= 60 OR data_confidence == LOW
  - "high":   risk_flag_score > 60

Return JSON only. No explanation outside the JSON object."""


# ─── STEP 1 — Build baseline stats from historical campaigns (pure Python) ───
def build_baseline_stats(campaigns_df: pd.DataFrame) -> dict:
    """
    Compute avg_roi, avg_brand_lift_pts, avg_conversion_rate per brand category.
    All math in Python — never delegated to LLM.
    """
    df = campaigns_df.copy()
    df['roi']             = df['actual_revenue_uplift'] / df['budget_usd']
    df['conversion_rate'] = df['conversions']           / df['budget_usd']

    stats = {}
    for cat, grp in df.groupby('brand_category'):
        stats[cat] = {
            'avg_roi':             round(float(grp['roi'].mean()),             4),
            'avg_brand_lift_pts':  round(float(grp['brand_lift_pts'].mean()),  4),
            'avg_conversion_rate': round(float(grp['conversion_rate'].mean()), 6),
        }
    return stats


# ─── STEP 2 — Build three scenarios for one artist (pure Python) ─────────────
def build_scenarios(
    artist_id: str,
    artist_name: str,
    brand_category: str,
    momentum_score: float,
    cross_platform_score: float,
    total_reach: int,
    baseline: dict,
) -> dict:
    """
    Returns dict with conservative, base, optimistic scenario dicts.
    ALL arithmetic done here — LLM receives only the results.
    """
    cat_stats = baseline.get(brand_category, baseline.get('Tech', {}))
    avg_roi      = cat_stats['avg_roi']
    avg_lift     = cat_stats['avg_brand_lift_pts']
    avg_conv_rt  = cat_stats['avg_conversion_rate']

    momentum_multiplier = 0.8 + (momentum_score / 500.0)

    def _scenario(scale: float, cross_bonus: bool = False) -> dict:
        base_roi = avg_roi * scale
        if cross_bonus and cross_platform_score > 75:
            base_roi *= 1.15
        proj_roi      = round(base_roi * momentum_multiplier, 4)
        proj_revenue  = round(REFERENCE_BUDGET * proj_roi, 2)
        proj_conv     = round(avg_conv_rt * scale * REFERENCE_BUDGET, 1)
        proj_reach    = int(total_reach * scale * 0.40 / 1.0)  # proportional to scale
        # conservative uses 0.40 of total reach, base 0.57, optimistic 0.80
        reach_factors = {0.70: 0.40, 1.00: 0.57, 1.40: 0.80}
        proj_reach    = int(total_reach * reach_factors.get(scale, scale * 0.57))
        proj_lift     = round(avg_lift * scale, 2)
        return {
            'projected_roi':         proj_roi,
            'projected_revenue':     proj_revenue,
            'projected_conversions': proj_conv,
            'projected_reach':       proj_reach,
            'projected_brand_lift':  proj_lift,
        }

    return {
        'conservative': _scenario(0.70),
        'base':         _scenario(1.00),
        'optimistic':   _scenario(1.40, cross_bonus=True),
    }


def build_roi_context(
    a3_row: pd.Series,
    scores_df: pd.DataFrame,
    artist_row: pd.Series,
    baseline: dict,
    scenarios: dict,
) -> dict:
    """Assemble everything into the LLM context dict."""
    aid = a3_row['artist_id']

    artist_scores = scores_df[scores_df['artist_id'] == aid]
    momentum      = round(float(artist_scores['momentum_score'].mean()),      2) if len(artist_scores) > 0 else 0.0
    cross_plat    = round(float(artist_scores['cross_platform_score'].iloc[0]), 2) if len(artist_scores) > 0 else 0.0
    risk_flag     = round(float(artist_scores['risk_flag_score'].iloc[0]),    2) if len(artist_scores) > 0 else 0.0

    brand_cat = str(a3_row['best_brand_category'])
    cat_stats = baseline.get(brand_cat, {})

    return {
        'artist_id':            aid,
        'artist_name':          artist_row['name'],
        'genre':                artist_row['genre'],
        'brand_category':       brand_cat,
        'reference_budget_usd': REFERENCE_BUDGET,
        'data_confidence':      str(a3_row['data_confidence']),
        'total_reach':          int(a3_row['total_reach']),
        'primary_market':       str(a3_row['primary_market']),
        'momentum_score':       momentum,
        'cross_platform_score': cross_plat,
        'risk_flag_score':      risk_flag,
        'historical_baseline': {
            'avg_roi':             cat_stats.get('avg_roi', 0),
            'avg_brand_lift_pts':  cat_stats.get('avg_brand_lift_pts', 0),
            'avg_conversion_rate': cat_stats.get('avg_conversion_rate', 0),
            'note': 'Computed from historical client_campaigns.csv — not invented'
        },
        'scenarios': {
            'conservative': scenarios['conservative'],
            'base':         scenarios['base'],
            'optimistic':   scenarios['optimistic'],
        },
    }


def call_agent_llm(context: dict) -> dict:
    """Call the LLM. Falls back to gpt-4o-mini if default model fails."""
    base_roi     = context['scenarios']['base']['projected_roi']
    base_revenue = context['scenarios']['base']['projected_revenue']
    budget       = context['reference_budget_usd']

    messages = [{"role": "user", "content": USER_PROMPT_TEMPLATE.format(
        context_json=json.dumps(context, indent=2, ensure_ascii=False),
        budget=budget,
        base_roi=base_roi,
        base_revenue=base_revenue,
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


def run_agent() -> list[dict]:
    """Main entry point. Returns list of result dicts."""
    print("━" * 60)
    print("  CSIE — Agent 4: ROI Forecast")
    print("━" * 60)

    # ── Load data ──────────────────────────────────────────────────
    print("Loading data...")
    df_agent3   = pd.read_csv(os.path.join(DATA_DIR, 'agent3_output.csv'))
    df_campaigns= pd.read_csv(os.path.join(DATA_DIR, 'client_campaigns.csv'))
    df_scores   = pd.read_csv(os.path.join(DATA_DIR, 'scores_weekly.csv'))
    df_artists  = pd.read_csv(os.path.join(DATA_DIR, 'artists.csv'))

    latest_week = df_scores['week_date'].max()
    df_scores = df_scores[df_scores['week_date'] == latest_week].copy()

    # ── STEP 1 — Baseline stats (pure Python) ─────────────────────
    baseline = build_baseline_stats(df_campaigns)
    print(f"  Baseline stats computed from {len(df_campaigns)} historical campaigns")
    print(f"  {'Category':<12} {'Avg ROI':>8}  {'Avg Lift':>9}  {'Conv Rate':>10}")
    print("  " + "─" * 44)
    for cat, s in sorted(baseline.items()):
        print(f"  {cat:<12} {s['avg_roi']:>8.3f}x  {s['avg_brand_lift_pts']:>8.1f}pt  {s['avg_conversion_rate']:>10.5f}")
    print()

    results      = []
    detail_rows  = []
    generated_at = datetime.now(timezone.utc).isoformat(timespec='seconds')

    for _, a3_row in df_agent3.iterrows():
        aid  = a3_row['artist_id']
        name = a3_row['artist_name']

        print(f"  {name} ...", end=" ", flush=True)

        artist_rows = df_artists[df_artists['artist_id'] == aid]
        if len(artist_rows) == 0:
            print("✗ not in artists.csv")
            continue
        artist_row = artist_rows.iloc[0]

        # Scores for this artist
        artist_scores = df_scores[df_scores['artist_id'] == aid]
        momentum    = float(artist_scores['momentum_score'].mean())      if len(artist_scores) > 0 else 0.0
        cross_plat  = float(artist_scores['cross_platform_score'].iloc[0]) if len(artist_scores) > 0 else 0.0
        risk_flag_s = float(artist_scores['risk_flag_score'].iloc[0])    if len(artist_scores) > 0 else 0.0
        brand_cat   = str(a3_row['best_brand_category'])
        total_reach = int(a3_row['total_reach'])

        # ── STEP 2 — Build scenarios (pure Python) ─────────────────
        scenarios = build_scenarios(
            aid, name, brand_cat, momentum, cross_plat, total_reach, baseline
        )

        context = build_roi_context(a3_row, df_scores, artist_row, baseline, scenarios)

        # Deterministic values pulled directly from scenarios
        cons  = scenarios['conservative']
        base  = scenarios['base']
        optim = scenarios['optimistic']

        llm_status          = "ok"
        recommended_scenario = "base"
        narrative            = "LLM unavailable"
        assumptions          = ["Campaign execution matches historical averages",
                                 "Audience data reflects current fan composition",
                                 "Market conditions remain stable during campaign"]
        risk_flag_out        = "none"

        try:
            llm = call_agent_llm(context)
            recommended_scenario = llm.get("recommended_scenario", "base").lower()
            narrative            = llm.get("investment_narrative", "").strip()
            raw_a1 = llm.get("assumption_1", assumptions[0])
            raw_a2 = llm.get("assumption_2", assumptions[1])
            raw_a3 = llm.get("assumption_3", assumptions[2])
            assumptions  = [str(raw_a1), str(raw_a2), str(raw_a3)]
            risk_flag_out = llm.get("risk_flag", "none")
            print(f"✓  base ROI={base['projected_roi']:.2f}x  →  {recommended_scenario.upper()}")
        except json.JSONDecodeError as e:
            llm_status = "parse_error"
            print(f"✗ JSON parse error: {e}")
        except Exception as e:
            llm_status = "failed"
            print(f"✗ {type(e).__name__}: {e}")
            traceback.print_exc()

        results.append({
            "artist_id":             aid,
            "artist_name":           name,
            "brand_category":        brand_cat,
            "reference_budget":      REFERENCE_BUDGET,
            "conservative_roi":      cons['projected_roi'],
            "base_roi":              base['projected_roi'],
            "optimistic_roi":        optim['projected_roi'],
            "base_revenue":          base['projected_revenue'],
            "base_conversions":      base['projected_conversions'],
            "base_reach":            base['projected_reach'],
            "base_brand_lift":       base['projected_brand_lift'],
            "recommended_scenario":  recommended_scenario,
            "assumption_1":          assumptions[0],
            "assumption_2":          assumptions[1],
            "assumption_3":          assumptions[2],
            "investment_narrative":  narrative,
            "risk_flag":             risk_flag_out,
            "llm_status":            llm_status,
            "generated_at":          generated_at,
        })

        # Detail rows — one per scenario
        for scenario_name, s in [("conservative", cons), ("base", base), ("optimistic", optim)]:
            detail_rows.append({
                "artist_id":             aid,
                "artist_name":           name,
                "scenario":              scenario_name,
                "projected_roi":         s['projected_roi'],
                "projected_revenue":     s['projected_revenue'],
                "projected_conversions": s['projected_conversions'],
                "projected_reach":       s['projected_reach'],
                "projected_brand_lift":  s['projected_brand_lift'],
            })

    # ── Write main output ──────────────────────────────────────────
    df_out = pd.DataFrame(results, columns=[
        "artist_id", "artist_name", "brand_category", "reference_budget",
        "conservative_roi", "base_roi", "optimistic_roi",
        "base_revenue", "base_conversions", "base_reach", "base_brand_lift",
        "recommended_scenario", "assumption_1", "assumption_2", "assumption_3",
        "investment_narrative", "risk_flag", "llm_status", "generated_at",
    ])
    df_out.to_csv(OUTPUT, index=False)

    # ── Write detail output ────────────────────────────────────────
    df_detail = pd.DataFrame(detail_rows, columns=[
        "artist_id", "artist_name", "scenario",
        "projected_roi", "projected_revenue", "projected_conversions",
        "projected_reach", "projected_brand_lift",
    ])
    df_detail.to_csv(OUTPUT_DETAIL, index=False)

    print(f"\n  Written {len(df_out)} rows → {OUTPUT}")
    print(f"  Written {len(df_detail)} rows → {OUTPUT_DETAIL}")

    # ── Console summary ────────────────────────────────────────────
    avg_base_roi = sum(r['base_roi'] for r in results) / len(results) if results else 0
    best = max(results, key=lambda r: r['base_roi']) if results else None

    print("\n" + "━" * 82)
    print(f"  {'Artist':<26} {'Category':<10} {'C-ROI':>6}  {'B-ROI':>6}  {'O-ROI':>6}  "
          f"{'Revenue (Base)':>16}  {'Rec.'}")
    print("  " + "─" * 78)
    for r in results:
        print(
            f"  {r['artist_name']:<26} {r['brand_category']:<10} "
            f"{r['conservative_roi']:>6.2f}x "
            f"{r['base_roi']:>6.2f}x "
            f"{r['optimistic_roi']:>6.2f}x "
            f"  ${r['base_revenue']:>13,.0f}  "
            f"{r['recommended_scenario'].upper()}"
        )
    print("━" * 82)
    print(f"  Avg base ROI across all artists: {avg_base_roi:.3f}x")
    if best:
        print(f"  Highest base ROI: {best['artist_name']} at {best['base_roi']:.3f}x "
              f"(${best['base_revenue']:,.0f})")
    print("━" * 82)

    return results


if __name__ == "__main__":
    run_agent()
