import type { SequentialFixture, SSEStreamFixture, PreStreamErrorFixture } from './types'

const initialResponse: SSEStreamFixture = {
  description: 'Initial assistant response',
  scenarios: [],
  chunks: [
    { data: { type: 'start', messageId: 'asst-initial-1' } },
    { data: { type: 'text-start', id: 't1' } },
    { data: { type: 'text-delta', id: 't1', delta: 'Original response.' } },
    { data: { type: 'text-end', id: 't1' } },
    { data: { type: 'finish' } },
  ],
}

const regenerateError: PreStreamErrorFixture = {
  description: 'Regenerate fails with 500',
  scenarios: [],
  preStreamError: { status: 500, body: JSON.stringify({ error: 'Internal server error' }) },
}

const retryResponse: SSEStreamFixture = {
  description: 'Retry succeeds with new response',
  scenarios: [],
  chunks: [
    { data: { type: 'start', messageId: 'asst-retry-1' } },
    { data: { type: 'text-start', id: 't2' } },
    { data: { type: 'text-delta', id: 't2', delta: 'Retried response.' } },
    { data: { type: 'text-end', id: 't2' } },
    { data: { type: 'finish' } },
  ],
}

const fixture: SequentialFixture = {
  description: 'Initial success, regenerate fails with 500, retry succeeds',
  scenarios: ['J-regen-retry-01'],
  responses: [initialResponse, regenerateError, retryResponse],
}
export default fixture
