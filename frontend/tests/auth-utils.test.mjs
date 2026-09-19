import assert from 'node:assert/strict'
import test from 'node:test'

import { localAuthRedirect, oauthCallbackOutcome } from '../src/auth-utils.ts'

test('localAuthRedirect accepts only the four configured local application origins', () => {
  assert.equal(localAuthRedirect('http://127.0.0.1:5173'), 'http://127.0.0.1:5173/')
  assert.equal(localAuthRedirect('http://localhost:8000'), 'http://localhost:8000/')
  for (const origin of [
    'https://127.0.0.1:5173',
    'http://127.0.0.1:4173',
    'http://localhost:5173.evil.example',
    'http://localhost:5173/callback',
  ]) {
    assert.throws(() => localAuthRedirect(origin), /configured local application origins/)
  }
})

test('OAuth callback errors distinguish cancellation from provider failure', () => {
  assert.deepEqual(
    oauthCallbackOutcome('http://127.0.0.1:5173/#error=access_denied'),
    { kind: 'cancelled', message: 'Google sign-in was cancelled. You remain signed out.' },
  )
  assert.equal(
    oauthCallbackOutcome('http://127.0.0.1:5173/?error=server_error')?.kind,
    'failed',
  )
  assert.equal(oauthCallbackOutcome('http://127.0.0.1:5173/'), null)
})
