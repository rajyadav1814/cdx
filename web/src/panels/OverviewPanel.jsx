import { useContext } from 'react'
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

const BRAND_BARS = [
  { key: 'Beverage', label: 'BEVERAGE',  color: '#1D9E75' },
  { key: 'Fashion',  label: 'FASHION',   color: '#8B7FE8' },
  { key: 'Tech',     label: 'TECH',      color: '#4A9EE8' },
  { key: 'Sport',    label: 'SPORT',     color: '#D4924A' },
  { key: 'Finance',  label: 'FINANCE',   color: '#D4A017' },
]

// ─── sub-components ───────────────────────────────────────────────────────────

function AgentCard({ agent, count, onNavigate }) {
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
          className="font-display font-bold text-text-primary leading-tight"
          style={{ fontSize: 13 }}
        >
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

function LeaderboardRow({ rank, artist, roiData, onNavigate }) {
  const roi = roiData?.find(
    r => r.artist_id === artist.artist_id || r.artist_name === artist.artist_name
  )

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
      onClick={handleClick}
    >
      <td className="px-4 py-3 font-mono text-xs text-text-muted w-8">{rank}</td>
      <td className="px-4 py-3">
        <div className="font-display font-bold text-sm text-text-primary">
          {artist.artist_name}
        </div>
      </td>
      <td className="px-4 py-3 text-xs text-text-secondary">
        {artist.top_territory_1}
        {artist.top_territory_2 ? ` · ${artist.top_territory_2}` : ''}
      </td>
      <td className="px-4 py-3">
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
      <td className="px-4 py-3">
        <span className={opportunityBadgeClass}>{artist.opportunity_class}</span>
      </td>
      <td className="px-4 py-3 font-mono text-xs" style={{ color: '#D4924A' }}>
        {roi ? `${Number(roi.base_roi).toFixed(2)}×` : '—'}
      </td>
      <td className="px-4 py-3">
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

function BrandCategoryBar({ bar, agent2Data }) {
  if (!agent2Data || agent2Data.length === 0) {
    return (
      <div className="flex items-center gap-3">
        <span className="label w-20 flex-shrink-0" style={{ color: bar.color }}>{bar.label}</span>
        <div className="flex-1 h-1.5 bg-bg-surface3 rounded-full" />
        <span className="text-xs text-text-muted w-20 text-right">No data</span>
      </div>
    )
  }

  const total = agent2Data.length
  const highFit = agent2Data.filter(
    d => d.best_brand_category === bar.key && Number(d.brand_fit_score) > 80
  ).length
  const pct = total > 0 ? (highFit / total) * 100 : 0

  return (
    <div className="flex items-center gap-3">
      <span className="label w-20 flex-shrink-0" style={{ color: bar.color }}>{bar.label}</span>
      <div className="flex-1 h-1.5 bg-bg-surface3 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: bar.color }}
        />
      </div>
      <span className="text-xs text-text-muted w-20 text-right">
        {highFit} of {total} HIGH fit
      </span>
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

  // Top 5 artists by momentum
  const top5 = agent1Data
    ? [...agent1Data].sort((a, b) => Number(b.momentum_score) - Number(a.momentum_score)).slice(0, 5)
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
              <SectionLabel>COMMERCIAL SIGNAL INTELLIGENCE ENGINE (CSIE)</SectionLabel>
              <h1 className="font-display font-black text-hero text-text-primary mt-2 leading-tight">
                Sony Music Latin
              </h1>
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

        {/* ── Section 2: Agent status cards ─────────────────────── */}
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

        {/* ── Section 3: KPI summary ─────────────────────────────── */}
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
          <SectionLabel>TOP OPPORTUNITIES THIS WEEK</SectionLabel>
          <h2 className="font-display font-bold text-title text-text-primary mt-1 mb-4">
            Artist Leaderboard
          </h2>

          {top5.length === 0 ? (
            <div
              className="card text-center py-8 text-text-muted text-sm"
            >
              No pipeline data yet. Run the pipeline to populate results.
            </div>
          ) : (
            <div className="card p-0 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs" style={{ minWidth: 560 }}>
                  <thead>
                    <tr className="border-b border-white/[0.06]">
                      {['#', 'ARTIST', 'TERRITORY', 'MOMENTUM', 'OPPORTUNITY', 'BASE ROI', ''].map(h => (
                        <th key={h} className="px-4 py-2.5 text-left label">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {top5.map((artist, i) => (
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
          )}
        </div>

        {/* ── Section 5: Brand category signals ─────────────────── */}
        <div>
          <SectionLabel>BRAND CATEGORY SIGNALS</SectionLabel>
          <div className="card mt-2 space-y-3">
            {BRAND_BARS.map(bar => (
              <BrandCategoryBar key={bar.key} bar={bar} agent2Data={agent2Data} />
            ))}
          </div>
        </div>

        {/* ── Section 6: Footer ──────────────────────────────────── */}
        <div
          className="border-t border-white/[0.06] pt-6 pb-2"
        >
          <div className="text-text-muted text-sm">
            Chromadata Commercial Signal Intelligence Engine (CSIE) — Built for Sony Music Latin Region
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
