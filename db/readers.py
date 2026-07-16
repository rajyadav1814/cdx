"""
CDX — Database Reader Helpers

Read-only queries that replace the old `read_csv_as_json()` calls in main.py.
All functions return list[dict] matching the JSON shape the frontend expects.

Import pattern:
    from db.readers import read_agent1, read_agent2, ...
"""

import json
from typing import Any

from db.connection import get_conn


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rows_to_dicts(cur) -> list[dict]:
    """Convert cursor results to a list of column-keyed dicts."""
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _serialize(val: Any) -> Any:
    """Make a value JSON-safe (handles Decimal, UUID, date, etc.)."""
    import decimal, datetime, uuid
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    if isinstance(val, uuid.UUID):
        return str(val)
    return val


def _serialize_rows(rows: list[dict]) -> list[dict]:
    return [{k: _serialize(v) for k, v in r.items()} for r in rows]


# ---------------------------------------------------------------------------
# Latest run helper
# ---------------------------------------------------------------------------

def get_latest_run_id() -> str | None:
    """Return the UUID of the most recently completed run, or None."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT run_id::text FROM pipeline_runs "
                "WHERE status = 'complete' "
                "ORDER BY completed_at DESC LIMIT 1;"
            )
            row = cur.fetchone()
            return row[0] if row else None


# ---------------------------------------------------------------------------
# Agent 1 — Opportunity results
# ---------------------------------------------------------------------------

def read_agent1(run_id: str | None = None) -> list[dict]:
    """
    Returns the same shape as the old agent1_output.csv:
    artist_id, artist_name, rank, momentum_score, cross_platform_score,
    risk_flag_score, opportunity_class, top_territory_1, top_territory_2,
    narrative, llm_status, generated_at
    """
    rid = run_id or get_latest_run_id()
    if not rid:
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.artist_id,
                    a.name          AS artist_name,
                    r.rank,
                    r.momentum_score,
                    r.cross_platform_score,
                    r.risk_flag_score,
                    r.opportunity_class,
                    r.top_territory_1,
                    r.top_territory_2,
                    r.narrative,
                    r.llm_status,
                    r.generated_at
                FROM agent_opportunity_results r
                JOIN artists a USING (artist_id)
                WHERE r.run_id = %s
                ORDER BY r.rank;
                """,
                [rid],
            )
            return _serialize_rows(_rows_to_dicts(cur))


# ---------------------------------------------------------------------------
# Agent 2 — Strategy results
# ---------------------------------------------------------------------------

def read_agent2(run_id: str | None = None) -> list[dict]:
    """
    Returns shape matching agent2_output.csv:
    artist_id, artist_name, best_brand_category, brand_fit_score,
    activation_pillar_1/2/3, recommended_channel, strategic_brief,
    sentiment_risk, llm_status, generated_at
    """
    rid = run_id or get_latest_run_id()
    if not rid:
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.artist_id,
                    a.name              AS artist_name,
                    r.best_brand_category,
                    r.brand_fit_score,
                    r.activation_pillars,
                    r.recommended_channel,
                    r.strategic_brief,
                    r.sentiment_risk,
                    r.llm_status,
                    r.generated_at
                FROM agent_strategy_results r
                JOIN artists a USING (artist_id)
                WHERE r.run_id = %s
                ORDER BY a.name;
                """,
                [rid],
            )
            rows = _rows_to_dicts(cur)

    # Expand JSONB activation_pillars → pillar_1/2/3 for CSV compatibility
    result = []
    for r in rows:
        pillars = r.pop("activation_pillars", []) or []
        if isinstance(pillars, str):
            pillars = json.loads(pillars)
        r["activation_pillar_1"] = pillars[0] if len(pillars) > 0 else ""
        r["activation_pillar_2"] = pillars[1] if len(pillars) > 1 else ""
        r["activation_pillar_3"] = pillars[2] if len(pillars) > 2 else ""
        result.append(r)
    return _serialize_rows(result)


# ---------------------------------------------------------------------------
# Agent 3 — Audience results
# ---------------------------------------------------------------------------

def read_agent3(run_id: str | None = None) -> list[dict]:
    """
    Returns shape matching agent3_output.csv:
    artist_id, artist_name, best_brand_category, total_reach,
    primary_market, secondary_market, primary_platform, audience_fit_score,
    data_confidence, proxy_pct, firstparty_pct, audience_summary,
    llm_status, generated_at
    """
    rid = run_id or get_latest_run_id()
    if not rid:
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.artist_id,
                    a.name              AS artist_name,
                    r.best_brand_category,
                    r.total_reach,
                    r.primary_market,
                    r.secondary_market,
                    r.primary_platform,
                    r.audience_fit_score,
                    r.data_confidence,
                    r.proxy_pct,
                    r.firstparty_pct,
                    r.audience_summary,
                    r.llm_status,
                    r.generated_at
                FROM agent_audience_results r
                JOIN artists a USING (artist_id)
                WHERE r.run_id = %s
                ORDER BY a.name;
                """,
                [rid],
            )
            return _serialize_rows(_rows_to_dicts(cur))


