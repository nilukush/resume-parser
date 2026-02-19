import { renderHook, waitFor, act } from '@testing-library/react'
import { vi } from 'vitest'
import { useWebSocket } from '../useWebSocket'
import type { WebSocketMessage } from '../useWebSocket'

// Create a mock WebSocket class that simulates real behavior
class MockWebSocket {
  static url: string | null = null
  static instances: MockWebSocket[] = []
  send = vi.fn()
  close = vi.fn()
  readyState = 1 as number // WebSocket.OPEN = 1
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null

  constructor(url: string) {
    MockWebSocket.url = url
    MockWebSocket.instances.push(this)
    // Simulate connection established
    setTimeout(() => {
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }

  // Helper method to simulate receiving a message
  simulateMessage(message: WebSocketMessage) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(message) }))
    }
  }

  // Helper method to simulate an error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }

  // Helper method to simulate closing
  simulateClose() {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }
}

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset the MockWebSocket static property
    MockWebSocket.url = null
    MockWebSocket.instances = []
  })

  it('should connect to WebSocket on mount', async () => {
    globalThis.WebSocket = MockWebSocket as any

    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/test'))

    // Wait for the connection to be established
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })

    expect(MockWebSocket.url).toBe('ws://localhost:8000/ws/test')
  })

  it('should receive and parse messages', async () => {
    globalThis.WebSocket = MockWebSocket as any

    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/test'))

    // Wait for connection
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })

    // Initially, no message
    expect(result.current.lastMessage).toBe(null)

    // Simulate receiving a message
    const testMessage: WebSocketMessage = {
      type: 'progress',
      stage: 'parsing',
      progress: 50,
      status: 'processing'
    }

    // Get the WebSocket instance and send a message
    if (MockWebSocket.instances.length > 0) {
      act(() => {
        MockWebSocket.instances[0].simulateMessage(testMessage)
      })
    }

    await waitFor(() => {
      expect(result.current.lastMessage).toEqual(testMessage)
    })
  })

  it('should send messages via sendMessage', async () => {
    let wsInstance: any = null
    const allSends: any[] = []

    // Create a mock WebSocket class with OPEN state
    class TestWebSocket {
      static OPEN = 1
      send = vi.fn((data: string) => {
        allSends.push({ instance: wsInstance, data })
      })
      close = vi.fn()
      readyState = 1 as number // TestWebSocket.OPEN
      onopen: ((event: Event) => void) | null = null
      onmessage: ((event: MessageEvent) => void) | null = null
      onerror: ((event: Event) => void) | null = null
      onclose: ((event: CloseEvent) => void) | null = null
      constructor(_url: string) {
        wsInstance = this
        setTimeout(() => {
          if (this.onopen) {
            this.onopen(new Event('open'))
          }
        }, 0)
      }
    }

    globalThis.WebSocket = TestWebSocket as any

    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/test'))

    // Wait for connection
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })

    // Verify WebSocket was created and wsInstance is set
    expect(wsInstance).not.toBe(null)

    const testMessage = { type: 'ping', data: 'test' }
    act(() => {
      result.current.sendMessage(testMessage)
    })

    // Check if send was called on our instance
    expect(allSends.length).toBeGreaterThan(0)
    expect(allSends[0].data).toBe(JSON.stringify(testMessage))
  })

  it('should handle WebSocket errors', async () => {
    globalThis.WebSocket = MockWebSocket as any

    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/test'))

    // Wait for connection
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })

    // Simulate an error
    if (MockWebSocket.instances.length > 0) {
      act(() => {
        MockWebSocket.instances[0].simulateError()
      })
    }

    await waitFor(() => {
      expect(result.current.error).not.toBe(null)
    })
  })

  it('should cleanup on unmount', async () => {
    globalThis.WebSocket = MockWebSocket as any

    const { result, unmount } = renderHook(() => useWebSocket('ws://localhost:8000/ws/test'))

    // Wait for connection
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })

    const mockClose = MockWebSocket.instances.length > 0 ? MockWebSocket.instances[0].close : vi.fn()

    unmount()

    expect(mockClose).toHaveBeenCalled()
  })
})
