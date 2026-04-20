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

  test('TC-comp-assistant-01: mid-stream ErrorBlock retry calls onRegenerate with message id', async () => {
    const userEvent = (await import('@testing-library/user-event')).default
    const user = userEvent.setup()
    const onRegenerate = vi.fn()
    const message = {
      id: 'assistant-xyz',
      role: 'assistant' as const,
      parts: [
        { type: 'text' as const, text: 'partial...' },
        { type: 'error' as const, errorText: 'context overflow' },
      ],
    }
    render(
      <AssistantMessage
        message={message}
        isLast={true}
        status="error"
        abortedTools={new Set()}
        toolProgress={{}}
        onRegenerate={onRegenerate}
      />,
    )
    const retryBtn = screen.getByTestId('error-retry-btn')
    await user.click(retryBtn)
    expect(onRegenerate).toHaveBeenCalledTimes(1)
    expect(onRegenerate).toHaveBeenCalledWith('assistant-xyz')
  })

  test('TC-comp-assistant-01: mid-stream ErrorBlock hides Retry when not last message', () => {
    const message = {
      id: 'a1',
      role: 'assistant' as const,
      parts: [
        { type: 'text' as const, text: 'partial...' },
        { type: 'error' as const, errorText: 'context overflow' },
      ],
    }
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        status="error"
        abortedTools={new Set()}
        toolProgress={{}}
        onRegenerate={vi.fn()}
      />,
    )
    expect(screen.queryByTestId('error-retry-btn')).not.toBeInTheDocument()
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

  test('TC-comp-assistant-02: input-streaming tool with id in abortedTools → ToolCard data-tool-state="aborted"', () => {
    const message = {
      id: 'a1',
      role: 'assistant' as const,
      parts: [
        { type: 'tool' as const, state: 'input-streaming', toolCallId: 'tc-aborted-streaming', toolName: 'x', input: {} },
      ],
    }
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        abortedTools={new Set(['tc-aborted-streaming'])}
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

describe('AssistantMessage — citation rendering', () => {
  const commonMarkText =
    'Analysis shows growth [1] and stability [2].\n\n' +
    '[1]: https://reuters.com/report "Reuters Report"\n' +
    '[2]: https://bloomberg.com/article'

  const commonMarkMsg = {
    id: 'a1',
    role: 'assistant' as const,
    parts: [{ type: 'text' as const, text: commonMarkText }],
  }

  test('TC-comp-citation-01: CommonMark citations render as RefSup after streaming', () => {
    render(
      <AssistantMessage
        message={commonMarkMsg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    )
    const refSups = screen.getAllByTestId('ref-sup')
    expect(refSups).toHaveLength(2)
    expect(refSups[0]).toHaveAttribute('data-ref-label', '1')
    expect(refSups[1]).toHaveAttribute('data-ref-label', '2')

    expect(screen.getByTestId('sources-block')).toBeInTheDocument()
    expect(screen.getByText('Reuters Report')).toBeInTheDocument()
    expect(screen.getByText('bloomberg.com')).toBeInTheDocument()
  })

  test('TC-comp-citation-02: no RefSup or Sources block during streaming', () => {
    render(
      <AssistantMessage
        message={commonMarkMsg}
        isLast={true}
        status="streaming"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    )
    expect(screen.queryByTestId('ref-sup')).not.toBeInTheDocument()
    expect(screen.queryByTestId('sources-block')).not.toBeInTheDocument()
  })

  test('TC-comp-citation-03: fallback format — [N] URL + full-width【N】inline', () => {
    const fallbackText =
      '最新報導顯示成長【1】，Bloomberg 確認趨勢【2】。\n\n' +
      '**References**\n' +
      '[1] https://reuters.com/report\n' +
      '[2] https://bloomberg.com/analysis'

    const fallbackMsg = {
      id: 'a2',
      role: 'assistant' as const,
      parts: [{ type: 'text' as const, text: fallbackText }],
    }

    render(
      <AssistantMessage
        message={fallbackMsg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    )
    const refSups = screen.getAllByTestId('ref-sup')
    expect(refSups).toHaveLength(2)

    expect(screen.getByTestId('sources-block')).toBeInTheDocument()
    expect(screen.queryByText('**References**')).not.toBeInTheDocument()
  })

  test('TC-comp-citation-04: streaming strips definition lines (no flicker)', () => {
    const streamingText =
      'NVDA 很棒 [1]。\n\n' +
      '[1]: https://reuters.com/report "Reuters"'

    const msg = {
      id: 'a3',
      role: 'assistant' as const,
      parts: [{ type: 'text' as const, text: streamingText }],
    }

    render(
      <AssistantMessage
        message={msg}
        isLast={true}
        status="streaming"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    )
    expect(screen.queryByText(/reuters\.com\/report/)).not.toBeInTheDocument()
    expect(screen.queryByTestId('sources-block')).not.toBeInTheDocument()
  })

  test('TC-comp-citation-05: bullet-prefixed ref defs render Sources block', () => {
    const bulletText =
      'NVDA news [1].\n\n' +
      '- [1]: https://reuters.com/nvda "Reuters NVDA"'

    const msg = {
      id: 'a4',
      role: 'assistant' as const,
      parts: [{ type: 'text' as const, text: bulletText }],
    }

    render(
      <AssistantMessage
        message={msg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    )
    expect(screen.getByTestId('sources-block')).toBeInTheDocument()
    expect(screen.queryByText(/- \[1\]/)).not.toBeInTheDocument()
  })

  test('TC-comp-citation-06: Chinese source header stripped', () => {
    const cnText =
      '報告內容 [1]。\n\n' +
      '來源：\n' +
      '[1]: https://reuters.com/report "Reuters"'

    const msg = {
      id: 'a5',
      role: 'assistant' as const,
      parts: [{ type: 'text' as const, text: cnText }],
    }

    render(
      <AssistantMessage
        message={msg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    )
    expect(screen.queryByText('來源：')).not.toBeInTheDocument()
    expect(screen.getByTestId('sources-block')).toBeInTheDocument()
  })
})