# ---------------------------------------------------------------------------
# Agent 4 — ROI results
# ---------------------------------------------------------------------------

def read_agent4(run_id: str | None = None) -> list[dict]:
    """
    Returns shape matching agent4_output.csv:
    artist_id, artist_name, brand_category, reference_budget,
    conservative_roi, base_roi, optimistic_roi, base_revenue,
    base_conversions, base_reach, base_brand_lift, recommended_scenario,
    assumption_1/2/3, investment_narrative, risk_flag, llm_status, generated_at
    """
    rid = run_id or get_latest_run_id()
    if not rid:
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.artist_id,
                    a.name              AS artist_name,
                    r.brand_category,
                    r.reference_budget,
                    r.conservative_roi,
                    r.base_roi,
                    r.optimistic_roi,
                    r.base_revenue,
                    r.base_conversions,
                    r.base_reach,
                    r.base_brand_lift,
                    r.recommended_scenario,
                    r.assumptions,
                    r.investment_narrative,
                    r.risk_flag,
                    r.llm_status,
                    r.generated_at
                FROM agent_roi_results r
                JOIN artists a USING (artist_id)
                WHERE r.run_id = %s
                ORDER BY r.base_roi DESC;
                """,
                [rid],
            )
            rows = _rows_to_dicts(cur)

    # Expand JSONB assumptions → assumption_1/2/3 for CSV compatibility
    result = []
    for r in rows:
        assumptions = r.pop("assumptions", []) or []
        if isinstance(assumptions, str):
            assumptions = json.loads(assumptions)
        r["assumption_1"] = assumptions[0] if len(assumptions) > 0 else ""
        r["assumption_2"] = assumptions[1] if len(assumptions) > 1 else ""
        r["assumption_3"] = assumptions[2] if len(assumptions) > 2 else ""
        result.append(r)
    return _serialize_rows(result)


# ---------------------------------------------------------------------------
# ROI scenarios detail
# ---------------------------------------------------------------------------

def read_roi_scenarios(run_id: str | None = None) -> list[dict]:
    """Returns shape matching roi_scenarios_detail.csv."""
    rid = run_id or get_latest_run_id()
    if not rid:
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.artist_id,
                    a.name              AS artist_name,
                    s.scenario,
                    s.projected_roi,
                    s.projected_revenue,
                    s.projected_conversions,
                    s.projected_reach,
                    s.projected_brand_lift
                FROM roi_scenarios s
                JOIN artists a USING (artist_id)
                WHERE s.run_id = %s
                ORDER BY a.name, s.scenario;
                """,
                [rid],
            )
            return _serialize_rows(_rows_to_dicts(cur))


# ---------------------------------------------------------------------------
# Pipeline summary (replaces pipeline_summary.json)
# ---------------------------------------------------------------------------

