from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_cdx import (
    AGENTS,
    AGENT_COLORS,
    BRAND_GOLD,
    BRAND_RED,
    configure_page,
    format_currency,
    format_date,
    format_number,
    format_reach,
    get_default_summary,
    load_agent_dataframe,
    load_models,
    load_summary,
    render_brand_image,
    render_progress_bar,
    run_pipeline,
    section_header,
)


configure_page("CDX - Overview")


def _agent_card(agent_key: str, count: str, subtitle: str, page: str) -> None:
    agent = AGENTS[agent_key]
    st.markdown(
        f"""
        <div class="cdx-card" style="border-left: 2px solid {agent['color']};">
            <div class="cdx-label" style="color:{agent['color']}">AGENT {agent['id']}</div>
            <h3 class="cdx-card-title" style="margin-top:0.15rem;">{agent['name']}</h3>
            <div class="cdx-subtle">{agent['sub']}</div>
            <div style="margin-top:0.75rem; display:flex; justify-content:space-between; align-items:center;">
                <span class="cdx-mono" style="color:var(--text-secondary);">{count}</span>
                <span class="cdx-subtle" style="font-size:0.8rem;">{subtitle}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if hasattr(st, "switch_page"):
        if st.button(f"Open {agent['name']}", key=f"open_{agent_key}", width="stretch"):
            st.switch_page(page)
    else:
        st.caption(f"Open: {page}")


def _opportunity_badge(cls: str) -> str:
    tone = {
        "HIGH": "green",
        "MEDIUM": "gold",
        "WATCH": "muted",
    }.get(cls, "muted")
    return f'<span class="cdx-pill {tone}">{cls}</span>'


def render_overview() -> None:
    summary = load_summary()
    agent1 = summary.get("agent1", {})
    agent2 = summary.get("agent2", {})
    agent3 = summary.get("agent3", {})
    agent4 = summary.get("agent4", {})

    agent1_df = load_agent_dataframe("agent1")
    agent2_df = load_agent_dataframe("agent2")
    agent3_df = load_agent_dataframe("agent3")
    agent4_df = load_agent_dataframe("agent4")

    run_col, brand_col = st.columns([0.78, 0.22])
    with brand_col:
        render_brand_image()
        st.markdown(
            """
            <div class="cdx-card" style="margin-top:0.8rem;">
                <div class="cdx-label">Presented to</div>
                <h3 class="cdx-card-title" style="color:var(--brand-gold);">Sony Music Latin</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with run_col:
        section_header(
            "Commercial Signal Intelligence",
            "Chromadata x Sony Music Latin",
            accent=BRAND_RED,
        )
        st.markdown(
            """
            <div class="cdx-card">
                <div class="cdx-subtle">
                    Four AI agents transform music-industry signals into explainable commercial
                    recommendations for brand partnership decisions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("Artists processed", summary.get("artists_processed", 0))
    with summary_cols[1]:
        st.metric("Agent 1 high + medium", int(agent1.get("high_opportunities", 0)) + int(agent1.get("medium_opportunities", 0)))
    with summary_cols[2]:
        st.metric("Agent 4 avg base ROI", f"{float(agent4.get('avg_base_roi', 0) or 0):.2f}x")

    controls = st.columns([0.38, 0.18, 0.18, 0.18, 0.08])
    with controls[0]:
        st.markdown(
            f"""
            <div class="cdx-card" style="border-left: 2px solid {BRAND_RED};">
                <div class="cdx-label">Pipeline</div>
                <h3 class="cdx-card-title">Run the full agent stack</h3>
                <div class="cdx-subtle">Agent 1 → Agent 2 → Agent 3 → Agent 4</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with controls[1]:
        if st.button("Run Pipeline", type="primary", width="stretch"):
            result = run_pipeline()
            st.success(f"Pipeline started at {format_date(result['timestamp'])}")
    with controls[2]:
        st.metric("Last run", format_date(summary.get("run_timestamp")))
    with controls[3]:
        st.metric("Models", len(load_models().get("providers", {})))
    with controls[4]:
        st.metric("Status", "Live" if summary.get("run_timestamp") else "Idle")

    st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)
    section_header("Agents", "Navigation", accent=BRAND_RED)

    cards = st.columns(4)
    with cards[0]:
        _agent_card("agent1", f"{int(agent1.get('high_opportunities', 0)) + int(agent1.get('medium_opportunities', 0))} results", "Opportunity discovery", "pages/1_Agent_1_Opportunity.py")
    with cards[1]:
        _agent_card("agent2", f"{int(agent2.get('briefs_generated', 0))} briefs", "Strategy synthesis", "pages/2_Agent_2_Strategy.py")
    with cards[2]:
        _agent_card("agent3", f"{len(agent3_df)} audience rows", "Audience fit", "pages/3_Agent_3_Audience.py")
    with cards[3]:
        _agent_card("agent4", f"{len(agent4_df)} ROI rows", "ROI forecasting", "pages/4_Agent_4_ROI.py")

    st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)
    left, right = st.columns([0.62, 0.38])

    with left:
        section_header("Agent 1 ranking", "Top momentum by artist", accent=AGENT_COLORS["agent1"])
        if not agent1_df.empty:
            ranked = agent1_df.copy().sort_values("momentum_score", ascending=False).head(10)
            ranked["momentum_score"] = ranked["momentum_score"].map(lambda x: f"{float(x):.1f}")
            ranked["cross_platform_score"] = ranked["cross_platform_score"].map(lambda x: f"{float(x):.1f}")
            ranked["risk_flag_score"] = ranked["risk_flag_score"].map(lambda x: f"{float(x):.1f}")
            ranked["opportunity_class"] = ranked["opportunity_class"].map(_opportunity_badge)
            st.markdown(ranked[["artist_name", "momentum_score", "cross_platform_score", "risk_flag_score", "opportunity_class"]].to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("Agent 1 output is not available yet.")

    with right:
        section_header("Brand signals", "Agent 2 / 3 / 4 snapshots", accent=BRAND_GOLD)
        cat_dist = agent2.get("best_brand_category_distribution", {})
        if cat_dist:
            max_count = max(cat_dist.values()) if cat_dist else 1
            for category, count in cat_dist.items():
                render_progress_bar(count, max_count, AGENT_COLORS["agent2"], category)
                st.caption(f"{category}: {count}")
        else:
            st.info("Run the pipeline to populate brand categories.")

        st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)
        st.metric("Avg reach", format_reach(agent3.get("avg_reach")))
        st.metric("Highest ROI artist", agent4.get("highest_roi_artist") or "—")
        st.metric("Highest ROI multiple", f"{float(agent4.get('highest_roi_multiple', 0) or 0):.2f}x")


render_overview()

