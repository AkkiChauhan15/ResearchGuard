export const LOCAL_AUTH_ORIGINS = new Set([
  'http://127.0.0.1:5173',
  'http://localhost:5173',
  'http://127.0.0.1:8000',
  'http://localhost:8000',
])

function exactHostedOrigin(value: string): string {
  const parsed = new URL(value)
  if (
    parsed.origin !== value
    || parsed.protocol !== 'https:'
    || parsed.username
    || parsed.password
    || parsed.pathname !== '/'
    || parsed.search
    || parsed.hash
  ) {
    throw new Error('VITE_APPLICATION_ORIGIN must be one exact HTTPS origin without a path.')
  }
  return parsed.origin
}

export function localAuthRedirect(origin: string, configuredHostedOrigin?: string): string {
  let parsed: URL
  try {
    parsed = new URL(origin)
  } catch {
    throw new Error('Google sign-in is limited to the configured application origins.')
  }
  let hostedOrigin: string | null = null
  if (configuredHostedOrigin?.trim()) hostedOrigin = exactHostedOrigin(configuredHostedOrigin.trim())
  if (
    parsed.origin !== origin
    || (!LOCAL_AUTH_ORIGINS.has(parsed.origin) && parsed.origin !== hostedOrigin)
  ) {
    throw new Error('Google sign-in is limited to the configured application origins.')
  }
  return `${parsed.origin}/`
}

export interface OAuthCallbackOutcome {
  kind: 'cancelled' | 'failed'
  message: string
}

export function oauthCallbackOutcome(href: string): OAuthCallbackOutcome | null {
  const url = new URL(href)
  const query = url.searchParams
  const fragment = new URLSearchParams(url.hash.startsWith('#') ? url.hash.slice(1) : url.hash)
  const error = query.get('error') || fragment.get('error')
  const errorCode = query.get('error_code') || fragment.get('error_code') || error
  if (!errorCode) return null
  if (errorCode === 'access_denied' || errorCode === 'user_cancelled') {
    return {
      kind: 'cancelled',
      message: 'Google sign-in was cancelled. You remain signed out.',
    }
  }
  return {
    kind: 'failed',
    message: 'Google sign-in did not complete. Check the Supabase and Google OAuth configuration, then try again.',
  }
}

export function clearOAuthErrorFromUrl(): void {
  const url = new URL(window.location.href)
  const fragment = new URLSearchParams(url.hash.startsWith('#') ? url.hash.slice(1) : url.hash)
  if (
    url.searchParams.has('error')
    || url.searchParams.has('error_code')
    || fragment.has('error')
    || fragment.has('error_code')
  ) {
    window.history.replaceState({}, document.title, url.pathname)
  }
}
