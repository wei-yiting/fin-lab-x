import type { SSEFixture } from './types'
import xssJavascriptUrl from './xss-javascript-url'
import duplicateReferences from './duplicate-references'
import midStreamErrorAfterText from './mid-stream-error-after-text'
import preStream409 from './pre-stream-409'
import preStreamNetworkOffline from './pre-stream-network-offline'
import happyText from './happy-text'
import happyToolThenText from './happy-tool-then-text'
import preStream500 from './pre-stream-500'
import preStream422Regenerate from './pre-stream-422-regenerate'
import longTextStream from './long-text-stream'
import midStreamErrorToolRunning from './mid-stream-error-tool-running'
import slowStartStream from './slow-start-stream'

export const fixtures: Record<string, SSEFixture> = {
  'xss-javascript-url': xssJavascriptUrl,
  'duplicate-references': duplicateReferences,
  'mid-stream-error-after-text': midStreamErrorAfterText,
  'pre-stream-409': preStream409,
  'pre-stream-network-offline': preStreamNetworkOffline,
  'happy-text': happyText,
  'happy-tool-then-text': happyToolThenText,
  'pre-stream-500': preStream500,
  'pre-stream-422-regenerate': preStream422Regenerate,
  'long-text-stream': longTextStream,
  'mid-stream-error-tool-running': midStreamErrorToolRunning,
  'slow-start-stream': slowStartStream,
}
