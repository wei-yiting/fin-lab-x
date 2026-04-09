import { http, HttpResponse, delay } from 'msw'
import type { SSEStreamFixture, SingleFixture } from './fixtures/types'
import { fixtures } from './fixtures'

function isStreamFixture(f: unknown): f is SSEStreamFixture {
  return typeof f === 'object' && f !== null && 'chunks' in f
}

const requestCounts = new Map<string, number>()

export const handlers = [
  http.post('/api/v1/chat', async ({ request }) => {
    const refererUrl = new URL(request.headers.get('referer') ?? globalThis.location.href)
    const fixtureName = refererUrl.searchParams.get('msw_fixture') ?? 'happy-text'

    const fixture = fixtures[fixtureName]
    if (!fixture) {
      return HttpResponse.json(
        { error: `unknown fixture: ${fixtureName}` },
        { status: 500 }
      )
    }

    let resolved: SingleFixture
    if ('responses' in fixture) {
      const count = requestCounts.get(fixtureName) ?? 0
      requestCounts.set(fixtureName, count + 1)
      resolved = fixture.responses[Math.min(count, fixture.responses.length - 1)]
    } else {
      resolved = fixture
    }

    if ('preStreamError' in resolved) {
      return new HttpResponse(resolved.preStreamError.body ?? null, {
        status: resolved.preStreamError.status,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    if ('networkFailure' in resolved && resolved.networkFailure) {
      return HttpResponse.error()
    }

    if (!isStreamFixture(resolved)) {
      return HttpResponse.json(
        { error: `invalid fixture shape: ${fixtureName}` },
        { status: 500 }
      )
    }

    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      async start(controller) {
        const onAbort = () => {
          try {
            controller.close()
          } catch {
            /* already closed */
          }
        }
        request.signal.addEventListener('abort', onAbort, { once: true })

        try {
          for (const chunk of resolved.chunks) {
            if (chunk.delayMs) await delay(chunk.delayMs)
            if (request.signal.aborted) return
            const frame = `data: ${JSON.stringify(chunk.data)}\n\n`
            controller.enqueue(encoder.encode(frame))
          }
          if (!resolved.dropConnectionBeforeEnd) {
            controller.close()
          } else {
            controller.error(new Error('simulated connection drop'))
          }
        } catch (err) {
          controller.error(err)
        }
      },
    })

    return new HttpResponse(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'x-vercel-ai-ui-message-stream': 'v1',
        'Cache-Control': 'no-cache',
      },
    })
  }),
]
