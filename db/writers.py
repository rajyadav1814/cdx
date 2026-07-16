"""
CDX — Database Writer Helpers

All writes use psycopg2.extras.execute_values for true bulk inserts —
a single SQL statement per table, regardless of row count.

Performance vs. old row-by-row approach (100 artists × 8 territories):
  upsert_scores_weekly: ~4 800 round-trips → 2 round-trips
  upsert_*_results:     N round-trips       → 1 round-trip each

Import pattern:
    from db.writers import upsert_artists, upsert_scores_weekly, ...
"""

import json
from typing import Any

from psycopg2.extras import execute_values   # bulk INSERT helper
from db.connection import get_conn

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _jsonb(value: Any) -> str | None:
    """Serialise a Python list/dict to a JSON string for psycopg2."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _batch_upsert(sql: str, rows: list[dict], keys: list[str],
                  *, page_size: int = 500) -> int:
    """
    Generic batch upsert using execute_values.
    sql must use a VALUES %s placeholder (no individual %s tokens).
    Returns number of input rows.
    """
    if not rows:
        return 0
    params = [tuple(r.get(k) for k in keys) for r in rows]
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, params, page_size=page_size)
    return len(rows)


# ---------------------------------------------------------------------------
# 1. artists
# ---------------------------------------------------------------------------

_UPSERT_ARTISTS = """
INSERT INTO artists
    (artist_id, name, country, genre, label,
     spotify_monthly_listeners, social_blade_followers,
     youtube_subscribers, updated_at)
VALUES %s
ON CONFLICT (artist_id) DO UPDATE SET
    name                      = EXCLUDED.name,
    country                   = EXCLUDED.country,
    genre                     = EXCLUDED.genre,
    label                     = EXCLUDED.label,
    spotify_monthly_listeners = EXCLUDED.spotify_monthly_listeners,
    social_blade_followers    = EXCLUDED.social_blade_followers,
    youtube_subscribers       = EXCLUDED.youtube_subscribers,
    updated_at                = now();
"""

_ARTIST_KEYS = [
    "artist_id", "name", "country", "genre", "label",
    "spotify_monthly_listeners", "social_blade_followers", "youtube_subscribers",
]


def upsert_artists(rows: list[dict]) -> int:
    """Batch-upsert artists. Appends `now()` for updated_at server-side."""
    if not rows:
        return 0
    params = [tuple(r.get(k) for k in _ARTIST_KEYS) + ("now()",) for r in rows]
    # updated_at is a literal — use a custom template
    sql = """
    INSERT INTO artists
        (artist_id, name, country, genre, label,
         spotify_monthly_listeners, social_blade_followers,
         youtube_subscribers, updated_at)
    VALUES %s
    ON CONFLICT (artist_id) DO UPDATE SET
        name                      = EXCLUDED.name,
        country                   = EXCLUDED.country,
        genre                     = EXCLUDED.genre,
        label                     = EXCLUDED.label,
        spotify_monthly_listeners = EXCLUDED.spotify_monthly_listeners,
        social_blade_followers    = EXCLUDED.social_blade_followers,
        youtube_subscribers       = EXCLUDED.youtube_subscribers,
        updated_at                = now();
    """
    params = [tuple(r.get(k) for k in _ARTIST_KEYS) for r in rows]
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur, sql, params,
                template="(%s,%s,%s,%s,%s,%s,%s,%s,now())",
                page_size=500,
            )
    return len(rows)


# ---------------------------------------------------------------------------
# 2. spotify_chart_entries
# ---------------------------------------------------------------------------

_UPSERT_SPOTIFY = """
INSERT INTO spotify_chart_entries
    (chart_date, territory, artist_id, track_title,
     chart_position, streams_estimate, peak_position, weeks_on_chart)
VALUES %s
ON CONFLICT (chart_date, territory, artist_id, track_title) DO UPDATE SET
    chart_position   = EXCLUDED.chart_position,
    streams_estimate = EXCLUDED.streams_estimate,
    peak_position    = EXCLUDED.peak_position,
    weeks_on_chart   = EXCLUDED.weeks_on_chart;
