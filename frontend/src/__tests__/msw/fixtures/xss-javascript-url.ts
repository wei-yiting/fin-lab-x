import type { SSEStreamFixture } from './types'

const fixture: SSEStreamFixture = {
  description: 'Markdown contains javascript: URL — security guard test',
  scenarios: ['S-md-03'],
  chunks: [
    { delayMs: 0,   data: { type: 'start', messageId: 'asst-xss-1' } },
    { delayMs: 30,  data: { type: 'text-start', id: 't1' } },
    { delayMs: 80,  data: { type: 'text-delta', id: 't1', delta: 'See [1] for the report.\n\n' } },
    { delayMs: 130, data: { type: 'text-delta', id: 't1', delta: '[1]: javascript:alert("XSS") "Click me"\n' } },
    { delayMs: 180, data: { type: 'text-delta', id: 't1', delta: '[2]: mailto:ir@nvidia.com "Contact IR"\n' } },
    { delayMs: 230, data: { type: 'text-end', id: 't1' } },
    { delayMs: 280, data: { type: 'finish' } },
  ],
}

export default fixture
