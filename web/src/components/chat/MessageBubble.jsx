import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'

const PROVIDER_COLORS = {
  anthropic: '#D4845A',
  openai:    '#19C37D',
}

function shortLabel(label) {
  if (!label) return ''
  // "Claude Sonnet 4.6" → "Sonnet 4.6", "GPT-4o Mini" → "GPT-4o Mini"
  return label
    .replace('Claude ', '')
    .replace('claude-', '')
}

function formatTimestamp(ts) {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

function parseContent(text) {
  if (!text) return []

  const segments = []
  const lines = text.split('\n')
  let listItems = []

  const flushList = () => {
    if (listItems.length > 0) {
      segments.push({ type: 'list', items: [...listItems] })
      listItems = []
    }
  }

  lines.forEach((line, idx) => {
    const listMatch = line.match(/^[-*]\s+(.+)/)
    if (listMatch) {
      listItems.push(listMatch[1])
      return
    }
    flushList()

    if (line.trim() === '') {
      if (idx > 0) segments.push({ type: 'br' })
      return
    }

    // Process inline bold
    const parts = []
    const boldRegex = /\*\*(.+?)\*\*/g
    let last = 0
    let m
    while ((m = boldRegex.exec(line)) !== null) {
      if (m.index > last) parts.push({ type: 'text', content: line.slice(last, m.index) })
      parts.push({ type: 'bold', content: m[1] })
      last = m.index + m[0].length
    }
    if (last < line.length) parts.push({ type: 'text', content: line.slice(last) })

    segments.push({ type: 'inline', parts })
  })
  flushList()

  return segments
}

function RenderedContent({ text }) {
  const segments = parseContent(text)
  return (
    <span>
      {segments.map((seg, i) => {
        if (seg.type === 'br') return <br key={i} />
        if (seg.type === 'list') {
          return (
            <ul key={i} className="list-disc pl-4 my-1 space-y-0.5">
              {seg.items.map((item, j) => (
                <li key={j}>{item}</li>
              ))}
            </ul>
          )
        }
        if (seg.type === 'inline') {
          return (
            <span key={i}>
              {seg.parts.map((p, j) =>
                p.type === 'bold'
                  ? <strong key={j} className="font-semibold text-text-primary">{p.content}</strong>
                  : <span key={j}>{p.content}</span>
              )}
            </span>
          )
        }
        return null
      })}
    </span>
  )
}

export default function MessageBubble({ message, accentColor }) {
  const [showTime, setShowTime] = useState(false)

  if (message.role === 'user') {
    return (
      <div className="flex justify-end px-4 py-1.5">
        <div className="max-w-[75%] bg-bg-surface2 rounded-sm px-3 py-2 text-sm text-text-primary leading-relaxed">
          {message.content}
        </div>
      </div>
    )
  }

  const providerColor = PROVIDER_COLORS[message.provider] || '#8A8A9A'

  return (
    <div className="flex items-start gap-2 px-4 py-2 max-w-[80%]">
      {/* CD badge */}
      <div
        className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-sm font-mono font-bold text-[9px] mt-0.5"
        style={{
          backgroundColor: `${accentColor}1A`,
          borderTop: `2px solid ${accentColor}B3`,
          color: accentColor,
        }}
      >
        CD
      </div>

      <div
        className="flex-1 rounded-sm px-3 py-2 text-sm leading-relaxed"
        style={{
          backgroundColor: `${accentColor}0F`,
          borderLeft: `2px solid ${accentColor}`,
          color: message.isError ? 'rgba(204,27,27,0.8)' : 'inherit',
        }}
      >
        {message.isError && (
          <div className="flex items-center gap-1.5 mb-1">
            <AlertTriangle size={12} className="text-brand-red" />
            <span className="text-xs text-brand-red font-medium">Error</span>
          </div>
        )}

        <div
          className="text-text-secondary"
          onMouseEnter={() => setShowTime(true)}
          onMouseLeave={() => setShowTime(false)}
        >
          <RenderedContent text={message.content} />
        </div>

        <div className="flex items-center gap-2 mt-2 flex-wrap">
          {showTime && message.timestamp && (
            <span className="text-[10px] text-text-muted font-mono">
              {formatTimestamp(message.timestamp)}
            </span>
          )}
          {message.modelLabel && (
            <span
              className="text-[10px] px-1.5 py-0.5 rounded-sm font-medium"
              style={{
                color: providerColor,
                backgroundColor: `${providerColor}15`,
              }}
            >
              {shortLabel(message.modelLabel)}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
