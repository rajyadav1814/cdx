import {
  PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer,
} from 'recharts'
import SectionLabel from '@/components/shared/SectionLabel'

const PALETTE = [
  '#1D9E75', '#8B7FE8', '#4A9EE8', '#D4924A',
  '#D4A017', '#CC1B1B', '#6B9E6B', '#9E7F1D',
]

const TERRITORY_LABELS = {
  MX: 'Mexico', CO: 'Colombia', AR: 'Argentina',
  ES: 'Spain',  CL: 'Chile',   VE: 'Venezuela',
  BR: 'Brazil', PE: 'Peru',    US: 'United States',
}

export default function TerritoryChart({ data }) {
  const counts = {}
  data
    .filter(d => d.opportunity_class === 'HIGH' || d.opportunity_class === 'MEDIUM')
    .forEach(d => {
      const key = d.top_territory_1 || 'Other'
      counts[key] = (counts[key] || 0) + 1
    })

  const chartData = Object.entries(counts)
    .map(([key, value]) => ({ name: TERRITORY_LABELS[key] || key, value }))
    .sort((a, b) => b.value - a.value)

  return (
    <div className="card flex flex-col gap-3">
      <SectionLabel>TERRITORY DISTRIBUTION</SectionLabel>
      <div style={{ height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="42%"
              innerRadius="50%"
              outerRadius="70%"
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: 'var(--bg-surface2)',
                border: '1px solid var(--border-hover)',
                borderRadius: 2,
                color: 'var(--text-primary)',
                fontSize: 12,
                fontFamily: 'DM Sans, sans-serif',
              }}
              formatter={(val, name) => [val, name]}
            />
            <Legend
              iconType="circle"
              iconSize={6}
              wrapperStyle={{
                fontSize: 11,
                color: '#8A8A9A',
                paddingTop: 8,
                fontFamily: 'DM Sans, sans-serif',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
