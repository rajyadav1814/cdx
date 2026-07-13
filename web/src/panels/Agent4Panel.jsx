import { useState, useEffect, useContext } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MessageSquare } from 'lucide-react'
import { NavigationContext } from '@/components/layout/AppShell'
import { api } from '@/lib/api'
import { AGENT_SUGGESTIONS } from '@/lib/constants'
import { useChat } from '@/hooks/useChat'
import ChatPanel from '@/components/chat/ChatPanel'
import Agent4Analytics from './analytics/Agent4Analytics'

const ACCENT = '#D4924A'

export default function Agent4Panel() {
  const navigate = useContext(NavigationContext)

  const { data, isLoading } = useQuery({
    queryKey: ['agent4'],
    queryFn: api.getAgent4,
  })

  const [mobileView, setMobileView]         = useState('chat')
  const [artistFocus, setArtistFocus]       = useState(null)
  const [initialMessage, setInitialMessage] = useState(null)

  const { hasMessages } = useChat('agent4')

  const artistOptions = data?.map(a => a.artist_name) ?? []

  useEffect(() => {
    const carryover = sessionStorage.getItem('cdx_artist_carryover')
    if (carryover) {
      setArtistFocus(carryover)
      sessionStorage.removeItem('cdx_artist_carryover')
    }
  }, [])

  const handleAskAgent = (name) => {
    setArtistFocus(name)
    setInitialMessage(`Walk me through the ROI forecast for ${name}`)
    setMobileView('chat')
  }

  const handleContinue = (target) => {
    if (artistFocus) sessionStorage.setItem('cdx_artist_carryover', artistFocus)
    navigate?.(target)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Mobile toggle */}
      <div className="flex md:hidden border-b border-white/[0.06] flex-shrink-0 bg-bg-surface">
        {[['chat', '💬 Chat'], ['analytics', '📊 Analytics']].map(([view, label]) => (
          <button
            key={view}
            onClick={() => setMobileView(view)}
            className="flex-1 py-2 text-sm font-medium bg-transparent border-0 cursor-pointer transition-colors"
            style={{
              color: mobileView === view ? ACCENT : 'var(--text-secondary)',
              borderBottom: mobileView === view ? `2px solid ${ACCENT}` : '2px solid transparent',
              fontFamily: 'inherit',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Chat — left 38% */}
        <div
          className={`w-full md:w-[38%] border-r border-white/[0.06] flex flex-col overflow-hidden
            ${mobileView === 'analytics' ? 'hidden md:flex' : 'flex'}`}
        >
          <ChatPanel
            agentKey="agent4"
            agentName="ROI Forecast"
            agentSub="Is It Worth It?"
            accentColor={ACCENT}
            artistOptions={artistOptions}
            suggestedQuestions={AGENT_SUGGESTIONS.agent4}
            onArtistMention={setArtistFocus}
            focusArtist={artistFocus}
            initialMessage={initialMessage}
            onContinue={handleContinue}
          />
        </div>

        {/* Analytics — right 62% */}
        <div
          className={`flex-1 overflow-y-auto relative
            ${mobileView === 'chat' ? 'hidden md:block' : 'block'}`}
        >
          <Agent4Analytics
            data={data}
            isLoading={isLoading}
            artistFocus={artistFocus}
            onAskAgent={handleAskAgent}
          />

          {/* Mobile FAB */}
          {mobileView === 'analytics' && (
            <button
              onClick={() => setMobileView('chat')}
              className="fixed bottom-6 right-6 md:hidden w-14 h-14 rounded-full flex items-center justify-center shadow-lg z-50"
              style={{ backgroundColor: ACCENT }}
            >
              <MessageSquare className="text-white" size={22} />
              {hasMessages && (
                <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-brand-red border-2 border-bg-base" />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
