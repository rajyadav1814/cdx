import { useRef, useEffect } from 'react'
import { MessageSquare, AlertTriangle } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import PanelHeader from '@/components/agent1/PanelHeader'
import KpiCard from '@/components/shared/KpiCard'
import SectionLabel from '@/components/shared/SectionLabel'
import SkeletonPanel from '@/components/shared/SkeletonPanel'
import EmptyState from '@/components/shared/EmptyState'
import { AGENTS } from '@/lib/constants'

const AGENT_COLOR = '#4A9EE8'

function ConfidenceBadge({ level }) {
  if (level === 'HIGH')   return <span className="badge badge-green">HIGH</span>
  if (level === 'MEDIUM') return <span className="badge badge-amber">MEDIUM</span>
  return <span className="badge badge-red">LOW</span>
}

function formatReach(n) {
  const num = Number(n)
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`
  if (num >= 1_000)     return `${(num / 1_000).toFixed(0)}K`
  return String(num)
}

function AudienceRow({ artist, artistFocus, onAskAgent }) {
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
      className="group border-b border-white/[0.04] transition-colors"
      style={{
        backgroundColor: isHighlighted ? `${AGENT_COLOR}10` : undefined,
        boxShadow: isHighlighted ? `inset 2px 0 0 ${AGENT_COLOR}` : undefined,
      }}
    >
      <td className="px-3 py-2 font-display font-bold text-text-primary whitespace-nowrap">
        {artist.artist_name}
      </td>
      <td className="px-3 py-2 text-text-secondary">{artist.primary_market || '—'}</td>
      <td className="px-3 py-2 text-text-muted">{artist.secondary_market || '—'}</td>
      <td className="px-3 py-2 font-mono text-text-secondary">
        {formatReach(artist.total_reach)}
      </td>
      <td className="px-3 py-2 text-text-muted">{artist.primary_platform || '—'}</td>
      <td className="px-3 py-2 font-mono" style={{ color: AGENT_COLOR }}>
        {Number(artist.audience_fit_score).toFixed(0)}
      </td>
      <td className="px-3 py-2">
        <ConfidenceBadge level={artist.data_confidence} />
      </td>
      <td className="px-3 py-2 font-mono text-text-muted">
        {Number(artist.proxy_pct).toFixed(0)}%
      </td>
      <td className="px-3 py-2">
        {onAskAgent && (
          <button
            className="btn-icon w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
            title={`Ask agent about ${artist.artist_name}`}
            onClick={() => onAskAgent(artist.artist_name)}
          >
            <MessageSquare size={11} />
          </button>
        )}
      </td>
    </tr>
  )
}

export default function Agent3Analytics({ data, isLoading, artistFocus, onAskAgent }) {
  const agent = AGENTS[3]

  if (isLoading) return <SkeletonPanel />
  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No audience data"
        message="Run the pipeline to generate Agent 3 results"
      />
    )
  }

  const totalReach = data.reduce((s, d) => s + Number(d.total_reach || 0), 0)
  const avgFitScore = (data.reduce((s, d) => s + Number(d.audience_fit_score || 0), 0) / data.length).toFixed(1)
  const highConfCount = data.filter(d => d.data_confidence === 'HIGH').length
  const avgProxyPct = (data.reduce((s, d) => s + Number(d.proxy_pct || 0), 0) / data.length).toFixed(1)

  const marketCounts = {}
  data.forEach(d => {
    if (d.primary_market) marketCounts[d.primary_market] = (marketCounts[d.primary_market] || 0) + 1
  })
  const primaryMarket = Object.entries(marketCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '—'

  const marketReach = {}
  data.forEach(d => {
    const mkt = d.primary_market || 'Other'
    marketReach[mkt] = (marketReach[mkt] || 0) + Number(d.total_reach || 0)
  })
  const marketChartData = Object.entries(marketReach)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([market, reach]) => ({ market, reach }))

  const showProxyWarning = Number(avgProxyPct) > 30

  return (
    <div className="flex flex-col overflow-hidden">
      <PanelHeader
        agent={agent}
        description="Audience demographics, reach, platform affinity, and data confidence scores"
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 flex-shrink-0">
        <KpiCard label="TOTAL REACH"      value={formatReach(totalReach)} accentColor={AGENT_COLOR} watermarkChar="◎" />
        <KpiCard label="PRIMARY MARKET"   value={primaryMarket}           accentColor={AGENT_COLOR} />
        <KpiCard label="AVG AUDIENCE FIT" value={avgFitScore}             accentColor={AGENT_COLOR} />
        <KpiCard label="HIGH CONFIDENCE"  value={highConfCount}           accentColor="#1D9E75" />
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-4">
        {showProxyWarning && (
          <div
            className="flex items-center gap-3 px-4 py-3 rounded-sm border"
            style={{ backgroundColor: '#D4924A10', borderColor: '#D4924A40' }}
          >
            <AlertTriangle size={14} className="flex-shrink-0" style={{ color: '#D4924A' }} />
            <span className="text-xs" style={{ color: '#D4924A' }}>
              <strong>{avgProxyPct}%</strong> of audience data is proxy-estimated. Treat reach figures as approximations, not confirmed measurements.
            </span>
          </div>
        )}

        {/* Market reach chart */}
        <div className="card">
          <SectionLabel>MARKET REACH DISTRIBUTION</SectionLabel>
          <div style={{ height: 200, marginTop: 12 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={marketChartData}
                layout="vertical"
                margin={{ top: 0, right: 48, bottom: 0, left: 0 }}
              >
                <XAxis
                  type="number"
                  tickFormatter={v => formatReach(v)}
                  tick={{ fill: '#8A8A9A', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="market"
                  width={36}
                  tick={{ fill: '#8A8A9A', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                  contentStyle={{
                    background: '#12121F',
                    border: '1px solid rgba(255,255,255,0.10)',
                    borderRadius: 2,
                    color: '#F0EEE8',
                    fontSize: 12,
                  }}
                  formatter={v => [formatReach(v), 'Reach']}
                />
                <Bar dataKey="reach" maxBarSize={12} radius={[0, 1, 1, 0]}>
                  {marketChartData.map((_, i) => (
                    <Cell key={i} fill={AGENT_COLOR} fillOpacity={1 - i * 0.08} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Audience table */}
        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-white/[0.06]">
            <SectionLabel>AUDIENCE PROFILES</SectionLabel>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs" style={{ minWidth: 680 }}>
              <thead>
                <tr className="border-b border-white/[0.06]">
                  {['ARTIST', 'PRIMARY MKT', 'SECONDARY', 'TOTAL REACH', 'PLATFORM', 'FIT SCORE', 'CONFIDENCE', 'PROXY %', ''].map(h => (
                    <th key={h} className="px-3 py-2 text-left label">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map(artist => (
                  <AudienceRow
                    key={artist.artist_id}
                    artist={artist}
                    artistFocus={artistFocus}
                    onAskAgent={onAskAgent}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
