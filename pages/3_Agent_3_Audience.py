from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_cdx import (
    AGENT_COLORS,
    AGENT_SUGGESTIONS,
    AGENTS,
    configure_page,
    format_date,
    format_reach,
    load_agent_dataframe,
    render_chat_panel,
    render_progress_bar,
    section_header,
)

configure_page('CDX - Agent 3 Audience')

data = load_agent_dataframe('agent3')
artist_options = sorted(data['artist_name'].dropna().astype(str).unique().tolist()) if not data.empty else []

left, right = st.columns([0.38, 0.62], gap='large')
with left:
    selected_model, artist_filter = render_chat_panel(
        'agent3',
        AGENT_COLORS['agent3'],
        artist_options,
        AGENT_SUGGESTIONS['agent3'],
        AGENTS['agent3']['name'],
        AGENTS['agent3']['sub'],
    )

with right:
    section_header(
        f"Agent {AGENTS['agent3']['id']} analytics",
        'Audience fit and confidence',
        accent=AGENT_COLORS['agent3'],
    )

    if data.empty:
        st.info('Agent 3 output is not available yet.')
    else:
        view = data.copy()
        if artist_filter:
            view = view[view['artist_name'] == artist_filter]

        metrics = st.columns(4)
        with metrics[0]:
            st.metric('Rows', len(view))
        with metrics[1]:
            st.metric('Avg reach', format_reach(view['total_reach'].mean() if not view.empty else 0))
        with metrics[2]:
            st.metric('High confidence', f"{(view['data_confidence'].eq('HIGH').mean() * 100 if not view.empty else 0):.0f}%")
        with metrics[3]:
            st.metric('First-party avg', f"{(view['firstparty_pct'].mean() if not view.empty else 0):.0f}%")

        st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)
        section_header('Confidence mix', 'Proxy vs first-party balance', accent=AGENT_COLORS['agent3'])
        if not view.empty:
            by_conf = view['data_confidence'].value_counts()
            max_count = int(by_conf.max()) if not by_conf.empty else 1
            for conf, count in by_conf.items():
                tone = AGENT_COLORS['agent3'] if conf == 'HIGH' else '#D4924A' if conf == 'MEDIUM' else '#8A8A9A'
                render_progress_bar(count, max_count, tone, conf)
                st.caption(f'{conf}: {count}')

        st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)
        section_header('Audience rows', 'Primary and secondary markets', accent=AGENT_COLORS['agent3'])
        display = view.sort_values('audience_fit_score', ascending=False)[[
            'artist_name',
            'best_brand_category',
            'total_reach',
            'primary_market',
            'secondary_market',
            'primary_platform',
            'audience_fit_score',
            'data_confidence',
            'proxy_pct',
            'firstparty_pct',
            'generated_at',
        ]].copy()
        display['total_reach'] = display['total_reach'].map(format_reach)
        display['generated_at'] = display['generated_at'].map(format_date)
        st.dataframe(display, width="stretch", hide_index=True)

        if not view.empty:
            focused = view.sort_values('total_reach', ascending=False).iloc[0]
            st.markdown(
                f'''
                <div class="cdx-card" style="margin-top:0.85rem; border-left: 2px solid {AGENT_COLORS['agent3']};">
                    <div class="cdx-label">Largest reach</div>
                    <h3 class="cdx-card-title">{focused.artist_name}</h3>
                    <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.65rem;">
                        <span class="cdx-pill blue">{focused.best_brand_category}</span>
                        <span class="cdx-pill muted">Reach {format_reach(focused.total_reach)}</span>
                        <span class="cdx-pill muted">Fit {float(focused.audience_fit_score):.0f}</span>
                    </div>
                    <div class="cdx-subtle" style="margin-top:0.85rem; line-height:1.6;">{focused.audience_summary}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
