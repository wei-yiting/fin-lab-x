import { describe, test, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AssistantMessage } from '../AssistantMessage'

describe('AssistantMessage — parts dispatch', () => {
  test('TC-comp-assistant-01: renders text part as Markdown', () => {
    const message = {
      id: 'a1',
      role: 'assistant' as const,
      parts: [{ type: 'text' as const, text: 'hello **world**' }],
    }
    render(<AssistantMessage message={message} isLast={false} abortedTools={new Set()} toolProgress={{}} />)
    expect(screen.getByText(/hello/)).toBeInTheDocument()
  })

  test('TC-comp-assistant-01: renders tool part as ToolCard', () => {
    const message = {
      id: 'a1',
      role: 'assistant' as const,
      parts: [
        { type: 'tool' as const, state: 'input-available', toolCallId: 'tc-1', toolName: 'yfinance', input: {} },
      ],
    }
    render(<AssistantMessage message={message} isLast={false} abortedTools={new Set()} toolProgress={{}} />)
    expect(screen.getByTestId('tool-card')).toBeInTheDocument()
  })

  test('TC-comp-assistant-01: renders error part as inline ErrorBlock', () => {
    const message = {
      id: 'a1',
      role: 'assistant' as const,
      parts: [
        { type: 'text' as const, text: 'partial...' },
        { type: 'error' as const, errorText: 'context overflow' },
      ],
    }
    render(<AssistantMessage message={message} isLast={false} abortedTools={new Set()} toolProgress={{}} />)
    expect(screen.getByTestId('inline-error-block')).toBeInTheDocument()
    expect(screen.getByText(/partial/)).toBeInTheDocument()
  })

  test('TC-comp-assistant-01: renders parallel tool parts in arrival order, stable', () => {
    const message = {
      id: 'a1',
      role: 'assistant' as const,
      parts: [
        { type: 'tool' as const, state: 'output-available', toolCallId: 'tc-A', toolName: 'a', input: {}, output: {} },
        { type: 'tool' as const, state: 'input-available', toolCallId: 'tc-B', toolName: 'b', input: {} },
      ],
    }
    const { container } = render(
      <AssistantMessage message={message} isLast={false} abortedTools={new Set()} toolProgress={{}} />
    )
    const cards = container.querySelectorAll('[data-testid="tool-card"]')
    expect(cards).toHaveLength(2)
    expect(cards[0]).toHaveAttribute('data-tool-call-id', 'tc-A')
    expect(cards[1]).toHaveAttribute('data-tool-call-id', 'tc-B')
  })
})

describe('AssistantMessage — aborted tools', () => {
  test('TC-comp-assistant-02: input-available tool with id in abortedTools → ToolCard data-tool-state="aborted"', () => {
    const message = {
      id: 'a1',
      role: 'assistant' as const,
      parts: [
        { type: 'tool' as const, state: 'input-available', toolCallId: 'tc-aborted', toolName: 'x', input: {} },
      ],
    }
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        abortedTools={new Set(['tc-aborted'])}
        toolProgress={{}}
      />
    )
    expect(screen.getByTestId('tool-card')).toHaveAttribute('data-tool-state', 'aborted')
  })

  test('TC-comp-assistant-02: output-available tool not affected by abortedTools', () => {
    const message = {
      id: 'a1',
      role: 'assistant' as const,
      parts: [
        { type: 'tool' as const, state: 'output-available', toolCallId: 'tc-done', toolName: 'x', input: {}, output: {} },
      ],
    }
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        abortedTools={new Set(['tc-done'])}
        toolProgress={{}}
      />
    )
    expect(screen.getByTestId('tool-card')).toHaveAttribute('data-tool-state', 'output-available')
  })
})

describe('AssistantMessage — RegenerateButton visibility', () => {
  const baseMsg = {
    id: 'a1',
    role: 'assistant' as const,
    parts: [{ type: 'text' as const, text: 'done' }],
  }

  test('TC-comp-assistant-03: isLast=true and status=ready → button visible', () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
        onRegenerate={vi.fn()}
      />
    )
    expect(screen.getByTestId('regenerate-btn')).toBeInTheDocument()
  })

  test('TC-comp-assistant-03: isLast=true but status=streaming → button hidden', () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isLast={true}
        status="streaming"
        abortedTools={new Set()}
        toolProgress={{}}
      />
    )
    expect(screen.queryByTestId('regenerate-btn')).not.toBeInTheDocument()
  })

  test('TC-comp-assistant-03: isLast=false → button hidden regardless of status', () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isLast={false}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />
    )
    expect(screen.queryByTestId('regenerate-btn')).not.toBeInTheDocument()
  })
})
