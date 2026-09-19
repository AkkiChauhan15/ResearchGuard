import assert from 'node:assert/strict'
import test from 'node:test'

import {
  applicationRedirect,
  localAuthRedirect,
  oauthCallbackOutcome,
  requestedInternalPath,
  safeInternalPath,
} from '../src/auth-utils.ts'

test('localAuthRedirect accepts only the four configured local application origins', () => {
  assert.equal(localAuthRedirect('http://127.0.0.1:5173'), 'http://127.0.0.1:5173/')
  assert.equal(localAuthRedirect('http://localhost:8000'), 'http://localhost:8000/')
  for (const origin of [
    'https://127.0.0.1:5173',
    'http://127.0.0.1:4173',
    'http://localhost:5173.evil.example',
    'http://localhost:5173/callback',
  ]) {
    assert.throws(() => localAuthRedirect(origin), /configured application origins/)
  }
})

test('localAuthRedirect accepts only the exact configured hosted application origin', () => {
  const production = 'https://research-guard-ai.vercel.app'
  assert.equal(localAuthRedirect(production, production), `${production}/`)
  assert.throws(
    () => localAuthRedirect('https://preview-research-guard-ai.vercel.app', production),
    /configured application origins/,
  )
  assert.throws(
    () => localAuthRedirect(production, `${production}/callback`),
    /one exact HTTPS origin/,
  )
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

test('internal return paths reject external and ambiguous redirects', () => {
  assert.equal(safeInternalPath('/account?setup=1'), '/account?setup=1')
  assert.equal(requestedInternalPath('?next=%2Faccount'), '/account')
  for (const unsafe of [
    'https://evil.example/path',
    '//evil.example/path',
    '/\\evil.example/path',
    '/account#token',
  ]) {
    assert.equal(safeInternalPath(unsafe), '/')
  }
  assert.equal(requestedInternalPath('?next=https%3A%2F%2Fevil.example'), '/')
})

test('application redirects remain on an approved application origin', () => {
  assert.equal(
    applicationRedirect('http://127.0.0.1:5173', '/update-password'),
    'http://127.0.0.1:5173/update-password',
  )
  assert.equal(
    applicationRedirect(
      'https://research-guard-ai.vercel.app',
      '/account',
      'https://research-guard-ai.vercel.app',
    ),
    'https://research-guard-ai.vercel.app/account',
  )
})
