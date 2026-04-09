import { describe, test, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorBlock } from '../ErrorBlock'

describe('ErrorBlock', () => {
  test('displays friendly title only, raw detail hidden by default', () => {
    render(
      <ErrorBlock
        friendly={{
          title: 'The system is busy. Please try again in a moment.',
          detail: 'HTTP 409: session busy on backend',
          retriable: true,
        }}
        onRetry={vi.fn()}
        source="pre-stream"
        errorClass="pre-stream-409"
      />
    )

    expect(screen.getByTestId('error-title')).toHaveTextContent(
      'The system is busy. Please try again in a moment.'
    )
    expect(screen.queryByText('HTTP 409: session busy on backend')).not.toBeInTheDocument()
  })

  test('clicking show-details toggle reveals raw detail', async () => {
    const user = userEvent.setup()
    render(
      <ErrorBlock
        friendly={{ title: 'Server error.', detail: 'stack trace ...', retriable: true }}
        onRetry={vi.fn()}
        source="pre-stream"
        errorClass="pre-stream-500"
      />
    )

    await user.click(screen.getByTestId('error-detail-toggle'))
    expect(screen.getByTestId('error-raw-detail')).toHaveTextContent('stack trace ...')
  })

  test('Retry button hidden when retriable=false', () => {
    render(
      <ErrorBlock
        friendly={{
          title: 'Conversation not found. Refresh to start a new one.',
          retriable: false,
        }}
        onRetry={vi.fn()}
        source="pre-stream"
        errorClass="pre-stream-404"
      />
    )
    expect(screen.queryByTestId('error-retry-btn')).not.toBeInTheDocument()
  })

  test('long detail (>200 chars) is truncated with show-more affordance', async () => {
    const user = userEvent.setup()
    const longDetail = 'x'.repeat(500)
    render(
      <ErrorBlock
        friendly={{ title: 'Server error.', detail: longDetail, retriable: true }}
        onRetry={vi.fn()}
        source="pre-stream"
        errorClass="pre-stream-500"
      />
    )

    await user.click(screen.getByTestId('error-detail-toggle'))
    const detail = screen.getByTestId('error-raw-detail')
    expect(detail.textContent!.length).toBeLessThan(longDetail.length)
  })
})
