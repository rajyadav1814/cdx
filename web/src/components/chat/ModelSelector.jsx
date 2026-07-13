const PROVIDER_COLORS = {
  anthropic: '#D4845A',
  openai:    '#19C37D',
}

export default function ModelSelector({
  agentKey,
  modelsData,
  selectedModelId,
  selectedProvider,
  onSelect,
  accentColor,
}) {
  const providers = modelsData?.providers || {}
  const providerIds = Object.keys(providers)

  const activeProvider = selectedProvider || providerIds[0] || ''
  const activeProviderConfig = providers[activeProvider]
  const activeModels = activeProviderConfig?.models || []

  const handleProviderClick = (providerId) => {
    const config = providers[providerId]
    const defaultModel = config?.models?.find(m => m.default) || config?.models?.[0]
    if (defaultModel) {
      onSelect(defaultModel.id, providerId)
    }
  }

  if (providerIds.length === 0) {
    return (
      <div className="text-xs text-text-muted px-1">
        No models configured. Set an API key in ~/cdx/.env.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1.5">
      {/* Provider tabs */}
      {providerIds.length > 1 && (
        <div className="flex gap-1">
          {providerIds.map(pid => {
            const isActive = pid === activeProvider
            const color = PROVIDER_COLORS[pid] || accentColor
            return (
              <button
                key={pid}
                onClick={() => handleProviderClick(pid)}
                className="px-2.5 py-1 rounded-sm text-[11px] font-medium uppercase tracking-wide transition-colors duration-100 cursor-pointer border-0"
                style={{
                  backgroundColor: isActive ? color : 'var(--bg-surface2)',
                  color: isActive ? '#fff' : 'var(--text-secondary)',
                  fontFamily: 'inherit',
                }}
              >
                {providers[pid]?.label || pid}
              </button>
            )
          })}
        </div>
      )}

      {/* Model select */}
      <select
        value={selectedModelId || ''}
        onChange={e => onSelect(e.target.value, activeProvider)}
        className="input text-xs py-1.5 pr-8 cursor-pointer"
        style={{ height: 30 }}
      >
        {activeModels.map(m => (
          <option key={m.id} value={m.id}>
            {m.label} — {m.description} ({m.tier})
          </option>
        ))}
      </select>
    </div>
  )
}
