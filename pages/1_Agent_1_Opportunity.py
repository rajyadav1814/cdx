from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_cdx import (
    AGENT_COLORS,
    AGENTS,
    configure_page,
    format_date,
    load_agent_dataframe,
    load_summary,
    section_header,
)

configure_page('CDX - Agent 1 Opportunity')

summary = load_summary()
data = load_agent_dataframe('agent1')

section_header(
    f"Agent {AGENTS['agent1']['id']} - {AGENTS['agent1']['name']}",
    AGENTS['agent1']['sub'],
    accent=AGENT_COLORS['agent1'],
)

top = st.columns(4)
with top[0]:
    st.metric('High opportunities', summary.get('agent1', {}).get('high_opportunities', 0))
with top[1]:
    st.metric('Medium opportunities', summary.get('agent1', {}).get('medium_opportunities', 0))
with top[2]:
    st.metric('Watch opportunities', summary.get('agent1', {}).get('watch_opportunities', 0))
with top[3]:
    st.metric('Top artist', summary.get('agent1', {}).get('top_artist') or '—')

st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)

if data.empty:
    st.info('Agent 1 output is not available yet.')
else:
    ranked = data.copy().sort_values('momentum_score', ascending=False)
    cards = st.columns(3)
    for idx, row in enumerate(ranked.head(6).itertuples(index=False)):
        with cards[idx % 3]:
            territory_2 = f" · {row.top_territory_2}" if getattr(row, 'top_territory_2', None) else ''
            st.markdown(
                f'''
                <div class="cdx-card" style="border-left: 2px solid {AGENT_COLORS['agent1']}; margin-bottom:0.75rem;">
                    <div class="cdx-label">Rank {getattr(row, 'rank', idx + 1)}</div>
                    <h3 class="cdx-card-title">{row.artist_name}</h3>
                    <div class="cdx-subtle">{row.top_territory_1}{territory_2}</div>
                    <div style="margin-top:0.8rem; display:flex; gap:0.6rem; flex-wrap:wrap;">
                        <span class="cdx-pill green">{row.opportunity_class}</span>
                        <span class="cdx-pill muted">Momentum {float(row.momentum_score):.1f}</span>
                        <span class="cdx-pill muted">Cross {float(row.cross_platform_score):.1f}</span>
                    </div>
                    <div class="cdx-subtle" style="margin-top:0.8rem; line-height:1.55;">{row.narrative}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

st.markdown('<div class="cdx-divider"></div>', unsafe_allow_html=True)
section_header('Ranked artists', 'Momentum and cross-platform scores', accent=AGENT_COLORS['agent1'])
display = ranked[[
    'rank',
    'artist_name',
    'momentum_score',
    'cross_platform_score',
    'risk_flag_score',
    'opportunity_class',
    'top_territory_1',
    'top_territory_2',
    'generated_at',
]].copy()
display['generated_at'] = display['generated_at'].map(format_date)
st.dataframe(display, width="stretch", hide_index=True)
