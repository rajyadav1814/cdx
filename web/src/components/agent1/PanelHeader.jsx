import AgentBadge from '@/components/shared/AgentBadge'

export default function PanelHeader({ agent, description }) {
  return (
    <div
      className="flex items-center gap-4 p-4 bg-bg-surface border-b border-white/[0.06] flex-shrink-0"
      style={{ borderLeft: `2px solid ${agent.color}` }}
    >
      <AgentBadge id={agent.id} color={agent.color} size="md" />
      <div>
        <span className="label" style={{ color: agent.color }}>
          AGENT {agent.id} OF 4
        </span>
        <h2 className="font-display font-bold text-heading text-text-primary leading-tight">
          {agent.name}
        </h2>
        <p className="text-sm text-text-secondary">{description}</p>
      </div>
    </div>
  )
}