"""

_SPOTIFY_KEYS = [
    "date", "territory", "artist_id", "track_title",
    "chart_position", "streams_estimate", "peak_position", "weeks_on_chart",
]


def upsert_spotify_charts(rows: list[dict]) -> int:
    return _batch_upsert(_UPSERT_SPOTIFY, rows, _SPOTIFY_KEYS)


# ---------------------------------------------------------------------------
# 3. kworb_crosschart
# ---------------------------------------------------------------------------

_UPSERT_KWORB = """
INSERT INTO kworb_crosschart
    (chart_date, artist_id, platforms_charting,
     peak_position_global, weeks_on_chart, territories_charting)
VALUES %s
ON CONFLICT (chart_date, artist_id) DO UPDATE SET
    platforms_charting   = EXCLUDED.platforms_charting,
    peak_position_global = EXCLUDED.peak_position_global,
    weeks_on_chart       = EXCLUDED.weeks_on_chart,
    territories_charting = EXCLUDED.territories_charting;
"""

_KWORB_KEYS = [
    "date", "artist_id", "platforms_charting",
    "peak_position_global", "weeks_on_chart", "territories_charting",
]


def upsert_kworb_crosschart(rows: list[dict]) -> int:
    return _batch_upsert(_UPSERT_KWORB, rows, _KWORB_KEYS)


# ---------------------------------------------------------------------------
# 4. social_growth
# ---------------------------------------------------------------------------

_UPSERT_SOCIAL = """
INSERT INTO social_growth
    (growth_date, artist_id, platform,
     followers_start, followers_end, growth_pct, engagement_rate)
VALUES %s
ON CONFLICT (growth_date, artist_id, platform) DO UPDATE SET
    followers_start = EXCLUDED.followers_start,
    followers_end   = EXCLUDED.followers_end,
    growth_pct      = EXCLUDED.growth_pct,
    engagement_rate = EXCLUDED.engagement_rate;
"""

_SOCIAL_KEYS = [
    "date", "artist_id", "platform",
    "followers_start", "followers_end", "growth_pct", "engagement_rate",
]


def upsert_social_growth(rows: list[dict]) -> int:
    return _batch_upsert(_UPSERT_SOCIAL, rows, _SOCIAL_KEYS)


# ---------------------------------------------------------------------------
# 5. media_mentions  (truncate-then-insert pattern)
# ---------------------------------------------------------------------------

_INSERT_MEDIA = """
INSERT INTO media_mentions
    (mention_date, artist_id, source, headline, sentiment_score, cultural_topics)
VALUES %s
ON CONFLICT DO NOTHING;
"""


def insert_media_mentions(rows: list[dict]) -> int:
    """
    Batch-insert media mentions.
    Call truncate_media_mentions() first for a full refresh.
    cultural_topics is normalised: comma-string → JSON array.
    """
    if not rows:
        return 0

    def _topics(val):
        if not val:
            return "[]"
        if isinstance(val, list):
            return json.dumps(val)
        # comma-separated string
        return json.dumps([t.strip() for t in str(val).split(",") if t.strip()])

    params = [
        (
            r.get("date"),
            r.get("artist_id"),
            r.get("source"),
            r.get("headline"),
            r.get("sentiment_score"),
            _topics(r.get("cultural_topics")),
        )
        for r in rows
    ]
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, _INSERT_MEDIA, params, page_size=500)
    return len(rows)


def truncate_media_mentions() -> None:
    """Remove all rows before a full regeneration run."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE media_mentions;")


# ---------------------------------------------------------------------------
# 6. audience_segments
# ---------------------------------------------------------------------------

_UPSERT_AUDIENCE = """
INSERT INTO audience_segments
    (artist_id, market, segment_name, age_range,
     gender_split_f, gender_split_m, platform_primary,
     estimated_reach, source_type)
VALUES %s
ON CONFLICT (artist_id, market, segment_name) DO UPDATE SET
    age_range        = EXCLUDED.age_range,
    gender_split_f   = EXCLUDED.gender_split_f,
    gender_split_m   = EXCLUDED.gender_split_m,
    platform_primary = EXCLUDED.platform_primary,
    estimated_reach  = EXCLUDED.estimated_reach,
    source_type      = EXCLUDED.source_type;
"""

_AUDIENCE_KEYS = [
    "artist_id", "market", "segment_name", "age_range",
    "gender_split_f", "gender_split_m", "platform_primary",
    "estimated_reach", "source_type",
]


