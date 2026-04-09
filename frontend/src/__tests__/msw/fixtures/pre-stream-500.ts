import type { PreStreamErrorFixture } from './types'

const fixture: PreStreamErrorFixture = {
  description: 'HTTP 500 server error',
  scenarios: ['S-err-01'],
  preStreamError: { status: 500, body: JSON.stringify({ error: 'Internal server error' }) },
}
export default fixture
