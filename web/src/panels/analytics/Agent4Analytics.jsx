import { useRef, useEffect } from 'react'
import { MessageSquare } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import PanelHeader from '@/components/agent1/PanelHeader'
import KpiCard from '@/components/shared/KpiCard'
import SectionLabel from '@/components/shared/SectionLabel'
import SkeletonPanel from '@/components/shared/SkeletonPanel'
import EmptyState from '@/components/shared/EmptyState'
import { AGENTS } from '@/lib/constants'
import { api } from '@/lib/api'

const AGENT_COLOR = '#D4924A'

function formatCurrency(n) {
  const num = Number(n)
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(2)}M`
  if (num >= 1_000)     return `$${(num / 1_000).toFixed(0)}K`
  return `$${num.toFixed(0)}`
}

function RiskBadge({ flag }) {
  if (!flag || flag === 'none' || flag === false) return null
  return <span className="badge badge-red">RISK FLAG</span>
}

function InvestmentCard({ artist, artistFocus, onAskAgent }) {
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
      className={`card group relative transition-all duration-200`}
      style={isHighlighted ? {
        borderColor: AGENT_COLOR,
        boxShadow: `0 0 0 1px ${AGENT_COLOR}40`,
      } : undefined}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="min-w-0">
          <div className="font-display font-bold text-text-primary">
            {artist.artist_name}
          </div>
          <div className="flex flex-wrap gap-1.5 mt-1 items-center">
            <span className="font-mono text-sm font-bold" style={{ color: AGENT_COLOR }}>
              {Number(artist.base_roi).toFixed(2)}× base ROI
            </span>
            <span className="badge badge-muted">{artist.brand_category}</span>
            <RiskBadge flag={artist.risk_flag} />
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span className="font-mono text-xs text-text-secondary">
            {formatCurrency(artist.base_revenue)}
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

      <p className="text-xs text-text-secondary leading-relaxed mb-2">
        {artist.investment_narrative}
      </p>

      <div className="space-y-0.5">
        {[artist.assumption_1, artist.assumption_2, artist.assumption_3]
          .filter(Boolean)
          .map((a, i) => (
            <div key={i} className="flex gap-1.5 text-[11px] text-text-muted">
              <span style={{ color: AGENT_COLOR }} className="flex-shrink-0">•</span>
              <span>{a}</span>
            </div>
          ))}
      </div>
    </div>
  )
}

function ScenarioCell({ value, isBase }) {
  return (
    <div
      className="text-center px-2 py-1.5 rounded-sm"
      style={isBase ? {
        background: '#D4924A15',
        border: '1px solid #D4924A40',
      } : {
        background: '#12121F',
      }}
    >
      <div className="font-mono text-sm font-bold" style={{ color: isBase ? AGENT_COLOR : '#8A8A9A' }}>
        {Number(value).toFixed(2)}×
      </div>
    </div>
  )
}

export default function Agent4Analytics({ data, isLoading, artistFocus, onAskAgent }) {
  const agent = AGENTS[4]

  const { data: scenarios } = useQuery({
    queryKey: ['roi_scenarios'],
    queryFn: api.getRoiScenarios,
    staleTime: 60000,
  })

  if (isLoading) return <SkeletonPanel />
  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No ROI forecast data"
        message="Run the pipeline to generate Agent 4 results"
      />
    )
  }

  const avgBaseRoi = (data.reduce((s, d) => s + Number(d.base_roi || 0), 0) / data.length).toFixed(2)
  const topArtist = [...data].sort((a, b) => Number(b.base_roi) - Number(a.base_roi))[0]
  const totalRevenue = data.reduce((s, d) => s + Number(d.base_revenue || 0), 0)
  const riskCount = data.filter(d => d.risk_flag && d.risk_flag !== 'none').length

  // Scenario chart data — all three ROI lines per artist
  const chartData = data.map(d => ({
    name: d.artist_name.split(' ').slice(-1)[0], // Last name for compact label
    conservative: Number(d.conservative_roi).toFixed(2),
    base:         Number(d.base_roi).toFixed(2),
    optimistic:   Number(d.optimistic_roi).toFixed(2),
  }))

  return (
    <div className="flex flex-col overflow-hidden">
      <PanelHeader
        agent={agent}
        description="Investment scenarios, projected ROI, and financial risk assessment"
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 flex-shrink-0">
        <KpiCard
          label="AVG BASE ROI"
          value={`${avgBaseRoi}×`}
          accentColor={AGENT_COLOR}
          watermarkChar="×"
        />
        <KpiCard
          label="HIGHEST ROI ARTIST"
          value={topArtist?.artist_name?.split(' ')[0] || '—'}
          accentColor={AGENT_COLOR}
        />
        <KpiCard
          label="TOTAL PROJECTED REVENUE"
          value={formatCurrency(totalRevenue)}
          accentColor={AGENT_COLOR}
        />
        <KpiCard
          label="RISK FLAGS"
          value={riskCount}
          accentColor={riskCount > 0 ? '#CC1B1B' : '#1D9E75'}
        />
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-4">
        {/* Scenario comparison chart */}
        <div className="card">
          <SectionLabel>ROI SCENARIO FORECAST — CONSERVATIVE / BASE / OPTIMISTIC</SectionLabel>
          <div style={{ height: 220, marginTop: 12 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: -8 }}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.04)" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#8A8A9A', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#8A8A9A', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={v => `${v}×`}
                />
                <Tooltip
                  contentStyle={{
                    background: '#12121F',
                    border: '1px solid rgba(255,255,255,0.10)',
                    borderRadius: 2,
                    color: '#F0EEE8',
                    fontSize: 11,
                  }}
                  formatter={(v, name) => [`${v}×`, name]}
                />
                <Legend
                  wrapperStyle={{ fontSize: 10, color: '#8A8A9A', paddingTop: 4 }}
                  iconType="line"
                />
                <Line
                  type="monotone"
                  dataKey="conservative"
                  stroke="#4A9EE8"
                  strokeWidth={1.5}
                  dot={false}
                  strokeDasharray="4 2"
                />
                <Line
                  type="monotone"
                  dataKey="base"
                  stroke={AGENT_COLOR}
                  strokeWidth={2}
                  dot={{ r: 3, fill: AGENT_COLOR }}
                />
                <Line
                  type="monotone"
                  dataKey="optimistic"
                  stroke="#1D9E75"
                  strokeWidth={1.5}
                  dot={false}
                  strokeDasharray="2 2"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Scenario table */}
        {scenarios && scenarios.length > 0 && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-white/[0.06]">
              <SectionLabel>SCENARIO COMPARISON</SectionLabel>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs" style={{ minWidth: 560 }}>
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="px-3 py-2 text-left label">ARTIST</th>
                    <th className="px-3 py-2 text-center label">CONSERVATIVE</th>
                    <th className="px-3 py-2 text-center label" style={{ color: AGENT_COLOR }}>BASE ▲</th>
                    <th className="px-3 py-2 text-center label">OPTIMISTIC</th>
                    <th className="px-3 py-2 text-left label">RECOMMENDED</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map(artist => (
                    <tr key={artist.artist_id} className="border-b border-white/[0.04]">
                      <td className="px-3 py-2 font-display font-bold text-text-primary whitespace-nowrap">
                        {artist.artist_name}
                      </td>
                      <td className="px-3 py-1.5">
                        <ScenarioCell value={artist.conservative_roi} isBase={false} />
                      </td>
                      <td className="px-3 py-1.5">
                        <ScenarioCell value={artist.base_roi} isBase={true} />
                      </td>
                      <td className="px-3 py-1.5">
                        <ScenarioCell value={artist.optimistic_roi} isBase={false} />
                      </td>
                      <td className="px-3 py-2">
                        <span className="badge badge-amber uppercase">{artist.recommended_scenario}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Investment recommendation cards */}
        <div>
          <SectionLabel>TOP INVESTMENT RECOMMENDATIONS</SectionLabel>
          <div className="mt-2 space-y-3">
            {[...data]
              .sort((a, b) => Number(b.base_roi) - Number(a.base_roi))
              .slice(0, 3)
              .map(artist => (
                <InvestmentCard
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
