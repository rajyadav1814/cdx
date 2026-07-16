"""
CDX — Commercial Signal Intelligence Engine
Scoring Engine — Prompt 2

Reads 5 source CSVs from data/ and writes data/scores_weekly.csv.
Pure Python/pandas deterministic math. No LLM calls.
All output scores are normalized 0–100.
"""

import os
import sys
import pandas as pd
import numpy as np

# ─── Paths ─────────────────────────────────────────────────────────────────── #
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT   = os.path.join(DATA_DIR, 'scores_weekly.csv')

# ─── DB writers & connection ──────────────────────────────────────────────────
from db.writers import upsert_scores_weekly
from db.connection import get_conn
_DB_ENABLED = True

# ─── Load source CSVs ────────────────────────────────────────────────────────
print("Loading data from DB...")
with get_conn() as conn:
    df_artists  = pd.read_sql("SELECT * FROM artists", conn)
    df_charts   = pd.read_sql(
        "SELECT id, chart_date AS date, territory, artist_id, track_title,"
        " chart_position, streams_estimate, peak_position, weeks_on_chart"
        " FROM spotify_chart_entries", conn)
    df_kworb    = pd.read_sql(
        "SELECT id, chart_date AS date, artist_id, platforms_charting,"
        " peak_position_global, weeks_on_chart, territories_charting"
        " FROM kworb_crosschart", conn)
    df_social   = pd.read_sql(
        "SELECT id, growth_date AS date, artist_id, platform,"
        " followers_start, followers_end, growth_pct, engagement_rate"
        " FROM social_growth", conn)
    df_media    = pd.read_sql(
        "SELECT id, mention_date AS date, artist_id, source,"
        " headline, sentiment_score, cultural_topics"
        " FROM media_mentions", conn)
    df_audience = pd.read_sql("SELECT * FROM audience_segments", conn)

df_charts['date'] = pd.to_datetime(df_charts['date'])
df_media['date']  = pd.to_datetime(df_media['date'])

TERRITORIES = ["MX", "CO", "AR", "BR", "ES", "CL", "PE", "US-Latin"]
WEEK_DATE   = str(df_charts['date'].max().date())
MEDIA_TODAY = df_media['date'].max()

# Only score ART_xxx IDs — skip LIVE_xxx bonus rows from scrape
ARTIST_IDS   = df_artists['artist_id'].tolist()
ARTIST_NAMES = dict(zip(df_artists['artist_id'], df_artists['name']))

# Filter chart data to known artists
df_charts_known = df_charts[df_charts['artist_id'].isin(ARTIST_IDS)]


def clip100(v: float) -> float:
    """Clip a value to [0, 100] and round to 2dp."""
    return round(float(np.clip(v, 0.0, 100.0)), 2)


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE 3 — CROSS_PLATFORM_CONSISTENCY_SCORE
#   3+ platforms → base 90, scaled by weeks_on_chart up to 100
#   2  platforms → base 60, scaled up to 75
#   1  platform  → base 20, scaled up to 40
# ═══════════════════════════════════════════════════════════════════════════════
print("Computing cross-platform scores...")

cross_platform_scores: dict[str, float] = {}

for _, row in df_kworb[df_kworb['artist_id'].isin(ARTIST_IDS)].iterrows():
    aid = row['artist_id']
    platforms = [p.strip() for p in str(row['platforms_charting']).split(',') if p.strip()]
    n = len(platforms)
    weeks = float(row['weeks_on_chart']) if pd.notna(row['weeks_on_chart']) else 0.0

    if n >= 3:
        base, width = 90.0, 10.0
    elif n == 2:
        base, width = 60.0, 15.0
    else:
        base, width = 20.0, 20.0

    # weeks_on_chart bonus: fraction of 1 year fills the width
    weeks_factor = min(1.0, weeks / 52.0)
    cross_platform_scores[aid] = clip100(base + weeks_factor * width)

