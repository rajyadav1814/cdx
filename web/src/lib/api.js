export const api = {
  getSummary:        () => fetch('/api/summary').then(r => r.json()),
  getModels:         () => fetch('/api/models').then(r => r.json()),
  getAgent1:         () => fetch('/api/agent1').then(r => r.json()),
  getAgent2:         () => fetch('/api/agent2').then(r => r.json()),
  getAgent3:         () => fetch('/api/agent3').then(r => r.json()),
  getAgent4:         () => fetch('/api/agent4').then(r => r.json()),
  getRoiScenarios:   () => fetch('/api/roi_scenarios').then(r => r.json()),
  getPipelineStatus: () => fetch('/api/pipeline_status').then(r => r.json()),
  runPipeline:       () => fetch('/api/run_pipeline', { method: 'POST' }).then(r => r.json()),
  clearChat: (sessionId) =>
    fetch(`/api/chat/clear?session_id=${sessionId}`).then(r => r.json()),
  sendChat: (agentKey, payload) =>
    fetch(`/api/chat/${agentKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(r => r.json()),
}