def upsert_audience_segments(rows: list[dict]) -> int:
    return _batch_upsert(_UPSERT_AUDIENCE, rows, _AUDIENCE_KEYS)


# ---------------------------------------------------------------------------
# 7. client_campaigns
# ---------------------------------------------------------------------------

_UPSERT_CAMPAIGNS = """
INSERT INTO client_campaigns
    (campaign_id, brand_name, brand_category, artist_id, territory,
     budget_usd, actual_revenue_uplift, conversions, reach_actual,
     brand_lift_pts, campaign_start, campaign_end)
VALUES %s
ON CONFLICT (campaign_id) DO UPDATE SET
    brand_name            = EXCLUDED.brand_name,
    brand_category        = EXCLUDED.brand_category,
    artist_id             = EXCLUDED.artist_id,
    territory             = EXCLUDED.territory,
    budget_usd            = EXCLUDED.budget_usd,
    actual_revenue_uplift = EXCLUDED.actual_revenue_uplift,
    conversions           = EXCLUDED.conversions,
    reach_actual          = EXCLUDED.reach_actual,
    brand_lift_pts        = EXCLUDED.brand_lift_pts,
    campaign_start        = EXCLUDED.campaign_start,
    campaign_end          = EXCLUDED.campaign_end;
"""

_CAMPAIGN_KEYS = [
    "campaign_id", "brand_name", "brand_category", "artist_id", "territory",
    "budget_usd", "actual_revenue_uplift", "conversions", "reach_actual",
    "brand_lift_pts", "campaign_start", "campaign_end",
]


def upsert_client_campaigns(rows: list[dict]) -> int:
    return _batch_upsert(_UPSERT_CAMPAIGNS, rows, _CAMPAIGN_KEYS)


# ---------------------------------------------------------------------------
# 8. scores_weekly + score_audience_fit  ← OPTIMISED BATCH INSERT
#
# Old approach: N × execute() for scores  +  N×5 × execute() for fit
#               = ~4 800 round-trips for 800 rows
#
# New approach: 1 × execute_values for scores (RETURNING all ids)
#               1 × execute_values for ALL fit rows
#               = 2 round-trips, regardless of dataset size
# ---------------------------------------------------------------------------

_UPSERT_SCORES_BATCH = """
INSERT INTO scores_weekly
    (artist_id, territory, week_date,
     momentum_score, territory_fit_score, cross_platform_score,
     narrative_resonance_score, risk_flag_score)
VALUES %s
ON CONFLICT (artist_id, territory, week_date) DO UPDATE SET
    momentum_score            = EXCLUDED.momentum_score,
    territory_fit_score       = EXCLUDED.territory_fit_score,
    cross_platform_score      = EXCLUDED.cross_platform_score,
    narrative_resonance_score = EXCLUDED.narrative_resonance_score,
    risk_flag_score           = EXCLUDED.risk_flag_score
RETURNING id, artist_id, territory, week_date::text;
"""

_UPSERT_FIT_BATCH = """
INSERT INTO score_audience_fit (scores_weekly_id, brand_category, fit_score)
VALUES %s
ON CONFLICT (scores_weekly_id, brand_category) DO UPDATE SET
    fit_score = EXCLUDED.fit_score;
"""

_BRAND_CATEGORIES = ["Beverages", "Fashion", "Tech", "Sport", "Finance"]