# Default 0 for any artist missing from kworb data
for aid in ARTIST_IDS:
    cross_platform_scores.setdefault(aid, 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE 4 — NARRATIVE_RESONANCE_SCORE
#   positive_component  = count(sentiment > 0.6) / max_across_artists  × 40
#   variety_component   = unique_topics / max_unique_topics             × 30
#   recency_component   = weighted_count / max_weighted                 × 30
#   (mentions in last 14 days count 2×)
# ═══════════════════════════════════════════════════════════════════════════════
print("Computing narrative resonance scores...")

CUTOFF_14 = MEDIA_TODAY - pd.Timedelta(days=14)

# Raw accumulators
nar_raw: dict[str, tuple] = {}   # aid → (positive_count, n_topics, weighted_count)

for aid in ARTIST_IDS:
    mentions = df_media[df_media['artist_id'] == aid]
    if len(mentions) == 0:
        nar_raw[aid] = (0, 0, 0.0)
        continue

    positive_count = int((mentions['sentiment_score'] > 0.6).sum())

    unique_topics: set[str] = set()
    for topics_str in mentions['cultural_topics'].dropna():
        for t in str(topics_str).split(','):
            t = t.strip()
            if t:
                unique_topics.add(t)
    n_topics = len(unique_topics)

    weighted_count = 0.0
    for _, m in mentions.iterrows():
        w = 2.0 if m['date'] >= CUTOFF_14 else 1.0
        weighted_count += w

    nar_raw[aid] = (positive_count, n_topics, weighted_count)

# Normalize each component globally
max_positive = max(v[0] for v in nar_raw.values()) or 1
max_topics   = max(v[1] for v in nar_raw.values()) or 1
max_weighted = max(v[2] for v in nar_raw.values()) or 1

narrative_scores: dict[str, float] = {}
for aid, (pos, topics, weighted) in nar_raw.items():
    pos_comp      = (pos     / max_positive) * 100.0
    topic_comp    = (topics  / max_topics)   * 100.0
    recency_comp  = (weighted / max_weighted) * 100.0
    narrative_scores[aid] = clip100(
        0.40 * pos_comp + 0.30 * topic_comp + 0.30 * recency_comp
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE 5 — RISK_FLAG_SCORE  (higher = riskier)
#   spike_risk:     any territory has week with streams > 3× that territory's mean → +50
#   sentiment_risk: each mention with sentiment < 0.3 adds 20 pts (capped 50)
#   total capped at 100
# ═══════════════════════════════════════════════════════════════════════════════
print("Computing risk flag scores...")

risk_scores: dict[str, float] = {}

for aid in ARTIST_IDS:
    risk = 0.0

    # Stream spike: check per territory to avoid cross-territory stream scale artefacts
    artist_charts = df_charts_known[df_charts_known['artist_id'] == aid]
    for ter in artist_charts['territory'].unique():
        ter_data = artist_charts[artist_charts['territory'] == ter]['streams_estimate']
        if len(ter_data) >= 2:
            mean_s = ter_data.mean()
            max_s  = ter_data.max()
            if mean_s > 0 and max_s > 3 * mean_s:
                risk += 50.0
                break  # one spike flag is enough

    # Negative sentiment risk
    neg_count = int((df_media[df_media['artist_id'] == aid]['sentiment_score'] < 0.3).sum())
    risk += min(50.0, neg_count * 20.0)

    risk_scores[aid] = clip100(risk)


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE 6 — AUDIENCE_FIT_[CATEGORY]
#   For each artist × brand category:
#     - age_match    up to 30 pts
#     - platform_match up to 25 pts
#     - gender_match   up to 25 pts
#     - engagement/reach up to 20 pts
#   Averaged across the artist's audience segments → 0–100
# ═══════════════════════════════════════════════════════════════════════════════
print("Computing audience fit scores...")

# Age range point maps per category
AFFINITY: dict[str, dict] = {
    "Beverages": {
        "age_pts":   {"18-24": 30, "25-34": 30, "13-17": 10, "35-44": 5,  "45+": 0},
        "plat_pts":  {"Instagram": 25, "TikTok": 25, "Spotify": 10, "YouTube": 5},
        "gender":    "neutral",
        "eng_min":   4.0,   # engagement_rate threshold
    },
    "Fashion": {
        "age_pts":   {"13-17": 30, "18-24": 30, "25-34": 20, "35-44": 5,  "45+": 0},
        "plat_pts":  {"Instagram": 25, "TikTok": 15, "Spotify": 5,  "YouTube": 5},
        "gender":    "female",   # bonus if gender_split_f > 55
        "eng_min":   3.0,
    },
    "Tech": {
        "age_pts":   {"18-24": 30, "25-34": 30, "13-17": 10, "35-44": 10, "45+": 0},
        "plat_pts":  {"YouTube": 25, "Spotify": 10, "Instagram": 5, "TikTok": 5},
        "gender":    "male",     # bonus if gender_split_m > 55
        "eng_min":   3.0,
    },
    "Sport": {
        "age_pts":   {"18-24": 25, "25-34": 25, "35-44": 20, "13-17": 15, "45+": 5},
        "plat_pts":  {"Instagram": 15, "YouTube": 15, "Spotify": 15, "TikTok": 10},
        "gender":    "neutral",
        "reach_min": 1_000_000,  # estimated_reach threshold
    },
    "Finance": {
        "age_pts":   {"25-34": 25, "35-44": 25, "45+": 20, "18-24": 10, "13-17": 0},
        "plat_pts":  {"Instagram": 15, "YouTube": 15, "Spotify": 15, "TikTok": 5},
        "gender":    "neutral",
        "eng_min":   2.0,
    },
}

# Pre-compute per-artist average engagement rate (from social_blade_growth)
engagement_map: dict[str, float] = {}
for aid in ARTIST_IDS:
    rows = df_social[df_social['artist_id'] == aid]
    engagement_map[aid] = float(rows['engagement_rate'].mean()) if len(rows) > 0 else 0.0

audience_fit_scores: dict[str, dict[str, float]] = {cat: {} for cat in AFFINITY}

for aid in ARTIST_IDS:
    segments = df_audience[df_audience['artist_id'] == aid]
    eng = engagement_map.get(aid, 0.0)

    for category, affin in AFFINITY.items():
        if len(segments) == 0:
            audience_fit_scores[category][aid] = 0.0
            continue

        seg_totals = []
        for _, seg in segments.iterrows():
            pts = 0.0

            # Age match (0–30)
            pts += affin["age_pts"].get(str(seg.get('age_range', '')), 0)

            # Platform match (0–25)
            pts += affin["plat_pts"].get(str(seg.get('platform_primary', '')), 0)

            # Gender match (0–25)
            gender_pref = affin["gender"]
            if gender_pref == "female":
                f_split = float(seg.get('gender_split_f', 50))
                pts += 25 if f_split > 55 else max(0.0, (f_split - 30) / 25 * 25)
            elif gender_pref == "male":
                m_split = float(seg.get('gender_split_m', 50))
                pts += 25 if m_split > 55 else max(0.0, (m_split - 30) / 25 * 25)
            else:  # neutral — always partial credit
                pts += 12.5

            # Engagement / reach (0–20)
            if 'eng_min' in affin:
                eng_min = affin['eng_min']
                pts += 20.0 if eng >= eng_min else max(0.0, eng / eng_min * 20.0)
            else:  # reach_min
                reach = float(seg.get('estimated_reach', 0))
                reach_min = affin['reach_min']
                pts += 20.0 if reach >= reach_min else max(0.0, reach / reach_min * 20.0)

            seg_totals.append(pts)

        raw = sum(seg_totals) / len(seg_totals) if seg_totals else 0.0
        audience_fit_scores[category][aid] = clip100(raw)


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE 1 — MOMENTUM_SCORE  (per artist × territory)
# SCORE 2 — TERRITORY_FIT_SCORE (per artist × territory)
# ═══════════════════════════════════════════════════════════════════════════════
print("Computing momentum and territory fit scores...")

# Pre-compute per-artist social growth component (same value across all territories)
social_component_map: dict[str, float] = {}
for aid in ARTIST_IDS:
    rows = df_social[df_social['artist_id'] == aid]
    if len(rows) == 0:
        social_component_map[aid] = 50.0
        continue
    avg_growth = float(rows['growth_pct'].mean())
    # 0% growth → 50, +10% → 100, -5% → 0  (range -5 to +10 maps to 0-100)
    social_component_map[aid] = clip100((avg_growth + 5.0) / 15.0 * 100.0)

# Pre-compute total streams per artist across all territories (latest week)
latest_date = df_charts_known['date'].max()
latest_charts = df_charts_known[df_charts_known['date'] == latest_date]

artist_total_streams: dict[str, float] = {}
for aid in ARTIST_IDS:
    rows = latest_charts[latest_charts['artist_id'] == aid]
    artist_total_streams[aid] = float(rows['streams_estimate'].sum()) if len(rows) > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# BUILD OUTPUT ROWS
# ═══════════════════════════════════════════════════════════════════════════════
print("Building output rows...")

output_rows = []

for _, artist in df_artists.iterrows():
    aid  = artist['artist_id']
    name = artist['name']

    for territory in TERRITORIES:
        ter_charts = df_charts_known[
            (df_charts_known['artist_id']  == aid) &
            (df_charts_known['territory'] == territory)
        ].sort_values('date')

        # ── MOMENTUM_SCORE ─────────────────────────────────────────────────
        if len(ter_charts) >= 2:
            curr = ter_charts.iloc[-1]
            prev = ter_charts.iloc[-2]

            # Chart position component (inverted: pos 1 = 100)
            inv_curr = max(0.0, 101.0 - float(curr['chart_position']))
            inv_prev = max(0.0, 101.0 - float(prev['chart_position']))
            improvement = inv_curr - inv_prev
            # Range: -100 to +100 → normalize to 0-100 (0 improvement = 50)
            pos_component = clip100((improvement + 100.0) / 2.0)

            # Stream growth component
            p_streams = float(prev['streams_estimate'])
            c_streams = float(curr['streams_estimate'])
            if p_streams > 0:
                growth_pct = (c_streams - p_streams) / p_streams * 100.0
            else:
                growth_pct = 0.0
            # -50% → 0, 0% → 33, +100% → 100 (using -50..+150 window)
            stream_component = clip100((growth_pct + 50.0) / 200.0 * 100.0)

        elif len(ter_charts) == 1:
            row = ter_charts.iloc[0]
            pos_component    = clip100(101.0 - float(row['chart_position']))
            stream_component = 50.0
        else:
            pos_component    = 0.0
            stream_component = 0.0

        social_component = social_component_map.get(aid, 50.0)

        momentum = clip100(
            0.40 * pos_component +
            0.30 * stream_component +
            0.30 * social_component
        )

        # ── TERRITORY_FIT_SCORE ─────────────────────────────────────────────
        # Proportion of artist's total (latest-week) streams coming from this territory
        if len(ter_charts) > 0:
            ter_streams   = float(
                latest_charts[
                    (latest_charts['artist_id'] == aid) &
                    (latest_charts['territory'] == territory)
                ]['streams_estimate'].sum()
            )
            total_streams = artist_total_streams.get(aid, 0.0)
            territory_fit_raw = (ter_streams / total_streams * 100.0) if total_streams > 0 else 0.0
        else:
            territory_fit_raw = 0.0

        output_rows.append({
            "artist_id":                  aid,
            "artist_name":                name,
            "territory":                  territory,
            "momentum_score":             momentum,
            "territory_fit_score":        clip100(territory_fit_raw),
            "cross_platform_score":       cross_platform_scores.get(aid, 0.0),
            "narrative_resonance_score":  narrative_scores.get(aid, 0.0),
            "risk_flag_score":            risk_scores.get(aid, 0.0),
            "audience_fit_beverages":     audience_fit_scores["Beverages"].get(aid, 0.0),
            "audience_fit_fashion":       audience_fit_scores["Fashion"].get(aid, 0.0),
            "audience_fit_tech":          audience_fit_scores["Tech"].get(aid, 0.0),
            "audience_fit_sport":         audience_fit_scores["Sport"].get(aid, 0.0),
            "audience_fit_finance":       audience_fit_scores["Finance"].get(aid, 0.0),
            "week_date":                  WEEK_DATE,
        })


# ─── Write output ────────────────────────────────────────────────────────────
df_out = pd.DataFrame(output_rows, columns=[
    "artist_id", "artist_name", "territory",
    "momentum_score", "territory_fit_score", "cross_platform_score",
    "narrative_resonance_score", "risk_flag_score",
    "audience_fit_beverages", "audience_fit_fashion",
    "audience_fit_tech", "audience_fit_sport", "audience_fit_finance",
    "week_date",
])

# ─── Write to database ────────────────────────────────────────────────────────
try:
    n = upsert_scores_weekly(output_rows)
    print(f"\n[DB] upserted {n} scores_weekly rows (incl. audience_fit child rows)")
except Exception as _e:
    print(f"\n[DB] scores_weekly upsert failed: {_e}")
    raise


# ─── Console summary: top 5 by momentum (averaged across territories) ────────
momentum_by_artist = (
    df_out.groupby(["artist_id", "artist_name"])["momentum_score"]
    .mean()
    .reset_index()
    .sort_values("momentum_score", ascending=False)
    .head(5)
)

# Full row for each top artist: use their highest-momentum territory row
print("\n" + "━" * 82)
print(f"  CDX — CSIE Scoring Complete   week_date={WEEK_DATE}")
print("━" * 82)
print(f"  {'Artist':<24} {'Terr':<10} {'Mom':>5} {'Fit':>5} {'XPlt':>5} "
      f"{'Narr':>5} {'Risk':>5} {'Bev':>5} {'Fash':>5} {'Tech':>5} {'Spt':>5} {'Fin':>5}")
print("  " + "─" * 78)

for _, row in momentum_by_artist.iterrows():
    aid = row['artist_id']
    # pick highest-momentum territory for display
    best = df_out[df_out['artist_id'] == aid].nlargest(1, 'momentum_score').iloc[0]
    print(
        f"  {best['artist_name']:<24} {best['territory']:<10} "
        f"{best['momentum_score']:>5.1f} "
        f"{best['territory_fit_score']:>5.1f} "
        f"{best['cross_platform_score']:>5.1f} "
        f"{best['narrative_resonance_score']:>5.1f} "
        f"{best['risk_flag_score']:>5.1f} "
        f"{best['audience_fit_beverages']:>5.1f} "
        f"{best['audience_fit_fashion']:>5.1f} "
        f"{best['audience_fit_tech']:>5.1f} "
        f"{best['audience_fit_sport']:>5.1f} "
        f"{best['audience_fit_finance']:>5.1f}"
    )

print("━" * 82)
print(f"  Total rows: {len(df_out)}  "
      f"({len(ARTIST_IDS)} artists × {len(TERRITORIES)} territories)")
print("━" * 82)
