import { useRef, useEffect, useContext, useCallback } from 'react'
import { Trash2 } from 'lucide-react'
import { NavigationContext } from '@/components/layout/AppShell'
import { useChat } from '@/hooks/useChat'
import { useModels } from '@/hooks/useModels'
import ModelSelector from './ModelSelector'
import MessageBubble from './MessageBubble'
import SuggestedQuestions from './SuggestedQuestions'
import TypingIndicator from './TypingIndicator'

const CONTINUE_LINKS = {
  agent2: { label: 'Continue to Audience-Fit →', target: 'agent3' },
  agent3: { label: 'Continue to ROI Forecast →', target: 'agent4' },
  agent4: { label: '← Back to overview',         target: 'overview' },
}

export default function ChatPanel({
  agentKey,
  agentName,
  agentSub,
  accentColor,
  artistOptions = [],
  suggestedQuestions = [],
  onArtistMention,
  focusArtist,
  initialMessage,
  onContinue,
}) {
  const navigate = useContext(NavigationContext)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  const {
    messages,
    isLoading,
    artistFilter,
    setArtistFilter,
    sendMessage,
    clearChat,
    hasMessages,
  } = useChat(agentKey)

  const {
    modelsData,
    selectedModelId,
    selectedProvider,
    selectModel,
    getSelectedModelLabel,
  } = useModels(agentKey)

  // Sync external focusArtist → internal artistFilter
  useEffect(() => {
    if (focusArtist) setArtistFilter(focusArtist)
  }, [focusArtist, setArtistFilter])

  // Pre-fill textarea when initialMessage changes
  useEffect(() => {
    if (initialMessage && textareaRef.current) {
      textareaRef.current.value = initialMessage
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 120) + 'px'
      textareaRef.current.focus()
    }
  }, [initialMessage])

  // Auto-scroll to bottom on new messages or loading state change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isLoading])

  const handleSend = useCallback(async () => {
    if (!textareaRef.current) return
    const text = textareaRef.current.value.trim()
    if (!text || isLoading) return
    textareaRef.current.value = ''
    textareaRef.current.style.height = 'auto'
    const result = await sendMessage(text, selectedModelId)
    // Check if any artist was mentioned in the reply
    if (result && !result.isError && onArtistMention && artistOptions.length > 0) {
      const replyLower = (result.content || '').toLowerCase()
      const mentioned = artistOptions.find(name => replyLower.includes(name.toLowerCase()))
      if (mentioned) onArtistMention(mentioned)
    }
  }, [isLoading, sendMessage, selectedModelId, onArtistMention, artistOptions])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaInput = (e) => {
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const handleContinue = (target) => {
    if (onContinue) {
      onContinue(target)
    } else if (navigate) {
      navigate(target)
    }
  }

  const modelLabel = getSelectedModelLabel()
  const continueLink = CONTINUE_LINKS[agentKey]

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* ── Header ────────────────────────────────────────────────── */}
      <div
        className="flex-shrink-0 p-3 bg-bg-surface border-b border-white/[0.06] space-y-2"
        style={{ borderTop: `3px solid ${accentColor}` }}
      >
        {/* Title row */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="font-display font-bold text-sm text-text-primary truncate">
              {agentName}
            </div>
            <div className="text-xs text-text-muted">{agentSub}</div>
          </div>
          <button
            className="btn-icon flex-shrink-0"
            onClick={clearChat}
            title="Clear conversation"
          >
            <Trash2 size={13} />
          </button>
        </div>

        {/* Model selector */}
        <ModelSelector
          agentKey={agentKey}
          modelsData={modelsData}
          selectedModelId={selectedModelId}
          selectedProvider={selectedProvider}
          onSelect={selectModel}
          accentColor={accentColor}
        />

        {/* Artist filter */}
        <div className="flex items-center gap-1.5">
          <select
            value={artistFilter || ''}
            onChange={e => setArtistFilter(e.target.value || null)}
            className="input text-xs py-1 flex-1"
            style={{ height: 28 }}
          >
            <option value="">All artists</option>
            {artistOptions.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>

          {artistFilter && (
            <button
              className="flex items-center gap-1 px-2 py-0.5 rounded-sm text-[11px] font-medium cursor-pointer border-0"
              style={{
                backgroundColor: `${accentColor}20`,
                color: accentColor,
                fontFamily: 'inherit',
              }}
              onClick={() => setArtistFilter(null)}
            >
              {artistFilter} ×
            </button>
          )}
        </div>
      </div>

      {/* ── Messages ──────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto py-2">
        {!hasMessages && !isLoading ? (
          <SuggestedQuestions
            questions={suggestedQuestions}
            onSelect={q => {
              if (textareaRef.current) {
                textareaRef.current.value = q
                textareaRef.current.style.height = 'auto'
                textareaRef.current.style.height =
                  Math.min(textareaRef.current.scrollHeight, 120) + 'px'
              }
              handleSend()
            }}
          />
        ) : (
          <>
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} accentColor={accentColor} />
            ))}
            {isLoading && (
              <TypingIndicator modelLabel={modelLabel} accentColor={accentColor} />
            )}
          </>
        )}

        {/* Continue navigation — only when there are messages */}
        {hasMessages && !isLoading && continueLink && (
          <div className="px-4 pt-2 pb-1">
            <button
              className="text-xs font-medium transition-opacity hover:opacity-70 bg-transparent border-0 p-0 cursor-pointer"
              style={{ color: accentColor, fontFamily: 'inherit' }}
              onClick={() => handleContinue(continueLink.target)}
            >
              {continueLink.label}
            </button>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ─────────────────────────────────────────────── */}
      <div className="flex-shrink-0 border-t border-white/[0.06] p-3 bg-bg-surface">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            className="input flex-1 resize-none text-sm leading-relaxed"
            placeholder={`Ask ${agentName}${modelLabel ? ` (${modelLabel})` : ''}…`}
            rows={1}
            disabled={isLoading}
            onInput={handleTextareaInput}
            onKeyDown={handleKeyDown}
            style={{ minHeight: 36, maxHeight: 120, paddingTop: 8, paddingBottom: 8 }}
          />
          <button
            className="btn-primary flex-shrink-0 px-3 py-2 text-xs"
            style={{
              backgroundColor: isLoading ? `${accentColor}40` : accentColor,
              cursor: isLoading ? 'not-allowed' : 'pointer',
            }}
            disabled={isLoading}
            onClick={handleSend}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
