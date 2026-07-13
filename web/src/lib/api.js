const BASE_URL = import.meta.env.VITE_BACKEND_URL || '';

export const api = {
  getSummary:        () => fetch(`${BASE_URL}/api/summary`).then(r => r.json()),
  getModels:         () => fetch(`${BASE_URL}/api/models`).then(r => r.json()),
  getAgent1:         () => fetch(`${BASE_URL}/api/agent1`).then(r => r.json()),
  getAgent2:         () => fetch(`${BASE_URL}/api/agent2`).then(r => r.json()),
  getAgent3:         () => fetch(`${BASE_URL}/api/agent3`).then(r => r.json()),
  getAgent4:         () => fetch(`${BASE_URL}/api/agent4`).then(r => r.json()),
  getRoiScenarios:   () => fetch(`${BASE_URL}/api/roi_scenarios`).then(r => r.json()),
  getPipelineStatus: () => fetch(`${BASE_URL}/api/pipeline_status`).then(r => r.json()),
  runPipeline:       () => fetch(`${BASE_URL}/api/run_pipeline`, { method: 'POST' }).then(r => r.json()),
  clearChat: (sessionId) =>
    fetch(`${BASE_URL}/api/chat/clear?session_id=${sessionId}`).then(r => r.json()),
  sendChat: (agentKey, payload) =>
    fetch(`${BASE_URL}/api/chat/${agentKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(r => r.json()),
}
