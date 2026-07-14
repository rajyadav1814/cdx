from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_cdx import (
    AGENT_COLORS,
    AGENT_SUGGESTIONS,
    AGENTS,
    configure_page,
    format_date,
    get_chat_history,
    load_agent_dataframe,
    render_chat_panel,
    render_progress_bar,
    section_header,
)

configure_page('CDX - Agent 2 Strategy')

data = load_agent_dataframe('agent2')
artist_options = sorted(data['artist_name'].dropna().astype(str).unique().tolist()) if not data.empty else []

left, right = st.columns([0.38, 0.62], gap='large')
with left:
    selected_model, artist_filter = render_chat_panel(
        'agent2',
        AGENT_COLORS['agent2'],
        artist_options,
        AGENT_SUGGESTIONS['agent2'],
        AGENTS['agent2']['name'],
        AGENTS['agent2']['sub'],
    )

with right:
    section_header(
        f"Agent {AGENTS['agent2']['id']} analytics",
        'Brand-fit briefs and activation guidance',
        accent=AGENT_COLORS['agent2'],
    )

    if data.empty:
        st.info('Agent 2 output is not available yet.')
    else:
        view = data.copy()
        if artist_filter:
            view = view[view['artist_name'] == artist_filter]

        metrics = st.columns(4)
        with metrics[0]:
            st.metric('Briefs', len(view))
        with metrics[1]:
            st.metric('Top category', view['best_brand_category'].mode().iloc[0] if not view.empty else '—')
        with metrics[2]:
            st.metric('Common channel', view['recommended_channel'].mode().iloc[0] if not view.empty else '—')
        with metrics[3]:
            st.metric('Latest run', format_date(view['generated_at'].max() if not view.empty else None))

        st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)
        section_header('Brand category mix', 'Distribution by best-fit category', accent=AGENT_COLORS['agent2'])
        cat_counts = view['best_brand_category'].value_counts() if not view.empty else pd.Series(dtype=int)
        if cat_counts.empty:
            st.caption('No category data available for the current selection.')
        else:
            max_count = int(cat_counts.max())
            for category, count in cat_counts.items():
                render_progress_bar(count, max_count, AGENT_COLORS['agent2'], category)
                st.caption(f'{category}: {count}')

        st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)
        section_header('Top briefs', 'Strategy synthesis rows', accent=AGENT_COLORS['agent2'])
        display = view.sort_values('brand_fit_score', ascending=False)[[
            'artist_name',
            'best_brand_category',
            'brand_fit_score',
            'recommended_channel',
            'sentiment_risk',
            'generated_at',
        ]].copy()
        display['generated_at'] = display['generated_at'].map(format_date)
        st.dataframe(display, width="stretch", hide_index=True)

        if not view.empty:
            focused = view.sort_values('brand_fit_score', ascending=False).iloc[0]
            st.markdown(
                f'''
                <div class="cdx-card" style="margin-top:0.85rem; border-left: 2px solid {AGENT_COLORS['agent2']};">
                    <div class="cdx-label">Focus brief</div>
                    <h3 class="cdx-card-title">{focused.artist_name}</h3>
                    <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.65rem;">
                        <span class="cdx-pill purple">{focused.best_brand_category}</span>
                        <span class="cdx-pill muted">Fit {float(focused.brand_fit_score):.0f}</span>
                        <span class="cdx-pill muted">{focused.recommended_channel}</span>
                    </div>
                    <div class="cdx-subtle" style="margin-top:0.85rem; line-height:1.6;">{focused.strategic_brief}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
