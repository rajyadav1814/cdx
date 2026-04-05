import { cn } from '@/lib/utils'
import SectionLabel from './SectionLabel'
import { Skeleton } from '@/components/ui/skeleton'

export default function KpiCard({
  label,
  value,
  delta,
  deltaPositive,
  accentColor = '#CC1B1B',
  loading = false,
  watermarkChar,
  className = '',
}) {
  return (
    <div
      className={cn('card relative overflow-hidden', className)}
      style={{ borderLeft: `2px solid ${accentColor}` }}
    >
      {watermarkChar && (
        <span
          className="watermark-num"
          style={{ bottom: -16, right: 8, color: accentColor }}
        >
          {watermarkChar}
        </span>
      )}

      <SectionLabel>{label}</SectionLabel>

      <div className="mt-2">
        {loading ? (
          <Skeleton className="h-9 w-24 bg-bg-surface3" />
        ) : (
          <div className="kpi-value">{value}</div>
        )}
      </div>

      {delta !== undefined && !loading && (
        <div
          className="mt-1 text-xs font-mono"
          style={{ color: deltaPositive ? '#1D9E75' : '#CC1B1B' }}
        >
          {deltaPositive ? '▲' : '▼'} {delta}
        </div>
      )}
    </div>
  )
}
