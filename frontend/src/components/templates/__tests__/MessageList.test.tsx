import { describe, test, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MessageList } from '../MessageList'

describe('MessageList — TypingIndicator visibility', () => {
  test('TC-comp-typing-02: transient data-tool-progress does not hide TypingIndicator', () => {
    const { rerender } = render(
      <MessageList
        messages={[{ id: 'u1', role: 'user', parts: [{ type: 'text', text: 'q' }] }]}
        status="streaming"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
      />
    )

    expect(screen.getByTestId('typing-indicator')).toBeInTheDocument()

    rerender(
      <MessageList
        messages={[{ id: 'u1', role: 'user', parts: [{ type: 'text', text: 'q' }] }]}
        status="streaming"
        toolProgress={{ 'tc-1': 'fetching...' }}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
      />
    )

    expect(screen.getByTestId('typing-indicator')).toBeInTheDocument()
    expect(screen.queryByTestId('tool-card')).not.toBeInTheDocument()
  })

  test('empty messages with ready status renders empty content', () => {
    render(
      <MessageList
        messages={[]}
        status="ready"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
        emptyContent={<div data-testid="empty-state">Empty</div>}
      />
    )

    expect(screen.getByTestId('empty-state')).toBeInTheDocument()
  })
})
