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

// Mock navigation
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'test-resume-id' })
  }
})

describe('ProcessingPage', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
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

  it('renders all stages with pending status initially', () => {
    render(
      <BrowserRouter>
        <ProcessingPage />
      </BrowserRouter>
    )

    // All stages should show 0% initially
    const percentages = screen.getAllByText('0%')
    expect(percentages).toHaveLength(3)
  })
})
