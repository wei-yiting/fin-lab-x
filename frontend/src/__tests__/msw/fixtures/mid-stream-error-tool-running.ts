import type { SSEStreamFixture } from './types'

const fixture: SSEStreamFixture = {
  description: 'Tool running then error arrives (tool never gets output)',
  scenarios: ['S-err-07'],
  chunks: [
    { data: { type: 'start', messageId: 'asst-err-tool' } },
    { data: { type: 'tool-input-available', toolCallId: 'tc-running', toolName: 'yfinance_quote', input: { ticker: 'NVDA' } } },
    { delayMs: 50, data: { type: 'text-start', id: 't1' } },
    { data: { type: 'text-delta', id: 't1', delta: 'Looking up NVDA...' } },
    { delayMs: 50, data: { type: 'error', errorText: 'context overflow' } },
    { data: { type: 'finish' } },
  ],
}
export default fixture
