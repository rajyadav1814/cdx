import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import AppShell from '@/components/layout/AppShell'
import ErrorBoundary from '@/components/ErrorBoundary'
import OverviewPanel from '@/panels/OverviewPanel'
import Agent1Panel from '@/panels/Agent1Panel'
import Agent2Panel from '@/panels/Agent2Panel'
import Agent3Panel from '@/panels/Agent3Panel'
import Agent4Panel from '@/panels/Agent4Panel'
import { api } from '@/lib/api'

const PANELS = {
  overview: OverviewPanel,
  agent1:   Agent1Panel,
  agent2:   Agent2Panel,
  agent3:   Agent3Panel,
  agent4:   Agent4Panel,
}

export default function App() {
  const [activePanel, setActivePanel] = useState('overview')

  const { data: summary } = useQuery({
    queryKey: ['summary'],
    queryFn: api.getSummary,
    staleTime: 30000,
  })

  const ActivePanel = PANELS[activePanel] ?? OverviewPanel

  return (
    <AppShell
      activePanel={activePanel}
      onNavigate={setActivePanel}
      summary={summary}
    >
      <ErrorBoundary key={activePanel}>
        <ActivePanel onNavigate={setActivePanel} />
      </ErrorBoundary>
    </AppShell>
  )
}
