import { createClient, type AuthChangeEvent, type Session } from '@supabase/supabase-js'
import { clearOAuthErrorFromUrl, localAuthRedirect, oauthCallbackOutcome } from './auth-utils'

const projectUrl = import.meta.env.VITE_SUPABASE_URL?.trim().replace(/\/$/, '')
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY?.trim()
const applicationOrigin = import.meta.env.VITE_APPLICATION_ORIGIN?.trim()

function validProjectUrl(value: string | undefined): value is string {
  if (!value) return false
  try {
    const url = new URL(value)
    return url.protocol === 'https:'
      && url.port === ''
      && url.pathname === '/'
      && !url.username
      && !url.password
      && url.hostname !== 'supabase.co'
      && url.hostname.endsWith('.supabase.co')
  } catch {
    return false
  }
}

export const frontendAuthConfigured = validProjectUrl(projectUrl) && Boolean(publishableKey)

export const supabase = frontendAuthConfigured
  ? createClient(projectUrl, publishableKey!, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
        flowType: 'implicit',
      },
    })
  : null

export async function restoreSession(): Promise<Session | null> {
  if (!supabase) return null
  const { data, error } = await supabase.auth.getSession()
  if (error) {
    await supabase.auth.signOut({ scope: 'local' })
    throw new Error('The saved sign-in session could not be restored. Please sign in again.')
  }
  let session = data.session
  if (session?.expires_at && session.expires_at * 1000 <= Date.now() + 30_000) {
    const refreshed = await supabase.auth.refreshSession()
    if (refreshed.error || !refreshed.data.session) {
      await supabase.auth.signOut({ scope: 'local' })
      return null
    }
    session = refreshed.data.session
  }
  return session
}

export function subscribeToAuth(
  callback: (event: AuthChangeEvent, session: Session | null) => void,
): () => void {
  if (!supabase) return () => undefined
  const { data } = supabase.auth.onAuthStateChange(callback)
  return () => data.subscription.unsubscribe()
}

export async function signInWithGoogle(): Promise<void> {
  if (!supabase) throw new Error('Google sign-in is unavailable until Supabase public configuration is added.')
  const redirectTo = localAuthRedirect(window.location.origin, applicationOrigin)
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo },
  })
  if (error) throw new Error('Google sign-in could not start. Check the Supabase provider configuration.')
}

export async function signOut(): Promise<void> {
  if (!supabase) return
  const { error } = await supabase.auth.signOut()
  if (error) {
    await supabase.auth.signOut({ scope: 'local' })
    throw new Error('The remote sign-out failed. This browser session was cleared locally.')
  }
}

export async function clearLocalSession(): Promise<void> {
  if (supabase) await supabase.auth.signOut({ scope: 'local' })
}

export async function getAccessToken(required = false): Promise<string | null> {
  const session = await restoreSession()
  if (!session && required) {
    throw new Error('Sign in with Google before starting or changing a live review.')
  }
  return session?.access_token ?? null
}

export function readOAuthOutcome(): ReturnType<typeof oauthCallbackOutcome> {
  return oauthCallbackOutcome(window.location.href)
}

export { clearOAuthErrorFromUrl }
