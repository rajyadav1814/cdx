import { useQuery } from '@tanstack/react-query'
import { TrendingUp } from 'lucide-react'
import { AGENTS } from '@/lib/constants'
import { api } from '@/lib/api'
import SkeletonPanel from '@/components/shared/SkeletonPanel'
import EmptyState from '@/components/shared/EmptyState'
import KpiCard from '@/components/shared/KpiCard'
import PanelHeader from '@/components/agent1/PanelHeader'
import MomentumBarChart from '@/components/agent1/MomentumBarChart'
import TerritoryChart from '@/components/agent1/TerritoryChart'
import NarrativeCards from '@/components/agent1/NarrativeCards'
import ArtistTable from '@/components/agent1/ArtistTable'

export default function Agent1Panel() {
  const agent = AGENTS[1]
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['agent1'],
    queryFn: api.getAgent1,
    staleTime: 60000,
  })

  if (isLoading) return <SkeletonPanel />

  if (isError) {
    return (
      <div className="p-6">
        <div
          className="card flex items-center justify-between gap-4"
          style={{ borderColor: '#CC1B1B' }}
        >
          <span className="text-sm text-text-secondary">
            Failed to load opportunity data. Check the API server.
          </span>
          <button className="btn-primary flex-shrink-0" onClick={() => refetch()}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-full">
        <EmptyState
          icon={TrendingUp}
          title="No opportunity data"
          message="Run the pipeline to generate Agent 1 results"
          action="Run Pipeline"
          onAction={api.runPipeline}
        />
      </div>
    )
  }

  const highCount   = data.filter(d => d.opportunity_class === 'HIGH').length
  const mediumCount = data.filter(d => d.opportunity_class === 'MEDIUM').length
  const avgMomentum = (
    data.reduce((sum, d) => sum + Number(d.momentum_score), 0) / data.length
  ).toFixed(1)

  return (
    <div className="h-full flex flex-col overflow-hidden bg-bg-base">
      <PanelHeader
        agent={agent}
        description="Identifies artists with the strongest commercial momentum across territories and platforms"
      />

      {/* KPI row */}
      <div className="flex-shrink-0 grid grid-cols-2 md:grid-cols-4 gap-4 p-4">
        <KpiCard
          label="ARTISTS ANALYZED"
          value={data.length}
          accentColor="#1D9E75"
          watermarkChar="∑"
        />
        <KpiCard
          label="HIGH OPPORTUNITIES"
          value={highCount}
          accentColor="#1D9E75"
        />
        <KpiCard
          label="MEDIUM OPPORTUNITIES"
          value={mediumCount}
          accentColor="#D4924A"
        />
        <KpiCard
          label="AVG MOMENTUM SCORE"
          value={<span className="font-mono">{avgMomentum}</span>}
          accentColor="#1D9E75"
        />
      </div>

      {/* scrollable content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <MomentumBarChart data={data} />
          <TerritoryChart data={data} />
          <NarrativeCards data={data} />
        </div>
        <ArtistTable data={data} />
      </div>
    </div>
  )
}
