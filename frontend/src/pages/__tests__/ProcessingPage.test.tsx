import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi, beforeEach, describe, it, expect } from 'vitest'
import ProcessingPage from '../ProcessingPage'

// Mock the WebSocket hook
const mockUseWebSocket = vi.fn(() => ({
  connected: true,
  lastMessage: null,
  sendMessage: vi.fn(),
  error: null
}))

vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => mockUseWebSocket()
}))

describe('ProcessingPage', () => {
  beforeEach(() => {
    mockUseWebSocket.mockReturnValue({
      connected: true,
      lastMessage: null,
      sendMessage: vi.fn(),
      error: null
    })
  })

  it('renders processing page with stages', () => {
    render(
      <BrowserRouter>
        <ProcessingPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/Parsing Your Resume/i)).toBeInTheDocument()
    expect(screen.getByText(/Text Extraction/i)).toBeInTheDocument()
    expect(screen.getByText(/NLP Parsing/i)).toBeInTheDocument()
    expect(screen.getByText(/AI Enhancement/i)).toBeInTheDocument()
  })
})
