import { createContext, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'
import Header from './Header'
import WorkflowBanner from './WorkflowBanner'

export const NavigationContext = createContext(null)

export default function AppShell({ children, activePanel, onNavigate, summary }) {
  const [bannerDismissed, setBannerDismissed] = useState(false)

  const { isError: serverDown } = useQuery({
    queryKey: ['health'],
    queryFn: () =>
      fetch('/api/summary').then(r => {
        if (!r.ok) throw new Error('Server unreachable')
        return r.json()
      }),
    retry: 1,
    staleTime: 30000,
    refetchOnWindowFocus: false,
  })

  const showBanner = serverDown && !bannerDismissed

  return (
    <NavigationContext.Provider value={onNavigate}>
      <div className="min-h-screen bg-bg-base text-text-primary">
        {showBanner && (
          <div
            className="flex items-center justify-between px-6 py-2 border-b"
            style={{
              backgroundColor: 'rgba(204,27,27,0.10)',
              borderColor: 'rgba(204,27,27,0.30)',
            }}
          >
          </div>
        )}
        <Header />
        <WorkflowBanner
          activePanel={activePanel}
          onNavigate={onNavigate}
          summary={summary}
        />
        <main
          style={{
            height: showBanner
              ? 'calc(100vh - 112px - 37px)'
              : 'calc(100vh - 112px)',
            overflow: 'hidden',
          }}
        >
        </main>
      </div>
    </NavigationContext.Provider>
  )
}
