import type { PreStreamErrorFixture } from './types'

const fixture: PreStreamErrorFixture = {
  description: 'HTTP 422 on regenerate (messageId mismatch)',
  scenarios: ['S-err-04'],
  preStreamError: { status: 422, body: JSON.stringify({ error: 'last turn is not an assistant message' }) },
}
export default fixture
