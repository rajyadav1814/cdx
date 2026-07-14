import React, { useContext, useState } from 'react'
import * as Icons from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight } from 'lucide-react'
import { NavigationContext } from '@/components/layout/AppShell'
import { AGENTS } from '@/lib/constants'
import { api } from '@/lib/api'
import { usePipeline } from '@/hooks/usePipeline'
import KpiCard from '@/components/shared/KpiCard'
import AgentBadge from '@/components/shared/AgentBadge'
import SectionLabel from '@/components/shared/SectionLabel'
import StatusDot from '@/components/shared/StatusDot'

// ─── helpers ──────────────────────────────────────────────────────────────────

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString([], {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

// Artists confirmed on Sony Music Latin roster (via Wikipedia category)
const SONY_MUSIC_LATIN_ARTISTS = new Set([
  'Ryan Castro', 'Fuerza Regida', 'Romeo Santos', 'Ozuna', 'Kapo',
  'Rauw Alejandro', 'Camilo', 'Maluma', 'TINI', 'Arcángel', 'Anuel AA',
  'Christian Nodal', 'Zion & Lennox', 'Residente', 'Chencho Corleone',
  'C. Tangana', 'Daddy Yankee', 'Prince Royce', 'Gusttavo Lima', 'Shakira',
  'Trueno', 'Paloma Mami', 'Nicky Jam', 'Cauty',
])

const BRAND_BARS = [
  { key: 'Beverage', label: 'BEVERAGE',  color: '#1D9E75' },
  { key: 'Fashion',  label: 'FASHION',   color: '#8B7FE8' },
  { key: 'Tech',     label: 'TECH',      color: '#4A9EE8' },
  { key: 'Sport',    label: 'SPORT',     color: '#D4924A' },
  { key: 'Finance',  label: 'FINANCE',   color: '#D4A017' },
]

// ─── sub-components ───────────────────────────────────────────────────────────

function AgentCard({ agent, count, onNavigate }) {
  const Icon = agent.icon ? Icons[agent.icon] : null

  return (
    <button
      className="card flex items-center gap-4 w-full text-left cursor-pointer"
      style={{ borderLeft: `2px solid ${agent.color}` }}
      onClick={() => onNavigate(agent.key)}
    >
      <AgentBadge id={agent.id} color={agent.color} size="md" />
      <div className="min-w-0 flex-1">
        <span className="label" style={{ color: agent.color }}>AGENT {agent.id}</span>
        <div
          className="font-display font-bold text-text-primary leading-tight flex items-center gap-1.5"
          style={{ fontSize: 13 }}
        >
          {Icon && <Icon size={12} style={{ color: agent.color, flexShrink: 0 }} />}
          {agent.name}
        </div>
        <div className="text-text-muted text-xs mt-0.5">
          {count != null ? `${count} results` : 'Not run yet'}
        </div>
      </div>
      <ChevronRight size={14} className="text-text-muted flex-shrink-0" />
    </button>
  )
}

const OPP_ROW_STYLE = {
  HIGH:   { borderLeft: '2px solid rgba(29,158,117,0.55)',  backgroundColor: 'rgba(29,158,117,0.04)' },
  MEDIUM: { borderLeft: '2px solid rgba(212,146,74,0.45)',  backgroundColor: 'rgba(212,146,74,0.03)' },
  WATCH:  { borderLeft: '2px solid rgba(255,255,255,0.07)', backgroundColor: 'transparent' },
}

function LeaderboardRow({ rank, artist, roiData, onNavigate }) {
  const roi = roiData?.find(
    r => r.artist_id === artist.artist_id || r.artist_name === artist.artist_name
  )
  const isSML   = SONY_MUSIC_LATIN_ARTISTS.has(artist.artist_name)
  const rowStyle = OPP_ROW_STYLE[artist.opportunity_class] || OPP_ROW_STYLE.WATCH

  const opportunityBadgeClass = {
    HIGH:   'badge badge-green',
    MEDIUM: 'badge badge-amber',
    WATCH:  'badge badge-muted',
  }[artist.opportunity_class] || 'badge badge-muted'

  const handleClick = () => {
    sessionStorage.setItem('cdx_artist_carryover', artist.artist_name)
    onNavigate('agent2')
  }

  return (
    <tr
      className="border-b border-white/[0.04] hover:bg-bg-surface2 transition-colors cursor-pointer"
      style={rowStyle}
      onClick={handleClick}
    >
      <td className="px-3 py-2.5 font-mono text-xs text-text-muted w-8">{rank}</td>
      <td className="px-3 py-2.5">
        <div className="flex items-center gap-2">
          {isSML && (
            <img
              src="/brand/sonymusiclatin_icon.jpeg"
              alt="Sony Music Latin"
              title="Sony Music Latin artist"
              style={{ width: 14, height: 14, borderRadius: 2, flexShrink: 0 }}
              className="object-contain opacity-90"
            />
          )}
          <span className="font-display font-bold text-sm text-text-primary leading-none">
            {artist.artist_name}
          </span>
        </div>
      </td>
      <td className="px-3 py-2.5 text-xs text-text-secondary">
        {artist.top_territory_1}
        {artist.top_territory_2 ? ` · ${artist.top_territory_2}` : ''}
      </td>
      <td className="px-3 py-2.5">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1 bg-bg-surface3 rounded-sm overflow-hidden" style={{ maxWidth: 64 }}>
            <div
              style={{
                width: `${Math.min((Number(artist.momentum_score) / 35) * 100, 100)}%`,
                height: 4,
                borderRadius: 1,
                backgroundColor: Number(artist.momentum_score) > 25
                  ? '#1D9E75'
                  : Number(artist.momentum_score) > 18
                    ? '#D4924A'
                    : '#CC1B1B',
              }}
            />
          </div>
          <span className="font-mono text-xs text-text-secondary w-8">
            {Number(artist.momentum_score).toFixed(1)}
          </span>
        </div>
      </td>
      <td className="px-3 py-2.5">
        <span className={opportunityBadgeClass}>{artist.opportunity_class}</span>
      </td>
      <td className="px-3 py-2.5 font-mono text-xs" style={{ color: '#D4924A' }}>
        {roi ? `${Number(roi.base_roi).toFixed(2)}×` : '—'}
      </td>
      <td className="px-3 py-2.5">
        <span
          className="text-xs font-medium cursor-pointer"
          style={{ color: '#1D9E75' }}
          onClick={e => { e.stopPropagation(); handleClick() }}
        >
          View →
        </span>
      </td>
    </tr>
  )
}

function BrandCategoryBar({ bar, agent2Data, mode, maxCount, selected, onClick }) {
  if (!agent2Data || agent2Data.length === 0) {
    return (
      <div className="flex items-center gap-3">
        <span className="label w-20 flex-shrink-0" style={{ color: bar.color }}>{bar.label}</span>
        <div className="flex-1 h-1.5 bg-bg-surface3 rounded-full" />
        <span className="text-xs text-text-muted w-24 text-right">No data</span>
      </div>
    )
  }

  const total = agent2Data.length

  const allInCat = agent2Data.filter(d => d.best_brand_category === bar.key).length

  let count, label, pct
  if (mode === 'all') {
    const avgScore = allInCat > 0
      ? agent2Data
          .filter(d => d.best_brand_category === bar.key)
          .reduce((sum, d) => sum + Number(d.brand_fit_score), 0) / allInCat
      : 0
    count = allInCat
    label = `${count} artists · ${avgScore.toFixed(0)} avg`
    pct   = maxCount > 0 ? (count / maxCount) * 100 : 0
  } else {
    const highFit = agent2Data.filter(
      d => d.best_brand_category === bar.key && Number(d.brand_fit_score) > 80
    ).length
    count = highFit
    label = `${highFit} of ${allInCat} HIGH fit`
    pct   = maxCount > 0 ? (count / maxCount) * 100 : 0
  }

  return (
    <button
      className="flex items-center gap-3 w-full text-left rounded-sm transition-all"
      style={{
        padding: '4px 6px',
        margin: '-4px -6px',
        width: 'calc(100% + 12px)',
        backgroundColor: selected ? `${bar.color}14` : 'transparent',
        outline: selected ? `1px solid ${bar.color}40` : '1px solid transparent',
        cursor: 'pointer',
      }}
      onClick={onClick}
    >
      <span className="label w-20 flex-shrink-0" style={{ color: bar.color }}>{bar.label}</span>
      <div className="flex-1 h-1.5 bg-bg-surface3 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: bar.color }}
        />
      </div>
      <span className="text-xs text-text-muted w-24 text-right">{label}</span>
    </button>
  )
}

function BrandCategorySection({ agent2Data, agent1Data }) {
  const [mode, setMode] = useState('all')
  const [selectedCategory, setSelectedCategory] = useState(null)

  const maxCount = React.useMemo(() => {
    if (!agent2Data || agent2Data.length === 0) return 1
    return Math.max(
      ...BRAND_BARS.map(bar => {
        if (mode === 'all') {
          return agent2Data.filter(d => d.best_brand_category === bar.key).length
        }
        return agent2Data.filter(
          d => d.best_brand_category === bar.key && Number(d.brand_fit_score) > 80
        ).length
      })
    ) || 1
  }, [agent2Data, mode])

  const selectedBar = BRAND_BARS.find(b => b.key === selectedCategory)

  // Artists in the selected category, sorted by brand_fit_score desc
  const drilldownArtists = React.useMemo(() => {
    if (!selectedCategory || !agent2Data) return []
    return agent2Data
      .filter(d => d.best_brand_category === selectedCategory)
      .map(d => {
        const a1 = agent1Data?.find(a => a.artist_id === d.artist_id || a.artist_name === d.artist_name)
        return { ...d, opportunity_class: a1?.opportunity_class ?? 'WATCH' }
      })
      .sort((a, b) => Number(b.brand_fit_score) - Number(a.brand_fit_score))
  }, [selectedCategory, agent2Data, agent1Data])

  const handleBarClick = (key) => setSelectedCategory(prev => prev === key ? null : key)

  return (
    <div>
      <div className="flex items-center justify-between mt-1 mb-3">
        <SectionLabel>BRAND CATEGORY SIGNALS</SectionLabel>
        <div
          className="flex items-center gap-0.5 p-0.5 rounded-sm"
          style={{ backgroundColor: '#0D0D18', border: '1px solid rgba(255,255,255,0.08)' }}
        >
          {[
            { key: 'all',     label: 'All Artists' },
            { key: 'highfit', label: 'HIGH Fit Only' },
          ].map(opt => (
            <button
              key={opt.key}
              onClick={() => setMode(opt.key)}
              className="px-3 py-1 text-xs font-mono transition-colors rounded-sm"
              style={
                mode === opt.key
                  ? { backgroundColor: '#CC1B1B', color: '#fff' }
                  : { color: 'rgba(255,255,255,0.45)' }
              }
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="card space-y-3">
        {BRAND_BARS.map(bar => (
          <BrandCategoryBar
            key={bar.key}
            bar={bar}
            agent2Data={agent2Data}
            mode={mode}
            maxCount={maxCount}
            selected={selectedCategory === bar.key}
            onClick={() => handleBarClick(bar.key)}
          />
        ))}
        <div className="pt-1" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <p className="text-xs text-text-muted">
            {selectedCategory
              ? `Showing ${selectedBar?.label} — click again to deselect · Click any other category to switch`
              : mode === 'all'
                ? 'Click a category bar to see artist breakdown below · Bars scaled to largest category'
                : 'Click a category bar to see HIGH fit artists below · Bars scaled to largest category'}
          </p>
        </div>
      </div>

      {/* ── Drill-down table ────────────────���─────────────────────── */}
      {selectedCategory && selectedBar && drilldownArtists.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center gap-3 mb-3">
            <div
              className="h-4 w-0.5 flex-shrink-0"
              style={{ backgroundColor: selectedBar.color }}
            />
            <SectionLabel style={{ color: selectedBar.color }}>
              {selectedBar.label.toUpperCase()} — ARTIST FIT BREAKDOWN
            </SectionLabel>
            <span className="font-mono text-xs text-text-muted">
              {drilldownArtists.length} artists
            </span>
          </div>

          <div className="card p-0 overflow-hidden">
            <div style={{ maxHeight: 520, overflowY: 'auto' }}>
              <table className="w-full text-xs" style={{ minWidth: 680, tableLayout: 'fixed' }}>
                <colgroup>
                  <col style={{ width: 32 }} />
                  <col style={{ width: 168 }} />
                  <col style={{ width: 80 }} />
                  <col style={{ width: 112 }} />
                  <col />
                </colgroup>
                <thead style={{ position: 'sticky', top: 0, zIndex: 1, backgroundColor: '#0D0D18' }}>
                  <tr className="border-b border-white/[0.06]">
                    <th className="px-3 py-2 text-left label">#</th>
                    <th className="px-3 py-2 text-left label">ARTIST</th>
                    <th className="px-3 py-2 text-left label">FIT</th>
                    <th className="px-3 py-2 text-left label">CHANNEL</th>
                    <th className="px-3 py-2 text-left label">STRATEGY BRIEF</th>
                  </tr>
                </thead>
                <tbody>
                  {drilldownArtists.map((artist, i) => {
                    const isSML = SONY_MUSIC_LATIN_ARTISTS.has(artist.artist_name)
                    const oppClass = artist.opportunity_class
                    const rowStyle = OPP_ROW_STYLE[oppClass] || OPP_ROW_STYLE.WATCH
                    const badgeClass = { HIGH: 'badge badge-green', MEDIUM: 'badge badge-amber', WATCH: 'badge badge-muted' }[oppClass] || 'badge badge-muted'
                    const sentences = (artist.strategic_brief || '')
                      .split(/(?<=[.!?])\s+/)
                      .map(s => s.trim())
                      .filter(Boolean)

                    return (
                      <tr
                        key={artist.artist_id || artist.artist_name}
                        className="border-b border-white/[0.04] align-top"
                        style={rowStyle}
                      >
                        <td className="px-3 py-2 font-mono text-text-muted">{i + 1}</td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {isSML && (
                              <img
                                src="/brand/sonymusiclatin_icon.jpeg"
                                alt="Sony Music Latin"
                                title="Sony Music Latin artist"
                                style={{ width: 12, height: 12, borderRadius: 2, flexShrink: 0 }}
                                className="object-contain opacity-90"
                              />
                            )}
                            <span className="font-display font-bold text-text-primary" style={{ fontSize: 12 }}>
                              {artist.artist_name}
                            </span>
                            <span className={badgeClass}>{oppClass}</span>
                          </div>
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-1.5">
                            <div className="h-1 rounded-sm overflow-hidden" style={{ width: 32, backgroundColor: 'rgba(255,255,255,0.08)' }}>
                              <div
                                style={{
                                  width: `${Math.min(Number(artist.brand_fit_score), 100)}%`,
                                  height: '100%',
                                  backgroundColor: selectedBar.color,
                                  borderRadius: 1,
                                }}
                              />
                            </div>
                            <span className="font-mono text-text-secondary" style={{ fontSize: 11 }}>
                              {Number(artist.brand_fit_score).toFixed(0)}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-2 text-text-muted" style={{ fontSize: 10 }}>
                          {artist.recommended_channel || '—'}
                        </td>
                        <td className="px-3 py-2">
                          {sentences.length > 0 ? sentences.map((s, idx) => (
                            <p
                              key={idx}
                              className="text-text-secondary"
                              style={{ fontSize: 11, lineHeight: 1.5, marginBottom: idx < sentences.length - 1 ? 4 : 0 }}
                            >
                              {s}
                            </p>
                          )) : <span className="text-text-muted">—</span>}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── main panel ───────────────────────────────────────────────────────────────

export default function OverviewPanel() {
  const navigate = useContext(NavigationContext)

  const { data: summary } = useQuery({
    queryKey: ['summary'],
    queryFn: api.getSummary,
    staleTime: 10000,
  })
  const { data: agent1Data } = useQuery({
    queryKey: ['agent1'],
    queryFn: api.getAgent1,
  })
  const { data: agent2Data } = useQuery({
    queryKey: ['agent2'],
    queryFn: api.getAgent2,
  })
  const { data: agent3Data } = useQuery({
    queryKey: ['agent3'],
    queryFn: api.getAgent3,
  })
  const { data: agent4Data } = useQuery({
    queryKey: ['agent4'],
    queryFn: api.getAgent4,
  })

  const pipeline = usePipeline()

  // Agent result counts
  const agentCounts = {
    agent1: summary
      ? (summary.agent1?.high_opportunities ?? 0) + (summary.agent1?.medium_opportunities ?? 0)
      : null,
    agent2: summary?.agent2?.briefs_generated ?? null,
    agent3: agent3Data?.length ?? null,
    agent4: agent4Data?.length ?? null,
  }

  // All artists ranked by momentum
  const sortedArtists = agent1Data
    ? [...agent1Data].sort((a, b) => Number(b.momentum_score) - Number(a.momentum_score))
    : []

  const dotStatus = pipeline.status === 'running'
    ? 'fresh'
    : summary?.run_timestamp
      ? 'fresh'
      : 'idle'

  return (
    <div className="h-full overflow-y-auto bg-bg-base">
      <div className="p-6 space-y-8 max-w-7xl mx-auto">

        {/* ── Section 1: Hero header ─────────────────────────────── */}
        <div className="card bg-grid" style={{ padding: '2rem' }}>
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-8">
            {/* Left */}
            <div className="flex-1">
              <SectionLabel>COMMERCIAL SIGNAL INTELLIGENCE (CSI)</SectionLabel>
              <div className="flex items-center gap-3 mt-2">
                <img
                  src="/brand/sonymusiclatin_icon.jpeg"
                  alt=""
                  className="h-10 w-10 object-contain flex-shrink-0"
                  style={{ borderRadius: 2 }}
                />
                <h1 className="font-display font-black text-hero text-text-primary leading-tight">
                  Sony Music Latin
                </h1>
              </div>
              <p className="text-text-secondary mt-2 max-w-xl leading-relaxed">
                Four AI agents transforming music industry signals into explainable
                commercial recommendations for brand partnerships.
              </p>
            </div>

            {/* Right — pipeline controls */}
            <div className="flex flex-col gap-3 md:min-w-[260px]">
              <div className="flex items-center gap-2">
                <StatusDot status={dotStatus} />
                <span className="label text-text-muted ml-1">
                  {pipeline.lastRun
                    ? `Last run: ${formatDate(pipeline.lastRun)}`
                    : summary?.run_timestamp
                      ? `Last run: ${formatDate(summary.run_timestamp)}`
                      : 'Pipeline not run yet'}
                </span>
              </div>

              <button
                className="btn-primary"
                onClick={pipeline.runPipeline}
                disabled={pipeline.isRunning}
                style={pipeline.isRunning ? { opacity: 0.6, cursor: 'not-allowed' } : undefined}
              >
                {pipeline.isRunning ? 'Running...' : 'Run Full Pipeline'}
              </button>

              {pipeline.isRunning && (
                <div>
                  <div className="w-full bg-bg-surface3 rounded-full h-1">
                    <div
                      className="h-1 rounded-full bg-brand-red transition-all duration-500"
                      style={{ width: `${pipeline.stageProgress}%` }}
                    />
                  </div>
                  <p className="text-text-muted text-xs mt-1.5">
                    {pipeline.currentStageLabel}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Section 2: Platform guide ─────────────────────────── */}
        <div>
          <SectionLabel>HOW TO USE THIS PLATFORM</SectionLabel>
          <h2 className="font-display font-bold text-title text-text-primary mt-1 mb-4">
            Commercial Signal Intelligence — User Guide
          </h2>

          <div className="card space-y-5" style={{ padding: '1.5rem' }}>
            <p className="text-text-secondary text-sm leading-relaxed max-w-4xl">
              The CSI platform transforms music industry signals into explainable commercial
              recommendations for brand partnership decisions. It runs four sequential AI agents,
              each building on the previous, to take you from raw chart data all the way to a
              fully modelled investment forecast — all without the LLM ever inventing a number.
              Every score and financial figure is calculated deterministically in Python first;
              the AI then interprets and narrates that evidence.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">

              {/* Step 1 */}
              <div className="flex gap-4 p-4 rounded-sm" style={{ backgroundColor: 'rgba(29,158,117,0.06)', border: '1px solid rgba(29,158,117,0.15)' }}>
                <div
                  className="flex-shrink-0 flex flex-col items-center justify-center font-display font-black text-white gap-0.5"
                  style={{ width: 32, height: 40, borderRadius: 2, backgroundColor: '#1D9E75', fontSize: 11, flexShrink: 0 }}
                >
                  <Icons.Radar size={13} />
                  <span>1</span>
                </div>
                <div>
                  <div className="font-display font-bold text-sm mb-1 flex items-center gap-1.5" style={{ color: '#1D9E75' }}>
                    <Icons.Radar size={13} />
                    AGENT 1 — Opportunity Discovery
                  </div>
                  <p className="text-text-secondary text-xs leading-relaxed">
                    Start here. Agent 1 ranks all 100 artists by momentum score and classifies
                    each as HIGH, MEDIUM, or WATCH opportunity. Use the Artist Leaderboard on
                    this page to spot the top performers at a glance, or go to the Agent 1 panel
                    for the full ranked table with territory fit, cross-platform scores, and
                    AI-generated opportunity narratives. Click any artist row to jump directly
                    into their brand strategy brief.
                  </p>
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex gap-4 p-4 rounded-sm" style={{ backgroundColor: 'rgba(139,127,232,0.06)', border: '1px solid rgba(139,127,232,0.15)' }}>
                <div
                  className="flex-shrink-0 flex flex-col items-center justify-center font-display font-black text-white gap-0.5"
                  style={{ width: 32, height: 40, borderRadius: 2, backgroundColor: '#8B7FE8', fontSize: 11, flexShrink: 0 }}
                >
                  <Icons.Lightbulb size={13} />
                  <span>2</span>
                </div>
                <div>
                  <div className="font-display font-bold text-sm mb-1 flex items-center gap-1.5" style={{ color: '#8B7FE8' }}>
                    <Icons.Lightbulb size={13} />
                    AGENT 2 — Strategy Synthesis
                  </div>
                  <p className="text-text-secondary text-xs leading-relaxed">
                    Determines the best brand category fit (Beverages, Fashion, Tech, Sport, or
                    Finance) for each artist using pre-computed audience fit scores and cultural
                    signal data. Each artist receives a strategic brief with three activation
                    pillars, a recommended channel, and a sentiment risk rating. Use the chat
                    interface on the left to ask follow-up questions about any artist's strategy —
                    the AI has full access to their data context.
                  </p>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex gap-4 p-4 rounded-sm" style={{ backgroundColor: 'rgba(74,158,232,0.06)', border: '1px solid rgba(74,158,232,0.15)' }}>
                <div
                  className="flex-shrink-0 flex flex-col items-center justify-center font-display font-black text-white gap-0.5"
                  style={{ width: 32, height: 40, borderRadius: 2, backgroundColor: '#4A9EE8', fontSize: 11, flexShrink: 0 }}
                >
                  <Icons.Users size={13} />
                  <span>3</span>
                </div>
                <div>
                  <div className="font-display font-bold text-sm mb-1 flex items-center gap-1.5" style={{ color: '#4A9EE8' }}>
                    <Icons.Users size={13} />
                    AGENT 3 — Audience-Fit
                  </div>
                  <p className="text-text-secondary text-xs leading-relaxed">
                    Profiles the fan audience for each artist across markets, showing estimated
                    reach, age/gender breakdowns, primary platform, and data confidence level.
                    Confidence is classified as HIGH (50%+ first-party data), MEDIUM, or LOW
                    (proxy-estimated only). LOW confidence artists are flagged automatically —
                    treat these as directional signals only and validate with first-party data
                    before committing campaign budget.
                  </p>
                </div>
              </div>

              {/* Step 4 */}
              <div className="flex gap-4 p-4 rounded-sm" style={{ backgroundColor: 'rgba(212,146,74,0.06)', border: '1px solid rgba(212,146,74,0.15)' }}>
                <div
                  className="flex-shrink-0 flex flex-col items-center justify-center font-display font-black text-white gap-0.5"
                  style={{ width: 32, height: 40, borderRadius: 2, backgroundColor: '#D4924A', fontSize: 11, flexShrink: 0 }}
                >
                  <Icons.TrendingUp size={13} />
                  <span>4</span>
                </div>
                <div>
                  <div className="font-display font-bold text-sm mb-1 flex items-center gap-1.5" style={{ color: '#D4924A' }}>
                    <Icons.TrendingUp size={13} />
                    AGENT 4 — ROI Forecast
                  </div>
                  <p className="text-text-secondary text-xs leading-relaxed">
                    Models three investment scenarios — Conservative (0.70× baseline),
                    Base (1.00×), and Optimistic (1.40×) — using historical campaign data
                    from similar brand categories. All revenue projections, conversion estimates,
                    and ROI multiples are calculated in Python before the AI is called. The
                    recommended scenario is determined by cross-platform score and data confidence.
                    Use the scenario chart to compare risk/return across all three cases.
                  </p>
                </div>
              </div>
            </div>

            <div
              className="flex items-start gap-3 mt-1 p-3 rounded-sm text-xs text-text-muted"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <span style={{ color: '#D4A017', flexShrink: 0 }}>▸</span>
              <span>
                <strong className="text-text-secondary">Workflow tip:</strong> Run the full
                pipeline from the button above whenever you want to refresh all four agents
                with the latest data. Use the workflow banner at the top to jump between
                agents. On Agent 2, 3, and 4 panels, click any artist row to pre-load that
                artist into the chat for instant contextual questions. Artist context carries
                over as you navigate between agents.
              </span>
            </div>
          </div>
        </div>

        {/* ── Section 3: Agent status cards ─────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.values(AGENTS).map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              count={agentCounts[agent.key]}
              onNavigate={navigate || (() => {})}
            />
          ))}
        </div>

        {/* ── Section 4: KPI summary ─────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            label="ARTISTS IN PIPELINE"
            value={summary?.artists_processed ?? 0}
            accentColor="#F0EEE8"
            watermarkChar="∑"
          />
          <KpiCard
            label="HIGH OPPORTUNITIES"
            value={summary?.agent1?.high_opportunities ?? 0}
            accentColor="#1D9E75"
          />
          <KpiCard
            label="AVG BASE ROI"
            value={summary?.agent4?.avg_base_roi
              ? `${Number(summary.agent4.avg_base_roi).toFixed(2)}×`
              : '—'}
            accentColor="#D4924A"
            watermarkChar="×"
          />
          <KpiCard
            label="HIGHEST ROI"
            value={summary?.agent4?.highest_roi_multiple
              ? `${Number(summary.agent4.highest_roi_multiple).toFixed(2)}×`
              : '—'}
            delta={summary?.agent4?.highest_roi_artist || undefined}
            deltaPositive={true}
            accentColor="#D4A017"
          />
        </div>

        {/* ── Section 4: Leaderboard ─────────────────────────────── */}
        <div>
          <div className="flex items-center justify-between mt-1 mb-4">
            <div>
              <SectionLabel>ARTIST RANKINGS — ALL OPPORTUNITIES</SectionLabel>
              <h2 className="font-display font-bold text-title text-text-primary mt-1">
                Artist Leaderboard
                {sortedArtists.length > 0 && (
                  <span className="font-mono text-sm text-text-muted font-normal ml-2">
                    ({sortedArtists.length} artists)
                  </span>
                )}
              </h2>
            </div>
            {sortedArtists.length > 0 && (
              <div className="flex items-center gap-3 text-xs text-text-muted">
                <span className="flex items-center gap-1.5">
                  <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: 1, backgroundColor: 'rgba(29,158,117,0.6)' }} />
                  HIGH
                </span>
                <span className="flex items-center gap-1.5">
                  <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: 1, backgroundColor: 'rgba(212,146,74,0.6)' }} />
                  MEDIUM
                </span>
                <span className="flex items-center gap-1.5">
                  <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: 1, backgroundColor: 'rgba(255,255,255,0.15)' }} />
                  WATCH
                </span>
                <span className="flex items-center gap-1.5 ml-1" style={{ borderLeft: '1px solid rgba(255,255,255,0.08)', paddingLeft: 10 }}>
                  <img src="/brand/sonymusiclatin_icon.jpeg" alt="" style={{ width: 12, height: 12, borderRadius: 1 }} />
                  Sony Music Latin
                </span>
              </div>
            )}
          </div>

          {sortedArtists.length === 0 ? (
            <div className="card text-center py-8 text-text-muted text-sm">
              No pipeline data yet. Run the pipeline to populate results.
            </div>
          ) : (
            <div className="card p-0 overflow-hidden">
              <div className="overflow-x-auto">
                <div style={{ maxHeight: 480, overflowY: 'auto' }}>
                  <table className="w-full text-xs" style={{ minWidth: 560 }}>
                    <thead style={{ position: 'sticky', top: 0, zIndex: 1, backgroundColor: '#0D0D18' }}>
                      <tr className="border-b border-white/[0.06]">
                        {['#', 'ARTIST', 'TERRITORY', 'MOMENTUM', 'OPPORTUNITY', 'BASE ROI', ''].map(h => (
                          <th key={h} className="px-3 py-2.5 text-left label">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sortedArtists.map((artist, i) => (
                        <LeaderboardRow
                          key={artist.artist_id}
                          rank={i + 1}
                          artist={artist}
                          roiData={agent4Data}
                          onNavigate={navigate || (() => {})}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── Section 5: Brand category signals ─────────────────── */}
        <BrandCategorySection agent2Data={agent2Data} agent1Data={agent1Data} />

        {/* ── Section 6: Footer ──────────────────────────────────── */}
        <div
          className="border-t border-white/[0.06] pt-6 pb-2"
        >
          <div className="text-text-muted text-sm">
            Chromadata Commercial Signal Intelligence (CSI) — Built for Sony Music Latin Region
          </div>
          <div className="text-text-muted text-xs mt-1">
            All scores calculated via Python/SQL. LLM interprets evidence only.
            Sample data — POC demonstration purposes.
          </div>
          <div className="text-text-muted text-xs mt-1">
            © 2026 Chromadata. Confidential.
          </div>
        </div>

      </div>
    </div>
  )
}