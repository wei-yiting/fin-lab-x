import type { SSEFixture } from './types'
import xssJavascriptUrl from './xss-javascript-url'
import duplicateReferences from './duplicate-references'
import midStreamErrorAfterText from './mid-stream-error-after-text'
import preStream409 from './pre-stream-409'
import preStreamNetworkOffline from './pre-stream-network-offline'

export const fixtures: Record<string, SSEFixture> = {
  'xss-javascript-url': xssJavascriptUrl,
  'duplicate-references': duplicateReferences,
  'mid-stream-error-after-text': midStreamErrorAfterText,
  'pre-stream-409': preStream409,
  'pre-stream-network-offline': preStreamNetworkOffline,
}
