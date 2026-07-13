import { useRef, useEffect } from 'react'
import { MessageSquare } from 'lucide-react'
import PanelHeader from '@/components/agent1/PanelHeader'
import KpiCard from '@/components/shared/KpiCard'
import SectionLabel from '@/components/shared/SectionLabel'
import SkeletonPanel from '@/components/shared/SkeletonPanel'
import EmptyState from '@/components/shared/EmptyState'
import { AGENTS } from '@/lib/constants'

const BRAND_CATEGORIES = ['Tech', 'Fashion', 'Beverage', 'Travel', 'Beauty']
const AGENT_COLOR = '#8B7FE8'

function matrixCellStyle(score, isActive) {
  if (!isActive) return { background: 'var(--bg-surface2)', color: 'var(--text-muted)' }
  if (score >= 85) return { background: '#1D9E7520', color: '#1D9E75', border: '1px solid #1D9E7540' }
  if (score >= 70) return { background: '#4A9EE820', color: '#4A9EE8', border: '1px solid #4A9EE840' }
  if (score >= 55) return { background: '#D4924A20', color: '#D4924A', border: '1px solid #D4924A40' }
  return { background: '#CC1B1B15', color: '#CC1B1B', border: '1px solid #CC1B1B30' }
}

function SentimentBadge({ risk }) {
  if (risk === 'none')   return <span className="badge badge-green">None</span>
  if (risk === 'low')    return <span className="badge badge-amber">Low</span>
  if (risk === 'medium') return <span className="badge badge-amber">Medium</span>
  return <span className="badge badge-red">{risk}</span>
}

function CategoryBadge({ category }) {
  return (
    <span className="badge" style={{ backgroundColor: `${AGENT_COLOR}15`, color: AGENT_COLOR }}>
      {category}
    </span>
  )
}

function BriefCard({ artist, artistFocus, onAskAgent }) {
  const ref = useRef(null)
  const isHighlighted = artistFocus === artist.artist_name

  useEffect(() => {
    if (isHighlighted && ref.current) {
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [isHighlighted])

  return (
    <div
      ref={ref}
      className={`card group relative transition-all duration-200
        ${isHighlighted ? 'ring-1' : ''}`}
      style={isHighlighted ? { ringColor: AGENT_COLOR, borderColor: AGENT_COLOR,
        boxShadow: `0 0 0 1px ${AGENT_COLOR}40` } : undefined}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="min-w-0">
          <div className="font-display font-bold text-text-primary">
            {artist.artist_name}
          </div>
          <div className="flex flex-wrap gap-1.5 mt-1">
            <CategoryBadge category={artist.best_brand_category} />
            <span className="badge badge-muted">{artist.recommended_channel}</span>
            <SentimentBadge risk={artist.sentiment_risk} />
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="font-mono font-bold text-lg" style={{ color: AGENT_COLOR }}>
            {Number(artist.brand_fit_score).toFixed(0)}
          </span>
          {onAskAgent && (
            <button
              className="btn-icon opacity-0 group-hover:opacity-100 transition-opacity duration-150"
              title={`Ask agent about ${artist.artist_name}`}
              onClick={() => onAskAgent(artist.artist_name)}
            >
              <MessageSquare size={13} />
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-2">
        {[artist.activation_pillar_1, artist.activation_pillar_2, artist.activation_pillar_3]
          .filter(Boolean)
          .map((p, i) => (
            <span key={i} className="badge badge-muted text-text-secondary">{p}</span>
          ))}
      </div>

      <p className="text-xs text-text-secondary leading-relaxed">
        {artist.strategic_brief}
      </p>
    </div>
  )
}

function MatrixRow({ artist, artistFocus }) {
  const ref = useRef(null)
  const isHighlighted = artistFocus === artist.artist_name

  useEffect(() => {
    if (isHighlighted && ref.current) {
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [isHighlighted])

  return (
    <tr
      ref={ref}
      className={`border-b border-white/[0.04] transition-colors ${isHighlighted ? 'ring-1' : ''}`}
      style={{ backgroundColor: isHighlighted ? `${AGENT_COLOR}10` : undefined }}
    >
      <td
        className="px-3 py-2 font-display font-bold text-text-primary whitespace-nowrap"
        style={isHighlighted ? { boxShadow: `inset 2px 0 0 ${AGENT_COLOR}` } : undefined}
      >
        {artist.artist_name}
      </td>
      {BRAND_CATEGORIES.map(cat => {
        const isActive = artist.best_brand_category === cat
        const score = isActive ? Number(artist.brand_fit_score) : 0
        const style = matrixCellStyle(score, isActive)
        return (
          <td key={cat} className="px-2 py-2 text-center">
            <span
              className="inline-flex items-center justify-center w-14 h-6 rounded-sm text-[11px] font-mono font-bold"
              style={style}
            >
              {isActive ? score.toFixed(0) : '—'}
            </span>
          </td>
        )
      })}
    </tr>
  )
}

export default function Agent2Analytics({ data, isLoading, artistFocus, onAskAgent }) {
  const agent = AGENTS[2]

  if (isLoading) return <SkeletonPanel />
  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No strategy data"
        message="Run the pipeline to generate Agent 2 results"
      />
    )
  }

  const avgFitScore = (data.reduce((s, d) => s + Number(d.brand_fit_score), 0) / data.length).toFixed(1)
  const categoryCounts = {}
  data.forEach(d => {
    categoryCounts[d.best_brand_category] = (categoryCounts[d.best_brand_category] || 0) + 1
  })
  const topCategory = Object.entries(categoryCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '—'
  const noRiskCount = data.filter(d => d.sentiment_risk === 'none').length

  return (
    <div className="flex flex-col overflow-hidden">
      <PanelHeader
        agent={agent}
        description="Brand-artist fit scores, activation strategies, and cultural briefs"
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 flex-shrink-0">
        <KpiCard label="BRIEFS GENERATED"    value={data.length}  accentColor={AGENT_COLOR} />
        <KpiCard label="AVG BRAND FIT SCORE" value={avgFitScore}  accentColor={AGENT_COLOR} watermarkChar="%" />
        <KpiCard label="TOP BRAND CATEGORY"  value={topCategory}  accentColor={AGENT_COLOR} />
        <KpiCard label="NO SENTIMENT RISK"   value={noRiskCount}  accentColor="#1D9E75" />
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-4">
        {/* Brand-artist fit matrix */}
        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-white/[0.06]">
            <SectionLabel>BRAND-ARTIST FIT MATRIX</SectionLabel>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs" style={{ minWidth: 560 }}>
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="px-3 py-2 text-left label">ARTIST</th>
                  {BRAND_CATEGORIES.map(cat => (
                    <th key={cat} className="px-2 py-2 text-center label w-20">{cat.toUpperCase()}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map(artist => (
                  <MatrixRow key={artist.artist_id} artist={artist} artistFocus={artistFocus} />
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Strategy brief cards */}
        <div>
          <SectionLabel>STRATEGY BRIEFS</SectionLabel>
          <div className="mt-2 space-y-3">
            {data.map(artist => (
              <BriefCard
                key={artist.artist_id}
                artist={artist}
                artistFocus={artistFocus}
                onAskAgent={onAskAgent}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