def upsert_scores_weekly(rows: list[dict]) -> int:
    """
    Batch-upsert scores_weekly AND score_audience_fit in exactly 2 SQL calls.

    Each row dict must contain:
        artist_id, territory, week_date,
        momentum_score, territory_fit_score, cross_platform_score,
        narrative_resonance_score, risk_flag_score,
        audience_fit_beverages, audience_fit_fashion, audience_fit_tech,
        audience_fit_sport, audience_fit_finance
    """
    if not rows:
        return 0

    # ── Step 1: build scores params ──────────────────────────────────────────
    scores_params = [
        (
            r["artist_id"],
            r["territory"],
            r["week_date"],
            r.get("momentum_score"),
            r.get("territory_fit_score"),
            r.get("cross_platform_score"),
            r.get("narrative_resonance_score"),
            r.get("risk_flag_score"),
        )
        for r in rows
    ]

    with get_conn() as conn:
        with conn.cursor() as cur:

            # ── Step 2: single batch upsert, get back all IDs ─────────────
            returned = execute_values(
                cur,
                _UPSERT_SCORES_BATCH,
                scores_params,
                fetch=True,          # returns RETURNING rows directly
                page_size=500,
            )
            # NOTE: execute_values(fetch=True) returns the rows as its return value.
            #       Do NOT call cur.fetchall() — the cursor is already exhausted.

            # Build lookup: (artist_id, territory, week_date_str) → scores_weekly id
            id_map: dict[tuple, int] = {
                (str(r[1]), str(r[2]), str(r[3])): r[0]
                for r in returned
            }

            # ── Step 3: build all audience_fit rows in one pass ───────────
            fit_params: list[tuple] = []
            for row in rows:
                key = (str(row["artist_id"]), str(row["territory"]), str(row["week_date"]))
                scores_id = id_map.get(key)
                if scores_id is None:
                    continue
                for cat in _BRAND_CATEGORIES:
                    fit_val = row.get(f"audience_fit_{cat.lower()}")
                    if fit_val is not None:
                        fit_params.append((scores_id, cat, fit_val))

            # ── Step 4: single batch upsert for all fit rows ──────────────
            if fit_params:
                execute_values(
                    cur,
                    _UPSERT_FIT_BATCH,
                    fit_params,
                    template="(%s, %s::brand_category_enum, %s)",
                    page_size=1000,
                )

    return len(rows)


# ---------------------------------------------------------------------------
# 9. pipeline_runs
# ---------------------------------------------------------------------------

def create_pipeline_run(triggered_by: str = "system") -> str:
    """Insert a new pipeline_runs row in 'running' state. Returns run_id (UUID str)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO pipeline_runs (status, triggered_by) "
                "VALUES ('running', %s) RETURNING run_id::text;",
                [triggered_by],
            )
            return cur.fetchone()[0]


def complete_pipeline_run(run_id: str, exit_code: int = 0) -> None:
    """Mark a pipeline run as complete."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pipeline_runs "
                "SET status = 'complete', completed_at = now(), exit_code = %s "
                "WHERE run_id = %s;",
                [exit_code, run_id],
            )


def fail_pipeline_run(run_id: str, exit_code: int = 1) -> None:
    """Mark a pipeline run as errored."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pipeline_runs "
                "SET status = 'error', completed_at = now(), exit_code = %s "
                "WHERE run_id = %s;",
                [exit_code, run_id],
            )


# ---------------------------------------------------------------------------
# 10. Agent result tables — all batch-inserted
# ---------------------------------------------------------------------------

_CLASS_MAP    = {"HIGH": "HIGH", "MEDIUM": "MEDIUM", "WATCH": "LOW", "LOW": "LOW"}
_RISK_MAP     = {"none": "low", "low": "low", "medium": "medium", "high": "high"}
_SCENARIO_MAP = {"conservative": "conservative", "base": "base", "optimistic": "optimistic"}

# ── Agent 1: Opportunity ──────────────────────────────────────────────────────

_UPSERT_OPP = """
INSERT INTO agent_opportunity_results
    (run_id, artist_id, rank, momentum_score, cross_platform_score,
     risk_flag_score, opportunity_class, top_territory_1, top_territory_2,
     narrative, llm_status, generated_at)
VALUES %s
ON CONFLICT (run_id, artist_id) DO UPDATE SET
    rank                 = EXCLUDED.rank,
    momentum_score       = EXCLUDED.momentum_score,
    cross_platform_score = EXCLUDED.cross_platform_score,
    risk_flag_score      = EXCLUDED.risk_flag_score,
    opportunity_class    = EXCLUDED.opportunity_class,
    top_territory_1      = EXCLUDED.top_territory_1,
    top_territory_2      = EXCLUDED.top_territory_2,
    narrative            = EXCLUDED.narrative,
    llm_status           = EXCLUDED.llm_status;
