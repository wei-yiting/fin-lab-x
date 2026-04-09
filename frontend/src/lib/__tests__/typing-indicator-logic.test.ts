import { describe, test, expect } from 'vitest'
import { shouldShowTypingIndicator } from '../typing-indicator-logic'

describe('shouldShowTypingIndicator — truth table', () => {
  type Case = {
    name: string
    status: 'submitted' | 'streaming' | 'ready' | 'error'
    lastMessage: { role: 'user' | 'assistant'; parts: Record<string, unknown>[] } | null
    expected: boolean
  }

  const cases: Case[] = [
    {
      name: 'submitted, no last message → show',
      status: 'submitted',
      lastMessage: null,
      expected: true,
    },
    {
      name: 'submitted, last is user → show',
      status: 'submitted',
      lastMessage: { role: 'user', parts: [{ type: 'text', text: 'q' }] },
      expected: true,
    },
    {
      name: 'streaming, last assistant has no rendered part → show',
      status: 'streaming',
      lastMessage: { role: 'assistant', parts: [] },
      expected: true,
    },
    {
      name: 'streaming, last assistant has text part → hide',
      status: 'streaming',
      lastMessage: { role: 'assistant', parts: [{ type: 'text', text: 'hi' }] },
      expected: false,
    },
    {
      name: 'streaming, last assistant has tool part → hide',
      status: 'streaming',
      lastMessage: {
        role: 'assistant',
        parts: [{ type: 'tool', state: 'input-available', toolCallId: 'tc1' }],
      },
      expected: false,
    },
    {
      name: 'streaming, last assistant has only error part → hide (S-stream-07)',
      status: 'streaming',
      lastMessage: {
        role: 'assistant',
        parts: [{ type: 'error', errorText: 'oops' }],
      },
      expected: false,
    },
    {
      name: 'ready, last assistant complete → hide (S-stream-08)',
      status: 'ready',
      lastMessage: { role: 'assistant', parts: [{ type: 'text', text: 'done' }] },
      expected: false,
    },
    {
      name: 'error → hide',
      status: 'error',
      lastMessage: null,
      expected: false,
    },
  ]

  test.each(cases)('$name', ({ status, lastMessage, expected }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
    expect(shouldShowTypingIndicator({ status, lastMessage: lastMessage as any })).toBe(expected)
  })
})
