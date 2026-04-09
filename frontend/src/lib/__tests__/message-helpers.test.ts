import { describe, test, expect } from 'vitest'
import { findOriginalUserText } from '../message-helpers'
import type { UIMessage } from '@ai-sdk/react'

const makeMsg = (id: string, role: 'user' | 'assistant', text: string): UIMessage => ({
  id,
  role,
  parts: [{ type: 'text', text }],
})

describe('findOriginalUserText', () => {
  test('returns text of the user message immediately before assistant', () => {
    const messages = [
      makeMsg('u1', 'user', 'first question'),
      makeMsg('a1', 'assistant', 'first answer'),
      makeMsg('u2', 'user', 'second question'),
      makeMsg('a2', 'assistant', 'second answer'),
    ]
    expect(findOriginalUserText(messages, 'a2')).toBe('second question')
    expect(findOriginalUserText(messages, 'a1')).toBe('first question')
  })

  test('returns empty string if assistantMessageId not found', () => {
    expect(findOriginalUserText([], 'nonexistent')).toBe('')
  })

  test('returns empty string if message before is not user role', () => {
    const messages = [
      makeMsg('a1', 'assistant', 'orphan'),
    ]
    expect(findOriginalUserText(messages, 'a1')).toBe('')
  })
})
