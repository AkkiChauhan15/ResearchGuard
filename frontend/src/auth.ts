import { createClient, type AuthChangeEvent, type Session } from '@supabase/supabase-js'
import {
  applicationRedirect,
  clearOAuthErrorFromUrl,
  localAuthRedirect,
  oauthCallbackOutcome,
  safeInternalPath,
} from './auth-utils'

const projectUrl = import.meta.env.VITE_SUPABASE_URL?.trim().replace(/\/$/, '')
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY?.trim()
const applicationOrigin = import.meta.env.VITE_APPLICATION_ORIGIN?.trim()
const configuredPasswordMinimum = Number.parseInt(
  import.meta.env.VITE_SUPABASE_PASSWORD_MIN_LENGTH ?? '6',
  10,
)
const AUTH_RETURN_KEY = 'researchguard.auth.return_path'

export const passwordMinimumLength = Number.isInteger(configuredPasswordMinimum)
  && configuredPasswordMinimum >= 6
  && configuredPasswordMinimum <= 128
  ? configuredPasswordMinimum
  : 6

export interface AuthCapabilities {
  email: boolean
  google: boolean
  signup: boolean
  emailConfirmationRequired: boolean
}

export interface EmailSignUpResult {
  session: Session | null
  confirmationRequired: boolean
}

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

function rememberAuthReturn(path: string): void {
  try {
    window.sessionStorage.setItem(AUTH_RETURN_KEY, safeInternalPath(path))
  } catch {
    // OAuth still returns safely to the application root when session storage is unavailable.
  }
}

export function consumeAuthReturn(fallback = '/'): string {
  try {
    const value = window.sessionStorage.getItem(AUTH_RETURN_KEY)
    window.sessionStorage.removeItem(AUTH_RETURN_KEY)
    return safeInternalPath(value, fallback)
  } catch {
    return fallback
  }
}

export function clearAuthReturn(): void {
  try {
    window.sessionStorage.removeItem(AUTH_RETURN_KEY)
  } catch {
    // There is no pending redirect to clear when storage is unavailable.
  }
}

export async function loadAuthCapabilities(): Promise<AuthCapabilities> {
  if (!frontendAuthConfigured || !projectUrl || !publishableKey) {
    return { email: false, google: false, signup: false, emailConfirmationRequired: true }
  }
  const response = await fetch(`${projectUrl}/auth/v1/settings`, {
    headers: { apikey: publishableKey },
  })
  if (!response.ok) throw new Error('Authentication options could not be loaded.')
  const payload = await response.json() as {
    disable_signup?: unknown
    mailer_autoconfirm?: unknown
    external?: Record<string, unknown>
  }
  return {
    email: payload.external?.email === true,
    google: payload.external?.google === true,
    signup: payload.disable_signup !== true,
    emailConfirmationRequired: payload.mailer_autoconfirm !== true,
  }
}

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

export async function signInWithGoogle(returnPath = '/'): Promise<void> {
  if (!supabase) throw new Error('Google sign-in is unavailable until Supabase public configuration is added.')
  rememberAuthReturn(returnPath)
  const redirectTo = localAuthRedirect(window.location.origin, applicationOrigin)
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo },
  })
  if (error) throw new Error('Google sign-in could not start. Check the Supabase provider configuration.')
}

export async function signInWithEmail(email: string, password: string): Promise<Session> {
  if (!supabase) throw new Error('Email sign-in is unavailable until Supabase public configuration is added.')
  const { data, error } = await supabase.auth.signInWithPassword({ email: email.trim(), password })
  if (error || !data.session) {
    throw new Error('The email or password was not accepted. Check both fields or reset the password.')
  }
  return data.session
}

export async function signUpWithEmail(
  fullName: string,
  email: string,
  password: string,
): Promise<EmailSignUpResult> {
  if (!supabase) throw new Error('Account creation is unavailable until Supabase public configuration is added.')
  const emailRedirectTo = applicationRedirect(window.location.origin, '/account', applicationOrigin)
  const { data, error } = await supabase.auth.signUp({
    email: email.trim(),
    password,
    options: {
      emailRedirectTo,
      data: { full_name: fullName.trim() },
    },
  })
  if (error) {
    if (error.code === 'weak_password') throw new Error(error.message)
    throw new Error('Account creation could not be completed. Check the fields and try again.')
  }
  return {
    session: data.session,
    confirmationRequired: data.session === null,
  }
}

export async function requestPasswordReset(email: string): Promise<void> {
  if (!supabase) throw new Error('Password recovery is unavailable until Supabase public configuration is added.')
  const redirectTo = applicationRedirect(window.location.origin, '/update-password', applicationOrigin)
  const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), { redirectTo })
  if (error) throw new Error('The recovery request could not be sent. Wait before trying again.')
}

export async function updatePassword(password: string): Promise<void> {
  if (!supabase) throw new Error('Password update is unavailable until Supabase public configuration is added.')
  const { error } = await supabase.auth.updateUser({ password })
  if (error) {
    if (error.code === 'weak_password') throw new Error(error.message)
    throw new Error('The password could not be updated. The recovery link may be invalid or expired.')
  }
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
