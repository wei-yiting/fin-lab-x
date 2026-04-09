import type { SSEStreamFixture } from './types'

const chunks: SSEStreamFixture['chunks'] = [
  { data: { type: 'start', messageId: 'asst-long' } },
  { data: { type: 'text-start', id: 't1' } },
]
for (let i = 0; i < 50; i++) {
  chunks.push({ data: { type: 'text-delta', id: 't1', delta: `Paragraph ${i}. This is a longer response that keeps streaming for testing stop behavior. ` } })
}
chunks.push({ data: { type: 'text-end', id: 't1' } })
chunks.push({ data: { type: 'finish' } })

const fixture: SSEStreamFixture = {
  description: 'Long text stream for stop behavior testing',
  scenarios: ['TC-e2e-stop-01'],
  chunks: chunks.map(c => ({ delayMs: 50, ...c })),
}
export default fixture
