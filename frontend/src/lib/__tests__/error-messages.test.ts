import { describe, test, expect } from 'vitest'
import { toFriendlyError, type ErrorContext } from '../error-messages'

describe('toFriendlyError — pre-stream HTTP errors', () => {
  test.each([
    [422, "Couldn't regenerate that message. Please try again.", true],
    [404, 'Conversation not found. Refresh to start a new one.', false],
    [409, 'The system is busy. Please try again in a moment.', true],
    [500, 'Server error. Please try again.', true],
    [503, 'Something went wrong. Please try again.', true],
  ])('status %d → "%s" (retriable: %s)', (status, expectedTitle, expectedRetriable) => {
    const result = toFriendlyError({ source: 'pre-stream-http', status })
    expect(result.title).toBe(expectedTitle)
    expect(result.retriable).toBe(expectedRetriable)
  })
})

test('network failure → connection-lost message', () => {
  const result = toFriendlyError({
    source: 'network',
    rawMessage: 'Failed to fetch',
  })
  expect(result.title).toBe('Connection lost. Check your network and try again.')
  expect(result.retriable).toBe(true)
  expect(result.detail).toBe('Failed to fetch')
})

describe('toFriendlyError — tool-output-error pattern matching', () => {
  test.each([
    ['API rate limit exceeded', 'Too many requests. Please wait a moment and try again.', true],
    ['ticker not found', "We couldn't find that data.", false],
    ['Connection timeout after 30s', 'The tool timed out. Please try again.', true],
    ['Permission denied (403)', 'Access denied for this resource.', false],
    ['Some unknown error', 'The tool failed to run. Please try again.', true],
  ])('rawMessage "%s" → "%s"', (rawMessage, expectedTitle, expectedRetriable) => {
    const result = toFriendlyError({
      source: 'tool-output-error',
      rawMessage,
    })
    expect(result.title).toBe(expectedTitle)
    expect(result.retriable).toBe(expectedRetriable)
    expect(result.detail).toBe(rawMessage)
  })
})

describe('toFriendlyError — mid-stream-sse pattern matching', () => {
  test.each([
    ['context length exceeded', 'This conversation is too long. Start a new chat to continue.', false],
    ['token limit reached', 'This conversation is too long. Start a new chat to continue.', false],
    ['rate limit', 'The system is busy. Please try again in a moment.', true],
    ['Unknown stream error', 'Something went wrong while generating the response. Please try again.', true],
  ])('mid-stream rawMessage "%s" → "%s"', (rawMessage, expectedTitle, expectedRetriable) => {
    const result = toFriendlyError({
      source: 'mid-stream-sse',
      rawMessage,
    })
    expect(result.title).toBe(expectedTitle)
    expect(result.retriable).toBe(expectedRetriable)
  })
})

describe('toFriendlyError — invariants', () => {
  test('title is always English ASCII (no Chinese characters)', () => {
    const cases: ErrorContext[] = [
      { source: 'pre-stream-http', status: 422 },
      { source: 'pre-stream-http', status: 999 },
      { source: 'network' },
      { source: 'tool-output-error', rawMessage: 'random error' },
      { source: 'mid-stream-sse', rawMessage: 'random' },
    ]
    for (const ctx of cases) {
      const result = toFriendlyError(ctx)
      expect(result.title).toMatch(/^[\x20-\x7E]+$/)
      expect(result.title.length).toBeLessThanOrEqual(80)
      expect(result.title.length).toBeGreaterThan(0)
    }
  })

  test('detail is set only when rawMessage is provided', () => {
    expect(toFriendlyError({ source: 'pre-stream-http', status: 422 }).detail).toBeUndefined()
    expect(toFriendlyError({ source: 'pre-stream-http', status: 422, rawMessage: 'x' }).detail).toBe('x')
  })
})