"""


def upsert_opportunity_results(run_id: str, rows: list[dict]) -> int:
    if not rows:
        return 0
    params = [
        (
            run_id,
            r.get("artist_id"),
            r.get("rank"),
            r.get("momentum_score"),
            r.get("cross_platform_score"),
            r.get("risk_flag_score"),
            _CLASS_MAP.get(str(r.get("opportunity_class", "MEDIUM")).upper(), "MEDIUM"),
            r.get("top_territory_1"),
            r.get("top_territory_2"),
            r.get("narrative"),
            r.get("llm_status", "ok"),
        )
        for r in rows
    ]
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur, _UPSERT_OPP, params,
                template=(
                    "(%s,%s,%s,%s,%s,%s,"
                    "%s::opportunity_class_enum,%s,%s,%s,"
                    "%s::llm_status_enum, now())"
                ),
                page_size=500,
            )
    return len(rows)


# ── Agent 2: Strategy ─────────────────────────────────────────────────────────

_UPSERT_STRAT = """
INSERT INTO agent_strategy_results
    (run_id, artist_id, best_brand_category, brand_fit_score,
     activation_pillars, recommended_channel, strategic_brief,
     sentiment_risk, llm_status, generated_at)
VALUES %s
ON CONFLICT (run_id, artist_id) DO UPDATE SET
    best_brand_category  = EXCLUDED.best_brand_category,
    brand_fit_score      = EXCLUDED.brand_fit_score,
    activation_pillars   = EXCLUDED.activation_pillars,
    recommended_channel  = EXCLUDED.recommended_channel,
    strategic_brief      = EXCLUDED.strategic_brief,
    sentiment_risk       = EXCLUDED.sentiment_risk,
    llm_status           = EXCLUDED.llm_status;
"""


def upsert_strategy_results(run_id: str, rows: list[dict]) -> int:
    if not rows:
        return 0
    params = [
        (
            run_id,
            r.get("artist_id"),
            r.get("best_brand_category"),
            r.get("brand_fit_score"),
            json.dumps([
                r.get("activation_pillar_1", ""),
                r.get("activation_pillar_2", ""),
                r.get("activation_pillar_3", ""),
            ]),
            r.get("recommended_channel"),
            r.get("strategic_brief"),
            _RISK_MAP.get(str(r.get("sentiment_risk", "low")).lower(), "low"),
            r.get("llm_status", "ok"),
        )
        for r in rows
    ]
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur, _UPSERT_STRAT, params,
                template=(
                    "(%s,%s,%s::brand_category_enum,%s,%s,%s,%s,"
                    "%s::sentiment_risk_enum,%s::llm_status_enum,now())"
                ),
                page_size=500,
            )
    return len(rows)


# ── Agent 3: Audience ─────────────────────────────────────────────────────────

_UPSERT_AUD = """
INSERT INTO agent_audience_results
    (run_id, artist_id, best_brand_category, total_reach,
     primary_market, secondary_market, primary_platform,
     audience_fit_score, data_confidence, proxy_pct, firstparty_pct,
     audience_summary, llm_status, generated_at)
VALUES %s
ON CONFLICT (run_id, artist_id) DO UPDATE SET
    best_brand_category  = EXCLUDED.best_brand_category,
    total_reach          = EXCLUDED.total_reach,
    primary_market       = EXCLUDED.primary_market,
    secondary_market     = EXCLUDED.secondary_market,
    primary_platform     = EXCLUDED.primary_platform,
    audience_fit_score   = EXCLUDED.audience_fit_score,
    data_confidence      = EXCLUDED.data_confidence,
    proxy_pct            = EXCLUDED.proxy_pct,
    firstparty_pct       = EXCLUDED.firstparty_pct,
    audience_summary     = EXCLUDED.audience_summary,
    llm_status           = EXCLUDED.llm_status;
