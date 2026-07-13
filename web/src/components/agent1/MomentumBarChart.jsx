import {
  BarChart, Bar, XAxis, YAxis, Cell, LabelList,
  ResponsiveContainer, Tooltip,
} from 'recharts'
import SectionLabel from '@/components/shared/SectionLabel'

function barColor(score) {
  if (score > 80) return '#1D9E75'
  if (score > 65) return '#D4924A'
  return '#CC1B1B'
}

export default function MomentumBarChart({ data }) {
  const top8 = [...data]
    .sort((a, b) => b.momentum_score - a.momentum_score)
    .slice(0, 8)
    .map(d => ({
      name: d.artist_name,
      score: Math.round(Number(d.momentum_score) * 10) / 10,
    }))

  return (
    <div className="card flex flex-col gap-3">
      <SectionLabel>TOP ARTISTS — MOMENTUM SCORE</SectionLabel>
      <div style={{ height: 280, backgroundColor: 'var(--bg-surface)', borderRadius: 2, padding: '8px 0' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={top8}
            layout="vertical"
            margin={{ top: 4, right: 52, bottom: 4, left: 4 }}
          >
            <XAxis
              type="number"
              domain={[0, dataMax => Math.ceil(dataMax * 1.15)]}
              tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={96}
              tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: 'var(--border-color)' }}
              contentStyle={{
                background: 'var(--bg-surface2)',
                border: '1px solid var(--border-hover)',
                borderRadius: 2,
                color: 'var(--text-primary)',
                fontSize: 12,
                fontFamily: 'DM Sans, sans-serif',
              }}
              formatter={val => [val, 'Momentum']}
            />
            <Bar dataKey="score" maxBarSize={14} radius={[0, 1, 1, 0]}>
              {top8.map((entry, i) => (
                <Cell key={i} fill={barColor(entry.score)} />
              ))}
              <LabelList
                dataKey="score"
                position="right"
                style={{
                  fill: 'var(--text-secondary)',
                  fontSize: 10,
                  fontFamily: 'JetBrains Mono, monospace',
                }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
