import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useModels(agentKey) {
  const { data: modelsData } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
    staleTime: Infinity,
  })

  const [selectedModelId, setSelectedModelId] = useState(
    () => localStorage.getItem(`cdx_model_${agentKey}`) || null
  )
  const [selectedProvider, setSelectedProvider] = useState(null)

  // Auto-select default model on first load
  useEffect(() => {
    if (!modelsData) return
    const providers = modelsData.providers || {}

    // If we have a saved model, find its provider
    if (selectedModelId) {
      for (const [providerId, config] of Object.entries(providers)) {
        if (config.models?.some(m => m.id === selectedModelId)) {
          setSelectedProvider(providerId)
          return
        }
      }
    }

    // Otherwise, auto-select the default model for the first available provider
    for (const [providerId, config] of Object.entries(providers)) {
      const defaultModel = config.models?.find(m => m.default)
      if (defaultModel) {
        setSelectedModelId(defaultModel.id)
        setSelectedProvider(providerId)
        localStorage.setItem(`cdx_model_${agentKey}`, defaultModel.id)
        return
      }
    }

    // Fallback: first model of first provider
    const firstEntry = Object.entries(providers)[0]
    if (firstEntry) {
      const [providerId, config] = firstEntry
      const firstModel = config.models?.[0]
      if (firstModel) {
        setSelectedModelId(firstModel.id)
        setSelectedProvider(providerId)
        localStorage.setItem(`cdx_model_${agentKey}`, firstModel.id)
      }
    }
  }, [modelsData, agentKey]) // eslint-disable-line react-hooks/exhaustive-deps

  const selectModel = (modelId, providerId) => {
    setSelectedModelId(modelId)
    setSelectedProvider(providerId)
    localStorage.setItem(`cdx_model_${agentKey}`, modelId)
  }

  const getSelectedModelLabel = () => {
    if (!modelsData || !selectedModelId) return selectedModelId || ''
    for (const config of Object.values(modelsData.providers || {})) {
      const model = config.models?.find(m => m.id === selectedModelId)
      if (model) return model.label
    }
    return selectedModelId || ''
  }

  const hasModels = !!(modelsData && Object.keys(modelsData.providers || {}).length > 0)

  return {
    modelsData,
    selectedModelId,
    selectedProvider,
    selectModel,
    getSelectedModelLabel,
    hasModels,
  }
}
