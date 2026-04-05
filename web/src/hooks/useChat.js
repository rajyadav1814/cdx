import { useState, useCallback } from 'react'
import { api } from '@/lib/api'

export function useChat(agentKey) {
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState(
    () => sessionStorage.getItem(`cdx_session_${agentKey}`) || null
  )
  const [isLoading, setIsLoading] = useState(false)
  const [artistFilter, setArtistFilter] = useState(null)

  const sendMessage = useCallback(async (text, modelId) => {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return

    const userMsg = {
      id: `u_${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)

    try {
      const resp = await api.sendChat(agentKey, {
        message: trimmed,
        model_id: modelId,
        artist_filter: artistFilter || '',
        session_id: sessionId || undefined,
      })

      if (resp.session_id) {
        setSessionId(resp.session_id)
        sessionStorage.setItem(`cdx_session_${agentKey}`, resp.session_id)
      }

      localStorage.setItem(`cdx_has_chat_${agentKey}`, '1')

      const assistantMsg = {
        id: `a_${Date.now()}`,
        role: 'assistant',
        content: resp.reply,
        modelId: resp.model_id,
        modelLabel: resp.model_label,
        provider: resp.provider,
        timestamp: resp.timestamp || new Date().toISOString(),
        isError: !!(resp.error),
        artistContext: resp.artist_context || null,
      }
      setMessages(prev => [...prev, assistantMsg])
      return assistantMsg
    } catch (err) {
      const errMsg = {
        id: `e_${Date.now()}`,
        role: 'assistant',
        content: 'Failed to connect. Check the API server is running on port 8000.',
        timestamp: new Date().toISOString(),
        isError: true,
      }
      setMessages(prev => [...prev, errMsg])
      return errMsg
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, artistFilter, sessionId, agentKey])

  const clearChat = useCallback(async () => {
    if (sessionId) {
      api.clearChat(sessionId).catch(() => {})
    }
    setMessages([])
    setSessionId(null)
    sessionStorage.removeItem(`cdx_session_${agentKey}`)
    localStorage.removeItem(`cdx_has_chat_${agentKey}`)
  }, [sessionId, agentKey])

  return {
    messages,
    isLoading,
    sessionId,
    artistFilter,
    setArtistFilter,
    sendMessage,
    clearChat,
    hasMessages: messages.length > 0,
  }
}
