import LogoIcon from '@/components/shared/LogoIcon'
import AgentBadge from '@/components/shared/AgentBadge'
import { AGENTS } from '@/lib/constants'

function hasChatActivity(agentKey) {
  try {
    return !!localStorage.getItem(`cdx_has_chat_${agentKey}`)
  } catch {
    return false
  }
}

function getAgentCount(agentKey, summary) {
  if (!summary) return null
  const map = {
    agent1: summary.agent1?.high_opportunities != null
      ? summary.agent1.high_opportunities + summary.agent1.medium_opportunities
      : null,
    agent2: summary.agent2?.briefs_generated ?? null,
    agent3: summary.agent3?.avg_reach
      ? `${(summary.agent3.avg_reach / 1_000_000).toFixed(1)}M avg`
      : null,
    agent4: summary.agent4?.avg_base_roi
      ? `${summary.agent4.avg_base_roi.toFixed(2)}x ROI`
      : null,
  }
  return map[agentKey] ?? null
}

export default function WorkflowBanner({ activePanel, onNavigate, summary }) {
  const agentList = Object.values(AGENTS)

  return (
    <div
      className="flex items-center overflow-x-auto"
      style={{
        height: 56,
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-color)',
        scrollbarWidth: 'none',
      }}
    >
      {/* Left label */}
      <div className="flex items-center gap-2 px-5 flex-shrink-0">
        <LogoIcon size="sm" />
        <span className="label text-text-muted ml-1">CSIE PIPELINE</span>
      </div>

      <span className="text-text-muted px-1 flex-shrink-0">›</span>

      {/* Overview step */}
      <button
        onClick={() => onNavigate('overview')}
        className="flex items-center gap-2 px-4 h-full flex-shrink-0 transition-colors"
        style={{
          borderBottom: activePanel === 'overview'
            ? '2px solid var(--text-primary)'
            : '2px solid transparent',
          background: activePanel === 'overview'
            ? 'var(--bg-surface2)'
            : 'transparent',
        }}
        onMouseEnter={e => {
          if (activePanel !== 'overview')
            e.currentTarget.style.background = 'var(--bg-surface2)'
        }}
        onMouseLeave={e => {
          if (activePanel !== 'overview')
            e.currentTarget.style.background = 'transparent'
        }}
      >
        <div>
          <div
            className="font-display font-bold text-text-primary"
            style={{ fontSize: 13, letterSpacing: '-0.01em' }}
          >
            Overview
          </div>
          <div className="label text-text-muted" style={{ marginTop: 1 }}>
            Pipeline summary
          </div>
        </div>
      </button>

      {/* Agent steps */}
      {agentList.map((agent, idx) => {
        const isActive = activePanel === agent.key
        const count = getAgentCount(agent.key, summary)
        const chatActive = hasChatActivity(agent.key)

        return (
          <div key={agent.id} className="flex items-center flex-shrink-0">
            <span className="text-text-muted px-1">›</span>
            <button
              onClick={() => onNavigate(agent.key)}
              className="flex items-center gap-2.5 px-5 h-full flex-shrink-0 transition-colors"
              style={{
                height: 56,
                borderBottom: isActive
                  ? `2px solid ${agent.color}`
                  : '2px solid transparent',
                background: isActive
                  ? 'var(--bg-surface2)'
                  : 'transparent',
              }}
              onMouseEnter={e => {
                if (!isActive)
                  e.currentTarget.style.background = 'var(--bg-surface2)'
              }}
              onMouseLeave={e => {
                if (!isActive)
                  e.currentTarget.style.background = 'transparent'
              }}
            >
              <AgentBadge id={agent.id} color={agent.color} size="sm" />
              <div>
                <div
                  className="font-display font-bold text-text-primary"
                  style={{ fontSize: 13, letterSpacing: '-0.01em' }}
                >
                  {agent.name}
                </div>
                <div className="label text-text-muted" style={{ marginTop: 1 }}>
                  {agent.sub}
                  {count != null && (
                    <span className="ml-2">· {count}</span>
                  )}
                </div>
              </div>
              {chatActive && (
                <div
                  className="w-1.5 h-1.5 rounded-full ml-0.5"
                  style={{ backgroundColor: agent.color }}
                />
              )}
            </button>
          </div>
        )
      })}
    </div>
  )
}
