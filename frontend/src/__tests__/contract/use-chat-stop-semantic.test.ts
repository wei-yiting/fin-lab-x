// NOTE: Vitest config has globals: false → import test/expect/lifecycle hooks explicitly.
// NOTE: DefaultChatTransport is exported from `ai`, not `@ai-sdk/react`.
import { test, expect, beforeAll, afterAll } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { setupServer } from 'msw/node'
import { http, HttpResponse, delay } from 'msw'

const server = setupServer(
  http.post('/api/v1/chat', async () => {
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder()
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ type: 'start', messageId: 'a1' })}\n\n`),
        )
        await delay(100)
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ type: 'text-start', id: 't1' })}\n\n`),
        )
        await delay(100)
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ type: 'text-delta', id: 't1', textDelta: 'hello' })}\n\n`,
          ),
        )
        // Long delay to give test time to call stop()
        await delay(5000)
        controller.close()
      },
    })
    return new HttpResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'x-vercel-ai-ui-message-stream': 'v1',
      },
    })
  }),
)

beforeAll(() => server.listen())
afterAll(() => server.close())

test('V-3: stop() transitions status to ready, not error', async () => {
  const transport = new DefaultChatTransport({ api: '/api/v1/chat' })
  const { result } = renderHook(() => useChat({ transport, id: 'test' }))

  await act(async () => {
    result.current.sendMessage({ text: 'long question' })
  })

  await waitFor(() => expect(result.current.status).toBe('streaming'))

  await act(async () => {
    await result.current.stop()
  })

  await waitFor(() => expect(result.current.status).toBe('ready'))
  // NOTE: AI SDK v6 types `useChat().error` as `Error | undefined`, not `Error | null`.
  // The verbatim plan snippet used `.toBeNull()` which fails on a clean abort.
  // Contract intent: "no error after stop()" — assert undefined (and falsy as belt+braces).
  expect(result.current.error).toBeUndefined()
  expect(result.current.error).toBeFalsy()
})
