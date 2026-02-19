import { render, screen } from '@testing-library/react'
import ProcessingStage from '../ProcessingStage'

describe('ProcessingStage', () => {
  it('renders stage name and progress percentage', () => {
    render(
      <ProcessingStage
        name="Text Extraction"
        status="pending"
        progress={0}
      />
    )

    expect(screen.getByText('Text Extraction')).toBeInTheDocument()
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('shows in-progress state correctly', () => {
    render(
      <ProcessingStage
        name="NLP Parsing"
        status="in_progress"
        progress={65}
      />
    )

    expect(screen.getByText('65%')).toBeInTheDocument()
  })

  it('shows complete state with checkmark', () => {
    render(
      <ProcessingStage
        name="AI Enhancement"
        status="complete"
        progress={100}
      />
    )

    expect(screen.getByText('100%')).toBeInTheDocument()
  })
})