"""


def upsert_audience_results(run_id: str, rows: list[dict]) -> int:
    if not rows:
        return 0
    params = [
        (
            run_id,
            r.get("artist_id"),
            r.get("best_brand_category"),
            r.get("total_reach"),
            r.get("primary_market"),
            r.get("secondary_market"),
            r.get("primary_platform"),
            r.get("audience_fit_score"),
            r.get("data_confidence", "MEDIUM"),
            r.get("proxy_pct"),
            r.get("firstparty_pct"),
            r.get("audience_summary"),
            r.get("llm_status", "ok"),
        )
        for r in rows
    ]
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur, _UPSERT_AUD, params,
                template=(
                    "(%s,%s,%s::brand_category_enum,%s,%s,%s,%s,%s,"
                    "%s::data_confidence_enum,%s,%s,%s,%s::llm_status_enum,now())"
                ),
                page_size=500,
            )
    return len(rows)


# ── Agent 4: ROI ──────────────────────────────────────────────────────────────

_UPSERT_ROI = """
INSERT INTO agent_roi_results
    (run_id, artist_id, brand_category, reference_budget,
     conservative_roi, base_roi, optimistic_roi,
     base_revenue, base_conversions, base_reach, base_brand_lift,
     recommended_scenario, assumptions, investment_narrative,
     risk_flag, llm_status, generated_at)
VALUES %s
ON CONFLICT (run_id, artist_id) DO UPDATE SET
    brand_category       = EXCLUDED.brand_category,
    reference_budget     = EXCLUDED.reference_budget,
    conservative_roi     = EXCLUDED.conservative_roi,
    base_roi             = EXCLUDED.base_roi,
    optimistic_roi       = EXCLUDED.optimistic_roi,
    base_revenue         = EXCLUDED.base_revenue,
    base_conversions     = EXCLUDED.base_conversions,
    base_reach           = EXCLUDED.base_reach,
    base_brand_lift      = EXCLUDED.base_brand_lift,
    recommended_scenario = EXCLUDED.recommended_scenario,
    assumptions          = EXCLUDED.assumptions,
    investment_narrative = EXCLUDED.investment_narrative,
    risk_flag            = EXCLUDED.risk_flag,
    llm_status           = EXCLUDED.llm_status;
"""

_UPSERT_SCENARIOS = """
INSERT INTO roi_scenarios
    (run_id, artist_id, scenario,
     projected_roi, projected_revenue, projected_conversions,
     projected_reach, projected_brand_lift)
VALUES %s
ON CONFLICT (run_id, artist_id, scenario) DO UPDATE SET
    projected_roi         = EXCLUDED.projected_roi,
    projected_revenue     = EXCLUDED.projected_revenue,
    projected_conversions = EXCLUDED.projected_conversions,
    projected_reach       = EXCLUDED.projected_reach,
    projected_brand_lift  = EXCLUDED.projected_brand_lift;
"""


def upsert_roi_results(run_id: str, rows: list[dict], detail_rows: list[dict]) -> int:
    """
    Batch-upsert agent_roi_results AND roi_scenarios in the same transaction.
    2 SQL calls total regardless of row count.
    """
    if not rows:
        return 0

    roi_params = [
        (
            run_id,
            r.get("artist_id"),
            r.get("brand_category"),
            r.get("reference_budget"),
            r.get("conservative_roi"),
            r.get("base_roi"),
            r.get("optimistic_roi"),
            r.get("base_revenue"),
            r.get("base_conversions"),
            r.get("base_reach"),
            r.get("base_brand_lift"),
            _SCENARIO_MAP.get(str(r.get("recommended_scenario", "base")).lower(), "base"),
            json.dumps([
                r.get("assumption_1", ""),
                r.get("assumption_2", ""),
                r.get("assumption_3", ""),
            ]),
            r.get("investment_narrative"),
            r.get("risk_flag", "none"),
            r.get("llm_status", "ok"),
        )
        for r in rows
    ]

    scenario_params = [
        (
            run_id,
            d.get("artist_id"),
            _SCENARIO_MAP.get(str(d.get("scenario", "base")).lower(), "base"),
            d.get("projected_roi"),
            d.get("projected_revenue"),
            d.get("projected_conversions"),
            d.get("projected_reach"),
            d.get("projected_brand_lift"),
        )
        for d in detail_rows
    ]

    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur, _UPSERT_ROI, roi_params,
                template=(
                    "(%s,%s,%s::brand_category_enum,%s,%s,%s,%s,%s,%s,%s,%s,"
                    "%s::scenario_enum,%s,%s,%s,%s::llm_status_enum,now())"
                ),
                page_size=500,
            )
            if scenario_params:
                execute_values(
                    cur, _UPSERT_SCENARIOS, scenario_params,
                    template="(%s,%s,%s::scenario_enum,%s,%s,%s,%s,%s)",
                    page_size=500,
                )
    return len(rows)
