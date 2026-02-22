import { useState, useEffect, useCallback, useRef } from 'react'

export type WebSocketStage = 'text_extraction' | 'nlp_parsing' | 'ai_enhancement' | 'complete' | 'error'

export interface WebSocketMessage {
  type: string
  resume_id?: string
  stage?: WebSocketStage | string
  progress?: number
  status?: string
  estimated_seconds_remaining?: number
  data?: unknown
  timestamp?: string
}

export interface WebSocketHookReturn {
  connected: boolean
  lastMessage: WebSocketMessage | null
  sendMessage: (message: unknown) => void
  error: Event | null
}

export function useWebSocket(url: string): WebSocketHookReturn {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<Event | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const isCleaningUpRef = useRef(false)
  const connectionAttemptedRef = useRef(false)  // Prevent duplicate connections

  const sendMessage = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    // Prevent multiple connections in React StrictMode
    if (connectionAttemptedRef.current) {
      return
    }
    connectionAttemptedRef.current = true

    let ws: WebSocket
    let reconnectAttempts = 0
    const maxReconnectAttempts = 3
    isCleaningUpRef.current = false

    const connect = () => {
      // Don't reconnect if component is unmounting
      if (isCleaningUpRef.current) {
        return
      }

      // Prevent multiple WebSocket instances
      if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
        return
      }

      try {
        ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => {
          setConnected(true)
          setError(null)
          reconnectAttempts = 0
          console.log('WebSocket connected')
        }

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            setLastMessage(message)
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err)
          }
        }

        ws.onerror = (event: Event) => {
          console.error('WebSocket error:', event)
          setError(event)
        }

        ws.onclose = (event) => {
          setConnected(false)
          console.log('WebSocket disconnected', { code: event.code, reason: event.reason })

          // Only attempt to reconnect if:
          // 1. Component is not unmounting
          // 2. The close was not intentional (code 1000)
          // 3. We haven't exceeded max reconnect attempts
          if (!isCleaningUpRef.current && event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++
            console.log(`Reconnecting... Attempt ${reconnectAttempts}`)
            reconnectTimeoutRef.current = setTimeout(connect, 2000)
          }
        }
      } catch (err) {
        console.error('Failed to create WebSocket connection:', err)
        setError(err as Event)
      }
    }

    connect()

    // Cleanup on unmount
    return () => {
      isCleaningUpRef.current = true
      connectionAttemptedRef.current = false  // Reset for next mount
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting')
        wsRef.current = null
      }
    }
  }, [url])

  return {
    connected,
    lastMessage,
    sendMessage,
    error
  }
}
