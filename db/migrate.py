"""
CDX — Schema Migration Runner

Applies the full PostgreSQL schema (DDL) against DATABASE_URL.
Idempotent: uses IF NOT EXISTS / CREATE OR REPLACE wherever possible.

Run once to set up a fresh database, or after pulling schema changes:
    python -m db.migrate
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from db.connection import get_conn

# ---------------------------------------------------------------------------
# Full schema DDL — mirrors the design in the migration spec exactly.
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
-- ============================================================================
-- 0. Extensions & enums
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE opportunity_class_enum AS ENUM ('HIGH', 'MEDIUM', 'LOW');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sentiment_risk_enum AS ENUM ('low', 'medium', 'high');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE scenario_enum AS ENUM ('conservative', 'base', 'optimistic');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE data_confidence_enum AS ENUM ('HIGH', 'MEDIUM', 'LOW');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE source_type_enum AS ENUM ('first-party', 'proxy');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE llm_status_enum AS ENUM ('ok', 'failed', 'parse_error');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE pipeline_status_enum AS ENUM ('running', 'complete', 'error');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE brand_category_enum AS ENUM ('Beverages', 'Fashion', 'Tech', 'Sport', 'Finance');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================================
-- 1. Dimension table — artists
-- ============================================================================
CREATE TABLE IF NOT EXISTS artists (
    artist_id                  TEXT PRIMARY KEY,
    name                       TEXT NOT NULL,
    country                    TEXT,
    genre                      TEXT,
    label                      TEXT,
    spotify_monthly_listeners  BIGINT,
    social_blade_followers     BIGINT,
    youtube_subscribers        BIGINT,
    updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 2. Raw / source signal tables
-- ============================================================================

-- spotify_charts
CREATE TABLE IF NOT EXISTS spotify_chart_entries (
    id               BIGSERIAL PRIMARY KEY,
    chart_date       DATE NOT NULL,
    territory        TEXT NOT NULL,
    artist_id        TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    track_title      TEXT NOT NULL,
    chart_position   SMALLINT,
    streams_estimate BIGINT,
    peak_position    SMALLINT,
    weeks_on_chart   SMALLINT,
    UNIQUE (chart_date, territory, artist_id, track_title)
);
CREATE INDEX IF NOT EXISTS idx_spotify_chart_artist_date ON spotify_chart_entries (artist_id, chart_date);

-- kworb_crosschart
CREATE TABLE IF NOT EXISTS kworb_crosschart (
    id                     BIGSERIAL PRIMARY KEY,
    chart_date             DATE NOT NULL,
    artist_id              TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    platforms_charting     TEXT,
    peak_position_global   SMALLINT,
    weeks_on_chart         SMALLINT,
    territories_charting   TEXT,
    UNIQUE (chart_date, artist_id)
);

-- social_blade_growth
CREATE TABLE IF NOT EXISTS social_growth (
    id              BIGSERIAL PRIMARY KEY,
    growth_date     DATE NOT NULL,
    artist_id       TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    platform        TEXT NOT NULL,
    followers_start BIGINT,
    followers_end   BIGINT,
    growth_pct      NUMERIC(6,3),
    engagement_rate NUMERIC(5,3),
    UNIQUE (growth_date, artist_id, platform)
);
CREATE INDEX IF NOT EXISTS idx_social_growth_artist_date ON social_growth (artist_id, growth_date);

-- media_mentions
CREATE TABLE IF NOT EXISTS media_mentions (
    id               BIGSERIAL PRIMARY KEY,
    mention_date     DATE NOT NULL,
    artist_id        TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    source           TEXT,
    headline         TEXT NOT NULL,
    sentiment_score  NUMERIC(4,3),
    cultural_topics  JSONB DEFAULT '[]'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_media_mentions_artist_date ON media_mentions (artist_id, mention_date);
CREATE INDEX IF NOT EXISTS idx_media_mentions_topics_gin ON media_mentions USING GIN (cultural_topics);

-- audience_segments
CREATE TABLE IF NOT EXISTS audience_segments (
    id                BIGSERIAL PRIMARY KEY,
    artist_id         TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    market            TEXT NOT NULL,
    segment_name      TEXT NOT NULL,
    age_range         TEXT,
    gender_split_f    NUMERIC(5,2),
    gender_split_m    NUMERIC(5,2),
    platform_primary  TEXT,
    estimated_reach   BIGINT,
    source_type       source_type_enum NOT NULL,
    UNIQUE (artist_id, market, segment_name)
);
CREATE INDEX IF NOT EXISTS idx_audience_segments_artist ON audience_segments (artist_id);

-- client_campaigns
CREATE TABLE IF NOT EXISTS client_campaigns (
    campaign_id            TEXT PRIMARY KEY,
    brand_name             TEXT NOT NULL,
    brand_category         brand_category_enum NOT NULL,
    artist_id              TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    territory              TEXT,
    budget_usd             NUMERIC(12,2),
    actual_revenue_uplift  NUMERIC(14,2),
    conversions            INTEGER,
    reach_actual           BIGINT,
    brand_lift_pts         NUMERIC(5,2),
    campaign_start         DATE,
    campaign_end           DATE
);
CREATE INDEX IF NOT EXISTS idx_campaigns_artist ON client_campaigns (artist_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_category ON client_campaigns (brand_category);

-- ============================================================================
-- 3. Computed scores layer
-- ============================================================================
CREATE TABLE IF NOT EXISTS scores_weekly (
    id                          BIGSERIAL PRIMARY KEY,
    artist_id                   TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    territory                   TEXT NOT NULL,
    week_date                   DATE NOT NULL,
    momentum_score              NUMERIC(6,2),
    territory_fit_score         NUMERIC(6,2),
    cross_platform_score        NUMERIC(6,2),
    narrative_resonance_score   NUMERIC(6,2),
    risk_flag_score             NUMERIC(6,2),
    UNIQUE (artist_id, territory, week_date)
);
CREATE INDEX IF NOT EXISTS idx_scores_weekly_artist_week ON scores_weekly (artist_id, week_date);

CREATE TABLE IF NOT EXISTS score_audience_fit (
    scores_weekly_id  BIGINT NOT NULL REFERENCES scores_weekly(id) ON DELETE CASCADE,
    brand_category    brand_category_enum NOT NULL,
    fit_score         NUMERIC(6,2),
    PRIMARY KEY (scores_weekly_id, brand_category)
);

-- ============================================================================
-- 4. Pipeline run tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    status       pipeline_status_enum NOT NULL DEFAULT 'running',
    exit_code    INTEGER,
    triggered_by TEXT
);

-- ============================================================================
-- 5. Agent output tables
-- ============================================================================

-- agent1: Opportunity Discovery
CREATE TABLE IF NOT EXISTS agent_opportunity_results (
    id                    BIGSERIAL PRIMARY KEY,
    run_id                UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    artist_id             TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    rank                  SMALLINT,
    momentum_score        NUMERIC(6,2),
    cross_platform_score  NUMERIC(6,2),
    risk_flag_score       NUMERIC(6,2),
    opportunity_class     opportunity_class_enum,
    top_territory_1       TEXT,
    top_territory_2       TEXT,
    narrative             TEXT,
    llm_status            llm_status_enum,
    generated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (run_id, artist_id)
);

-- agent2: Strategy Synthesis
CREATE TABLE IF NOT EXISTS agent_strategy_results (
    id                   BIGSERIAL PRIMARY KEY,
    run_id               UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    artist_id            TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    best_brand_category  brand_category_enum,
    brand_fit_score      NUMERIC(6,2),
    activation_pillars   JSONB DEFAULT '[]'::jsonb,
    recommended_channel  TEXT,
    strategic_brief      TEXT,
    sentiment_risk       sentiment_risk_enum,
    llm_status           llm_status_enum,
    generated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (run_id, artist_id)
);

-- agent3: Audience Fit
CREATE TABLE IF NOT EXISTS agent_audience_results (
    id                   BIGSERIAL PRIMARY KEY,
    run_id               UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    artist_id            TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    best_brand_category  brand_category_enum,
    total_reach          BIGINT,
    primary_market       TEXT,
    secondary_market     TEXT,
    primary_platform     TEXT,
    audience_fit_score   NUMERIC(6,2),
    data_confidence      data_confidence_enum,
    proxy_pct            NUMERIC(5,2),
    firstparty_pct       NUMERIC(5,2),
    audience_summary     TEXT,
    llm_status           llm_status_enum,
    generated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (run_id, artist_id)
);

-- agent4: ROI Forecast
CREATE TABLE IF NOT EXISTS agent_roi_results (
    id                   BIGSERIAL PRIMARY KEY,
    run_id               UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    artist_id            TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    brand_category       brand_category_enum,
    reference_budget     NUMERIC(12,2),
    conservative_roi     NUMERIC(6,3),
    base_roi             NUMERIC(6,3),
    optimistic_roi       NUMERIC(6,3),
    base_revenue         NUMERIC(14,2),
    base_conversions     NUMERIC(10,1),
    base_reach           BIGINT,
    base_brand_lift      NUMERIC(5,2),
    recommended_scenario scenario_enum,
    assumptions          JSONB DEFAULT '[]'::jsonb,
    investment_narrative TEXT,
    risk_flag            TEXT,
    llm_status           llm_status_enum,
    generated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (run_id, artist_id)
);

-- roi_scenarios_detail: long-format per scenario
CREATE TABLE IF NOT EXISTS roi_scenarios (
    id                       BIGSERIAL PRIMARY KEY,
    run_id                   UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    artist_id                TEXT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    scenario                 scenario_enum NOT NULL,
    projected_roi            NUMERIC(6,3),
    projected_revenue        NUMERIC(14,2),
    projected_conversions    NUMERIC(10,1),
    projected_reach          BIGINT,
    projected_brand_lift     NUMERIC(5,2),
    UNIQUE (run_id, artist_id, scenario)
);

-- ============================================================================
-- 6. Convenience views — "latest completed run" behaviour
-- ============================================================================
CREATE OR REPLACE VIEW latest_completed_run AS
    SELECT run_id, completed_at
    FROM pipeline_runs
    WHERE status = 'complete'
    ORDER BY completed_at DESC
    LIMIT 1;

CREATE OR REPLACE VIEW latest_opportunity_results AS
    SELECT r.* FROM agent_opportunity_results r
    JOIN latest_completed_run lr ON r.run_id = lr.run_id;

CREATE OR REPLACE VIEW latest_strategy_results AS
    SELECT r.* FROM agent_strategy_results r
    JOIN latest_completed_run lr ON r.run_id = lr.run_id;

CREATE OR REPLACE VIEW latest_audience_results AS
    SELECT r.* FROM agent_audience_results r
    JOIN latest_completed_run lr ON r.run_id = lr.run_id;

CREATE OR REPLACE VIEW latest_roi_results AS
    SELECT r.* FROM agent_roi_results r
    JOIN latest_completed_run lr ON r.run_id = lr.run_id;

-- ============================================================================
-- 7. Full artist profile view
-- ============================================================================
CREATE OR REPLACE VIEW artist_full_profile AS
    SELECT
        a.artist_id, a.name, a.genre, a.country,
        opp.opportunity_class, opp.momentum_score, opp.narrative AS opportunity_narrative,
        strat.best_brand_category, strat.recommended_channel, strat.strategic_brief,
        aud.total_reach, aud.data_confidence, aud.audience_summary,
        roi.recommended_scenario, roi.base_roi, roi.investment_narrative
    FROM artists a
    LEFT JOIN latest_opportunity_results opp   ON a.artist_id = opp.artist_id
    LEFT JOIN latest_strategy_results    strat ON a.artist_id = strat.artist_id
    LEFT JOIN latest_audience_results    aud   ON a.artist_id = aud.artist_id
    LEFT JOIN latest_roi_results         roi   ON a.artist_id = roi.artist_id;
"""


def run_migration(verbose: bool = True) -> None:
    """Apply the schema to the configured database."""
    if verbose:
        print("━" * 60)
        print("  CDX — Database Migration")
        print("━" * 60)
        print(f"  Target: {os.environ.get('DATABASE_URL', '(not set)')}")
        print()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)

    if verbose:
        print("  ✓  Schema applied successfully.")
        print()
        print("  Tables created (if not already present):")
        tables = [
            "artists", "spotify_chart_entries", "kworb_crosschart",
            "social_growth", "media_mentions", "audience_segments",
            "client_campaigns", "scores_weekly", "score_audience_fit",
            "pipeline_runs", "agent_opportunity_results",
            "agent_strategy_results", "agent_audience_results",
            "agent_roi_results", "roi_scenarios",
        ]
        for t in tables:
            print(f"    • {t}")
        print()
        print("  Views created/updated:")
        views = [
            "latest_completed_run", "latest_opportunity_results",
            "latest_strategy_results", "latest_audience_results",
            "latest_roi_results", "artist_full_profile",
        ]
        for v in views:
            print(f"    • {v}")
        print("━" * 60)


if __name__ == "__main__":
    run_migration()
