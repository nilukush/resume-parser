import { useEffect, useState, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket'
import ProcessingStage from '@/components/ProcessingStage'
import { AlertCircle } from 'lucide-react'

interface StageProgress {
  name: string
  status: 'pending' | 'in_progress' | 'complete' | 'error'
  progress: number
  statusMessage: string
}

export default function ProcessingPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [stages, setStages] = useState<StageProgress[]>([
    { name: 'Text Extraction', status: 'pending', progress: 0, statusMessage: 'Waiting...' },
    { name: 'NLP Parsing', status: 'pending', progress: 0, statusMessage: 'Waiting...' },
    { name: 'AI Enhancement', status: 'pending', progress: 0, statusMessage: 'Waiting...' }
  ])
  const [error, setError] = useState<string | null>(null)
  const [estimatedTime, setEstimatedTime] = useState<number>(30)
  const hasRedirectedRef = useRef(false)
  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const wsUrl = `${import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws'}/resumes/${id}`
  const { connected, lastMessage } = useWebSocket(wsUrl)

  // Fallback: Poll for completion if WebSocket doesn't receive messages
  // This handles the race condition where parsing completes before WebSocket stabilizes
  const checkCompletionStatus = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v1'}/resumes/${id}`)
      if (response.ok) {
        const data = await response.json()
        if (data.status === 'complete' && data.data) {
          // Resume is complete, redirect to review page
          handleComplete({ data: data.data } as WebSocketMessage)
          return true
        }
      }
      return false
    } catch {
      return false
    }
  }

  useEffect(() => {
    // If WebSocket connects but we don't receive progress after 5 seconds,
    // check if parsing is already complete (race condition fallback)
    if (connected && !hasRedirectedRef.current) {
      pollTimeoutRef.current = setTimeout(async () => {
        const isComplete = await checkCompletionStatus()
        if (!isComplete) {
          // If not complete, set stages to in_progress as parsing is likely happening
          setStages(prev => prev.map((s, i) =>
            i === 0 ? { ...s, status: 'in_progress' as const, statusMessage: 'Processing...' } : s
          ))
        }
      }, 5000)
    }

    return () => {
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current)
      }
    }
  }, [connected, id])

  // Also check immediately if WebSocket never connects
  useEffect(() => {
    const immediateCheckTimeout = setTimeout(async () => {
      if (!connected && !hasRedirectedRef.current) {
        const isComplete = await checkCompletionStatus()
        if (isComplete) {
          // Already complete, redirect will be handled by checkCompletionStatus
        }
      }
    }, 2000)

    return () => clearTimeout(immediateCheckTimeout)
  }, [connected, id])

  useEffect(() => {
    if (!lastMessage) return

    const message = lastMessage as WebSocketMessage

    switch (message.type) {
      case 'connection_established':
        console.log('WebSocket connected for resume:', message.resume_id)
        break

      case 'progress_update':
        updateStageProgress(message)
        break

      case 'complete':
        handleComplete(message)
        break

      case 'error':
        handleError(message)
        break
    }
  }, [lastMessage])

  const updateStageProgress = (message: WebSocketMessage) => {
    setStages(prevStages => {
      const newStages = [...prevStages]

      switch (message.stage) {
        case 'text_extraction':
          newStages[0] = {
            ...newStages[0],
            status: message.progress === 100 ? 'complete' : 'in_progress',
            progress: message.progress || 0,
            statusMessage: message.status || 'Processing...'
          }
          break

        case 'nlp_parsing':
          newStages[0] = { ...newStages[0], status: 'complete', progress: 100 }
          newStages[1] = {
            ...newStages[1],
            status: message.progress === 100 ? 'complete' : 'in_progress',
            progress: message.progress || 0,
            statusMessage: message.status || 'Processing...'
          }
          break

        case 'ai_enhancement':
          newStages[0] = { ...newStages[0], status: 'complete', progress: 100 }
          newStages[1] = { ...newStages[1], status: 'complete', progress: 100 }
          newStages[2] = {
            ...newStages[2],
            status: message.progress === 100 ? 'complete' : 'in_progress',
            progress: message.progress || 0,
            statusMessage: message.status || 'Processing...'
          }
          break

        case 'complete':
          // Mark all stages as complete and trigger redirect
          newStages[0] = { ...newStages[0], status: 'complete', progress: 100 }
          newStages[1] = { ...newStages[1], status: 'complete', progress: 100 }
          newStages[2] = { ...newStages[2], status: 'complete', progress: 100 }
          break
      }

      // Update estimated time
      if (message.estimated_seconds_remaining !== undefined) {
        setEstimatedTime(message.estimated_seconds_remaining)
      }

      return newStages
    })

    // If stage is complete, trigger the redirect
    if (message.stage === 'complete') {
      handleComplete(message)
    }
  }

  const handleComplete = (_message: WebSocketMessage) => {
    setStages(prevStages =>
      prevStages.map(stage => ({
        ...stage,
        status: 'complete' as const,
        progress: 100
      }))
    )

    // Prevent multiple redirects
    if (hasRedirectedRef.current) return
    hasRedirectedRef.current = true

    // Redirect to review page after a short delay
    setTimeout(() => {
      navigate(`/review/${id}`, { replace: true })
    }, 1500)
  }

  const handleError = (message: WebSocketMessage) => {
    const data = message.data as { error_message?: string } | undefined
    const errorMessage = data?.error_message || 'An unknown error occurred'
    setError(errorMessage)
  }

  const handleRetry = () => {
    setError(null)
    navigate('/', { replace: true })
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full text-center">
          <AlertCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-navy-900 mb-4">
            Parsing Failed
          </h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleRetry}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-navy-900 mb-2">
            ResuMate
          </h1>
          <p className="text-xl text-navy-700 mb-4">
            Parsing Your Resume
          </p>

          {/* Connection Status */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className={`h-3 w-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600">
              {connected ? 'Connected' : 'Connecting...'}
            </span>
          </div>

          {/* Estimated Time */}
          <div className="text-gray-600">
            Estimated time: <span className="font-semibold">{estimatedTime} seconds</span>
          </div>
        </div>

        {/* Processing Stages */}
        <div className="space-y-4">
          {stages.map((stage, index) => (
            <ProcessingStage
              key={index}
              name={stage.name}
              status={stage.status}
              progress={stage.progress}
            />
          ))}
        </div>

        {/* Cancel Button */}
        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/', { replace: true })}
            className="text-gray-600 hover:text-navy-600 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
