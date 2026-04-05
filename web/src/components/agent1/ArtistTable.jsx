import { useState } from 'react'
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '@/components/ui/collapsible'
import SectionLabel from '@/components/shared/SectionLabel'
import { ChevronDown } from 'lucide-react'

function scoreBarColor(score) {
  if (score > 80) return '#1D9E75'
  if (score > 65) return '#D4924A'
  return '#CC1B1B'
}

function OpportunityBadge({ cls }) {
  const map = {
    HIGH:   'badge badge-green',
    MEDIUM: 'badge badge-amber',
    WATCH:  'badge badge-muted',
    LOW:    'badge badge-muted',
  }
  return <span className={map[cls] || 'badge badge-muted'}>{cls}</span>
}

function ScoreBar({ score, maxScore }) {
  const width = maxScore > 0 ? (score / maxScore) * 100 : score
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-bg-surface3 rounded-sm overflow-hidden">
        <div
          style={{
            width: `${Math.min(width, 100)}%`,
            height: 4,
            borderRadius: 1,
            backgroundColor: scoreBarColor(score),
          }}
        />
      </div>
      <span className="font-mono text-xs text-text-secondary w-8 text-right flex-shrink-0">
        {Number(score).toFixed(1)}
      </span>
    </div>
  )
}

const COLS = 'grid-cols-[2rem_1fr_3.5rem_9rem_9rem_4rem_7rem_3.5rem_1.5rem]'

export default function ArtistTable({ data }) {
  const [openRows, setOpenRows] = useState({})

  const maxMomentum = Math.max(...data.map(d => Number(d.momentum_score)))

  const toggleRow = (id, open) =>
    setOpenRows(prev => ({ ...prev, [id]: open }))

  return (
    <div className="card p-0 overflow-hidden">
      <div className="px-4 py-3 border-b border-white/[0.06]">
        <SectionLabel>ALL ARTISTS — DISCOVERY TABLE</SectionLabel>
      </div>

      <div className="overflow-x-auto">
        {/* sticky header */}
        <div
          className={`grid ${COLS} gap-x-3 px-4 py-2 sticky top-0 z-10 bg-bg-surface border-b border-white/[0.06]`}
          style={{ minWidth: 720 }}
        >
          {['#', 'ARTIST', 'TERR', 'MOMENTUM', 'CROSS-PLAT', 'RISK', 'OPPORTUNITY', 'TERR 2', ''].map(h => (
            <span key={h} className="label text-text-muted text-[10px]">{h}</span>
          ))}
        </div>

        {/* rows */}
        <div style={{ minWidth: 720 }}>
          {data.map(artist => {
            const id = artist.artist_id
            const isOpen = !!openRows[id]
            return (
              <Collapsible
                key={id}
                open={isOpen}
                onOpenChange={open => toggleRow(id, open)}
              >
                <CollapsibleTrigger
                  className="block w-full text-left focus:outline-none focus-visible:bg-bg-surface2"
                  style={{
                    appearance: 'none',
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                  }}
                >
                  <div
                    className={`grid ${COLS} gap-x-3 px-4 py-2.5 border-b border-white/[0.04] transition-colors duration-100`}
                    style={{ backgroundColor: isOpen ? '#12121F' : undefined }}
                    onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#12121F' }}
                    onMouseLeave={e => { e.currentTarget.style.backgroundColor = isOpen ? '#12121F' : '' }}
                  >
                    {/* rank */}
                    <span className="font-mono text-xs text-text-muted self-center">
                      {artist.rank}
                    </span>
                    {/* artist name */}
                    <span className="font-display font-bold text-sm text-text-primary self-center truncate">
                      {artist.artist_name}
                    </span>
                    {/* territory 1 */}
                    <span className="text-xs text-text-secondary self-center">
                      {artist.top_territory_1}
                    </span>
                    {/* momentum */}
                    <div className="self-center">
                      <ScoreBar score={Number(artist.momentum_score)} maxScore={maxMomentum} />
                    </div>
                    {/* cross-platform */}
                    <div className="self-center">
                      <ScoreBar score={Number(artist.cross_platform_score)} maxScore={100} />
                    </div>
                    {/* risk */}
                    <span className="font-mono text-xs text-text-secondary self-center">
                      {Number(artist.risk_flag_score).toFixed(1)}
                    </span>
                    {/* opportunity */}
                    <div className="self-center">
                      <OpportunityBadge cls={artist.opportunity_class} />
                    </div>
                    {/* territory 2 */}
                    <span className="text-xs text-text-muted self-center">
                      {artist.top_territory_2 || '—'}
                    </span>
                    {/* chevron */}
                    <div className="self-center flex justify-center">
                      <ChevronDown
                        size={12}
                        className="text-text-muted"
                        style={{
                          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                          transition: 'transform 0.15s ease',
                        }}
                      />
                    </div>
                  </div>
                </CollapsibleTrigger>

                <CollapsibleContent>
                  <div className="px-4 py-3 bg-bg-surface border-b border-white/[0.06]">
                    <p className="text-xs text-text-secondary leading-relaxed">
                      {artist.narrative}
                    </p>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            )
          })}
        </div>
      </div>
    </div>
  )
}