def read_pipeline_summary() -> dict:
    """
    Build the summary dict that was previously stored as pipeline_summary.json.
    Queries the latest completed run live from the DB.
    """
    default = {
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

    rid = get_latest_run_id()
    if not rid:
        return default

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Run metadata
            cur.execute(
                "SELECT completed_at FROM pipeline_runs WHERE run_id = %s;",
                [rid],
            )
            run_row = cur.fetchone()
            run_ts = run_row[0].isoformat() if run_row and run_row[0] else None

            # Agent 1 summary
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE opportunity_class = 'HIGH')   AS high_count,
                    COUNT(*) FILTER (WHERE opportunity_class = 'MEDIUM') AS medium_count,
                    COUNT(*) FILTER (WHERE opportunity_class = 'LOW')    AS low_count,
                    COUNT(*)                                              AS total
                FROM agent_opportunity_results
                WHERE run_id = %s;
                """,
                [rid],
            )
            a1 = cur.fetchone()

            cur.execute(
                """
                SELECT a.name
                FROM agent_opportunity_results r
                JOIN artists a USING (artist_id)
                WHERE r.run_id = %s
                ORDER BY r.momentum_score DESC LIMIT 1;
                """,
                [rid],
            )
            top_artist_row = cur.fetchone()
            top_artist = top_artist_row[0] if top_artist_row else ""

            # Agent 2 summary
            cur.execute(
                """
                SELECT
                    COUNT(*)              AS briefs,
                    best_brand_category,
                    COUNT(*) AS cat_count
                FROM agent_strategy_results
                WHERE run_id = %s
                GROUP BY best_brand_category
                ORDER BY cat_count DESC;
                """,
                [rid],
            )
            a2_rows = cur.fetchall()
            briefs = sum(r[2] for r in a2_rows)
            cat_dist = {r[1]: r[2] for r in a2_rows}

            cur.execute(
                """
                SELECT recommended_channel, COUNT(*) AS n
                FROM agent_strategy_results
                WHERE run_id = %s
                GROUP BY recommended_channel ORDER BY n DESC LIMIT 1;
                """,
                [rid],
            )
            ch_row = cur.fetchone()
            most_common_channel = ch_row[0] if ch_row else ""

            # Agent 3 summary
            cur.execute(
                """
                SELECT
                    AVG(total_reach)::BIGINT                                              AS avg_reach,
                    COUNT(*) FILTER (WHERE data_confidence = 'HIGH')  * 100.0 / COUNT(*) AS high_pct,
                    COUNT(*) FILTER (WHERE data_confidence = 'MEDIUM')* 100.0 / COUNT(*) AS med_pct,
                    COUNT(*) FILTER (WHERE data_confidence = 'LOW')   * 100.0 / COUNT(*) AS low_pct
                FROM agent_audience_results
                WHERE run_id = %s;
                """,
                [rid],
            )
            a3 = cur.fetchone()

            # Agent 4 summary
            cur.execute(
                """
                SELECT
                    AVG(base_roi)                AS avg_roi,
                    SUM(base_revenue)            AS total_rev,
                    MAX(base_roi)                AS max_roi
                FROM agent_roi_results
                WHERE run_id = %s;
                """,
                [rid],
            )
            a4 = cur.fetchone()

            cur.execute(
                """
                SELECT a.name
                FROM agent_roi_results r
                JOIN artists a USING (artist_id)
                WHERE r.run_id = %s
                ORDER BY r.base_roi DESC LIMIT 1;
                """,
                [rid],
            )
            best_roi_row = cur.fetchone()
            best_roi_artist = best_roi_row[0] if best_roi_row else ""

    return {
        "run_timestamp":      run_ts,
        "artists_processed":  int(a1[3]) if a1 else 0,
        "agent1": {
            "status":               "ok",
            "high_opportunities":   int(a1[0]) if a1 else 0,
            "medium_opportunities": int(a1[1]) if a1 else 0,
            "watch_opportunities":  int(a1[2]) if a1 else 0,
            "top_artist":           top_artist,
        },
        "agent2": {
            "status":                          "ok",
            "briefs_generated":                briefs,
            "best_brand_category_distribution":{k: int(v) for k, v in cat_dist.items()},
            "most_common_channel":             most_common_channel,
        },
        "agent3": {
            "status":               "ok",
            "avg_reach":            int(a3[0]) if a3 and a3[0] else 0,
            "high_confidence_pct":  round(float(a3[1]), 1) if a3 and a3[1] else 0,
            "medium_confidence_pct":round(float(a3[2]), 1) if a3 and a3[2] else 0,
            "low_confidence_pct":   round(float(a3[3]), 1) if a3 and a3[3] else 0,
        },
        "agent4": {
            "status":                  "ok",
            "avg_base_roi":            round(float(a4[0]), 4) if a4 and a4[0] else 0,
            "total_projected_revenue": int(a4[1]) if a4 and a4[1] else 0,
            "highest_roi_multiple":    round(float(a4[2]), 4) if a4 and a4[2] else 0,
            "highest_roi_artist":      best_roi_artist,
        },
    }


# ---------------------------------------------------------------------------
# Agent chat context (replaces load_agent_context in main.py)
# ---------------------------------------------------------------------------

def load_agent_context_db(agent_key: str, artist_filter: str | None = None) -> dict:
    """
    Load context data for the chat agents directly from the DB.
    Replaces the CSV-based load_agent_context() in main.py.
    """
    rid = get_latest_run_id()

    def _filter_name(rows: list[dict]) -> list[dict]:
        if not artist_filter:
            return rows
        return [r for r in rows if
                str(r.get("artist_name", "")).lower() == artist_filter.lower()]

    if agent_key == "agent2":
        agent_rows  = _filter_name(read_agent2(rid))
        scores_rows = _read_scores_latest(artist_filter)
        extra_rows  = _read_media_mentions(artist_filter)
    elif agent_key == "agent3":
        agent_rows  = _filter_name(read_agent3(rid))
        scores_rows = _read_scores_latest(artist_filter)
        extra_rows  = _read_audience_segments(artist_filter)
    elif agent_key == "agent4":
        agent_rows  = _filter_name(read_agent4(rid))
        extra_rows  = read_roi_scenarios(rid)
        if artist_filter:
            extra_rows = [r for r in extra_rows
                         if str(r.get("artist_name", "")).lower() == artist_filter.lower()]
        scores_rows = _read_client_campaigns(artist_filter)
    else:
        agent_rows = scores_rows = extra_rows = []

    return {
        "agent_outputs":  agent_rows,
        "scores":         scores_rows,
        "supplemental":   extra_rows,
        "artist_filter":  artist_filter or "all artists",
        "generated_for":  "Sony Music Latin — CSIE",
    }


def _read_scores_latest(artist_filter: str | None = None) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if artist_filter:
                cur.execute(
                    """
                    SELECT s.*, a.name AS artist_name
                    FROM scores_weekly s
                    JOIN artists a USING (artist_id)
                    WHERE a.name ILIKE %s
                      AND s.week_date = (SELECT MAX(week_date) FROM scores_weekly)
                    ORDER BY s.territory;
                    """,
                    [artist_filter],
                )
            else:
                cur.execute(
                    """
                    SELECT s.*, a.name AS artist_name
                    FROM scores_weekly s
                    JOIN artists a USING (artist_id)
                    WHERE s.week_date = (SELECT MAX(week_date) FROM scores_weekly)
                    ORDER BY a.name, s.territory;
                    """
                )
            return _serialize_rows(_rows_to_dicts(cur))


def _read_media_mentions(artist_filter: str | None = None) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if artist_filter:
                cur.execute(
                    """
                    SELECT m.*, a.name AS artist_name
                    FROM media_mentions m
                    JOIN artists a USING (artist_id)
                    WHERE a.name ILIKE %s
                    ORDER BY m.mention_date DESC;
                    """,
                    [artist_filter],
                )
            else:
                cur.execute(
                    """
                    SELECT m.*, a.name AS artist_name
                    FROM media_mentions m
                    JOIN artists a USING (artist_id)
                    ORDER BY m.mention_date DESC;
                    """
                )
            return _serialize_rows(_rows_to_dicts(cur))


def _read_audience_segments(artist_filter: str | None = None) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if artist_filter:
                cur.execute(
                    """
                    SELECT seg.*, a.name AS artist_name
                    FROM audience_segments seg
                    JOIN artists a USING (artist_id)
                    WHERE a.name ILIKE %s
                    ORDER BY seg.estimated_reach DESC;
                    """,
                    [artist_filter],
                )
            else:
                cur.execute(
                    """
                    SELECT seg.*, a.name AS artist_name
                    FROM audience_segments seg
                    JOIN artists a USING (artist_id)
                    ORDER BY a.name, seg.estimated_reach DESC;
                    """
                )
            return _serialize_rows(_rows_to_dicts(cur))


def _read_client_campaigns(artist_filter: str | None = None) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if artist_filter:
                cur.execute(
                    """
                    SELECT c.*, a.name AS artist_name
                    FROM client_campaigns c
                    JOIN artists a USING (artist_id)
                    WHERE a.name ILIKE %s;
                    """,
                    [artist_filter],
                )
            else:
                cur.execute(
                    """
                    SELECT c.*, a.name AS artist_name
                    FROM client_campaigns c
                    JOIN artists a USING (artist_id);
                    """
                )
            return _serialize_rows(_rows_to_dicts(cur))
