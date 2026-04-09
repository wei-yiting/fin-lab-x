import type { PreStreamErrorFixture } from './types'

const fixture: PreStreamErrorFixture = {
  description: 'HTTP 409 session busy — pre-stream error',
  scenarios: ['S-err-01 (row 3: 409 session busy)'],
  preStreamError: {
    status: 409,
    body: JSON.stringify({ error: 'session busy' }),
  },
}

export default fixture
