from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_cdx import (
    AGENT_COLORS,
    AGENT_SUGGESTIONS,
    AGENTS,
    configure_page,
    format_currency,
    format_date,
    load_agent_dataframe,
    render_chat_panel,
    render_progress_bar,
    section_header,
)

configure_page('CDX - Agent 4 ROI')

data = load_agent_dataframe('agent4')
artist_options = sorted(data['artist_name'].dropna().astype(str).unique().tolist()) if not data.empty else []

left, right = st.columns([0.38, 0.62], gap='large')
with left:
    selected_model, artist_filter = render_chat_panel(
        'agent4',
        AGENT_COLORS['agent4'],
        artist_options,
        AGENT_SUGGESTIONS['agent4'],
        AGENTS['agent4']['name'],
        AGENTS['agent4']['sub'],
    )

with right:
    section_header(
        f"Agent {AGENTS['agent4']['id']} analytics",
        'ROI forecasting and scenario planning',
        accent=AGENT_COLORS['agent4'],
    )

    if data.empty:
        st.info('Agent 4 output is not available yet.')
    else:
        view = data.copy()
        if artist_filter:
            view = view[view['artist_name'] == artist_filter]

        metrics = st.columns(4)
        with metrics[0]:
            st.metric('Rows', len(view))
        with metrics[1]:
            st.metric('Avg base ROI', f"{(view['base_roi'].mean() if not view.empty else 0):.2f}x")
        with metrics[2]:
            st.metric('Top ROI artist', view.sort_values('base_roi', ascending=False)['artist_name'].iloc[0] if not view.empty else '—')

        st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)
        section_header('Scenario mix', 'Conservative to optimistic ROI spread', accent=AGENT_COLORS['agent4'])
        if not view.empty:
            display = view.sort_values('base_roi', ascending=False)[[
                'artist_name',
                'brand_category',
                'reference_budget',
                'conservative_roi',
                'base_roi',
                'optimistic_roi',
                'base_revenue',
                'recommended_scenario',
                'risk_flag',
                'generated_at',
            ]].copy()
            display['reference_budget'] = display['reference_budget'].map(format_currency)
            display['base_revenue'] = display['base_revenue'].map(format_currency)
            display['generated_at'] = display['generated_at'].map(format_date)
            st.dataframe(display, width="stretch", hide_index=True)

            best = view.sort_values('base_roi', ascending=False).iloc[0]
            st.markdown(
                f'''
                <div class="cdx-card" style="margin-top:0.85rem; border-left: 2px solid {AGENT_COLORS['agent4']};">
                    <div class="cdx-label">Focus scenario</div>
                    <h3 class="cdx-card-title">{best.artist_name}</h3>
                    <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.65rem;">
                        <span class="cdx-pill gold">{best.recommended_scenario}</span>
                        <span class="cdx-pill muted">Base {float(best.base_roi):.2f}x</span>
                        <span class="cdx-pill muted">Risk {best.risk_flag}</span>
                    </div>
                    <div class="cdx-subtle" style="margin-top:0.85rem; line-height:1.6;">{best.investment_narrative}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
