import { useState, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

const STAGES = [
  { key: 'scores', label: 'Generating scores...' },
  { key: 'agent1', label: 'Running Agent 1 — Opportunity Discovery...' },
  { key: 'agent2', label: 'Running Agent 2 — Strategy Synthesis...' },
  { key: 'agent3', label: 'Running Agent 3 — Audience-Fit...' },
  { key: 'agent4', label: 'Running Agent 4 — ROI Forecast...' },
  { key: 'done',   label: 'Pipeline complete ✓' },
]

export function usePipeline() {
  const queryClient = useQueryClient()
  const [stageIndex, setStageIndex] = useState(0)
  const [isRunning, setIsRunning] = useState(false)
  const intervalRef = useRef(null)

  const { data: statusData } = useQuery({
    queryKey: ['pipelineStatus'],
    queryFn: api.getPipelineStatus,
    refetchInterval: isRunning ? 2000 : false,
  })

  useEffect(() => {
    if (statusData?.status === 'complete' && isRunning) {
      setIsRunning(false)
      setStageIndex(STAGES.length - 1)
      clearInterval(intervalRef.current)
      queryClient.invalidateQueries()
    }
  }, [statusData?.status]) // eslint-disable-line react-hooks/exhaustive-deps

  const runPipeline = async () => {
    setIsRunning(true)
    setStageIndex(0)
    await api.runPipeline()
    intervalRef.current = setInterval(() => {
      setStageIndex(i => Math.min(i + 1, STAGES.length - 2))
    }, 8000)
  }

  return {
    isRunning,
    currentStageLabel: STAGES[stageIndex]?.label || '',
    stageProgress: (stageIndex / (STAGES.length - 1)) * 100,
    runPipeline,
    lastRun: statusData?.last_run,
    status: statusData?.status || 'idle',
  }
}
