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

  const sendMessage = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    let ws: WebSocket
    let reconnectAttempts = 0
    const maxReconnectAttempts = 3

    const connect = () => {
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

        ws.onclose = () => {
          setConnected(false)
          console.log('WebSocket disconnected')

          // Attempt to reconnect
          if (reconnectAttempts < maxReconnectAttempts) {
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
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (ws) {
        ws.close()
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
