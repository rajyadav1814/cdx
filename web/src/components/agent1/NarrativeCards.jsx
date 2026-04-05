import { useContext } from 'react'
import { NavigationContext } from '@/components/layout/AppShell'
import SectionLabel from '@/components/shared/SectionLabel'

const AGENT_COLOR = '#1D9E75'

function opportunityClass(cls) {
  if (cls === 'HIGH')   return 'badge badge-green'
  if (cls === 'MEDIUM') return 'badge badge-amber'
  return 'badge badge-muted'
}

export default function NarrativeCards({ data }) {
  const navigate = useContext(NavigationContext)
  const top3 = data.slice(0, 3)

  return (
    <div className="flex flex-col gap-3">
      <SectionLabel>TOP 3 NARRATIVES</SectionLabel>
      {top3.map(artist => (
        <div
          key={artist.artist_id}
          className="card"
          style={{ borderLeft: `2px solid ${AGENT_COLOR}` }}
        >
          <div className="flex items-start justify-between gap-3 mb-2">
            <div className="min-w-0">
              <div className="font-display font-bold text-text-primary text-sm leading-tight truncate">
                {artist.artist_name}
              </div>
              <div className="text-xs text-text-muted mt-0.5">
                {artist.top_territory_1}
                {artist.top_territory_2 ? ` · ${artist.top_territory_2}` : ''}
              </div>
            </div>
            <div className="flex flex-col items-end gap-1 flex-shrink-0">
              <span
                className="font-mono font-bold text-base leading-none"
                style={{ color: AGENT_COLOR }}
              >
                {Number(artist.momentum_score).toFixed(1)}
              </span>
              <span className={opportunityClass(artist.opportunity_class)}>
                {artist.opportunity_class}
              </span>
            </div>
          </div>

          <p className="text-xs text-text-secondary leading-relaxed">
            {artist.narrative}
          </p>

          {navigate && (
            <button
              className="mt-3 text-xs font-medium transition-opacity hover:opacity-70 bg-transparent border-0 p-0 cursor-pointer"
              style={{ color: AGENT_COLOR, fontFamily: 'inherit' }}
              onClick={() => navigate('agent2')}
            >
              View strategy →
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
