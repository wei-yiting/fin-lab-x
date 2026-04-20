import type { SSEStreamFixture } from './types'

const fixture: SSEStreamFixture = {
  description: 'Inline markdown links with javascript:/mailto:/https: — security guard test for body links (no ref defs)',
  scenarios: ['S-md-03-inline'],
  chunks: [
    { delayMs: 0,   data: { type: 'start', messageId: 'asst-xss-inline-1' } },
    { delayMs: 30,  data: { type: 'text-start', id: 't1' } },
    { delayMs: 80,  data: { type: 'text-delta', id: 't1', delta: "Visit [bad site](javascript:alert('xss')) and [mail link](mailto:x@y.com) and [safe](https://example.com)." } },
    { delayMs: 130, data: { type: 'text-end', id: 't1' } },
    { delayMs: 180, data: { type: 'finish' } },
  ],
}

export default fixture
