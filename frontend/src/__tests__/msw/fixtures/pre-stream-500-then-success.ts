import type { SequentialFixture } from './types'
import preStream500 from './pre-stream-500'
import happyText from './happy-text'

const fixture: SequentialFixture = {
  description: 'First request returns HTTP 500, second returns happy-text stream',
  scenarios: ['S-err-02', 'TC-e2e-smoke-error-01'],
  responses: [preStream500, happyText],
}
export default fixture
