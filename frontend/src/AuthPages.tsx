import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { BrandLockup } from './Brand'
import {
  frontendAuthConfigured,
  loadAuthCapabilities,
  passwordMinimumLength,
  requestPasswordReset,
  signInWithEmail,
  signInWithGoogle,
  signUpWithEmail,
  updatePassword,
  type AuthCapabilities,
} from './auth'
import { requestedInternalPath } from './auth-utils'
import {
  emptyProfile,
  loadProfile,
  researchRoles,
  saveProfile,
  type ResearcherProfile,
} from './profile'

export type AuthPageRoute = 'login' | 'signup' | 'forgot-password' | 'update-password' | 'account'
export type Navigate = (path: string, replace?: boolean) => void

interface AuthPagesProps {
  route: AuthPageRoute
  session: Session | null
  authReady: boolean
  backendAuthAvailable: boolean
  passwordRecoveryReady: boolean
  authMessage: string | null
  clearAuthMessage: () => void
  navigate: Navigate
  onAuthenticated: (session: Session, destination: string) => Promise<void>
  onSignOut: () => Promise<void>
  onExploreDemo: () => Promise<void>
}

const fieldClass =
  'mt-2 w-full rounded-md border border-line bg-deep/80 px-3.5 py-3 text-base text-ink shadow-sm transition placeholder:text-muted/60 hover:border-accent/50 focus:border-accent focus:shadow-[inset_0_0_10px_rgba(78,222,163,0.08)]'
const primaryButton =
  'inline-flex min-h-12 w-full items-center justify-center rounded-md bg-accent px-4 py-3 text-sm font-black text-accent-ink shadow-[0_0_20px_rgba(78,222,163,0.16)] transition hover:bg-accent-dark hover:shadow-[0_0_26px_rgba(78,222,163,0.25)] disabled:hover:bg-accent'
const secondaryButton =
  'inline-flex min-h-11 items-center justify-center rounded-md border border-accent/25 bg-accent/5 px-4 py-2.5 text-sm font-black text-accent transition hover:border-accent/60 hover:bg-accent/10'
const textLink =
  'inline-flex min-h-10 items-center rounded-md px-1 py-2 text-sm font-black text-accent underline decoration-accent/30 underline-offset-4'

function GoogleIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="size-5">
      <path fill="#4285F4" d="M21.6 12.23c0-.71-.06-1.4-.18-2.06H12v3.9h5.38a4.6 4.6 0 0 1-2 3.02v2.53h3.24c1.9-1.75 2.98-4.32 2.98-7.39Z" />
      <path fill="#34A853" d="M12 22c2.7 0 4.98-.9 6.63-2.38l-3.24-2.53c-.9.6-2.05.96-3.39.96-2.61 0-4.83-1.77-5.62-4.14H3.03v2.61A10 10 0 0 0 12 22Z" />
      <path fill="#FBBC05" d="M6.38 13.91A6.02 6.02 0 0 1 6.06 12c0-.66.11-1.3.32-1.91V7.48H3.03A10 10 0 0 0 2 12c0 1.61.38 3.14 1.03 4.52l3.35-2.61Z" />
      <path fill="#EA4335" d="M12 5.95c1.47 0 2.79.5 3.83 1.5l2.87-2.88A9.64 9.64 0 0 0 12 2a10 10 0 0 0-8.97 5.48l3.35 2.61C7.17 7.72 9.39 5.95 12 5.95Z" />
    </svg>
  )
}

function Spinner() {
  return <span aria-hidden="true" className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
}

function PasswordField({
  id,
  label,
  value,
  onChange,
  autoComplete,
}: {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  autoComplete: 'current-password' | 'new-password'
}) {
  const [visible, setVisible] = useState(false)
  return (
    <div>
      <div className="flex items-end justify-between gap-3">
        <label htmlFor={id} className="text-sm font-black text-ink">{label}</label>
        <button
          type="button"
          className="min-h-9 rounded-md px-2 text-xs font-black text-accent hover:bg-soft"
          aria-controls={id}
          aria-pressed={visible}
          onClick={() => setVisible((current) => !current)}
        >
          {visible ? 'Hide' : 'Show'}
        </button>
      </div>
      <input
        id={id}
        type={visible ? 'text' : 'password'}
        className={fieldClass}
        value={value}
        minLength={passwordMinimumLength}
        maxLength={128}
        autoComplete={autoComplete}
        required
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  )
}

function Alert({ children, tone = 'error' }: { children: ReactNode; tone?: 'error' | 'notice' }) {
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={tone === 'error'
        ? 'rounded-xl border border-danger/25 bg-danger-soft px-4 py-3 text-sm font-bold leading-6 text-danger'
        : 'rounded-xl border border-accent/20 bg-soft px-4 py-3 text-sm font-bold leading-6 text-accent-dark'}
    >
      {children}
    </div>
  )
}

function AuthShell({ children, navigate }: { children: ReactNode; navigate: Navigate }) {
  return (
    <div className="min-h-screen bg-canvas px-3 py-3 sm:px-6 sm:py-6">
      <a href="#account-content" className="fixed -top-20 left-3 z-50 rounded-md bg-accent px-4 py-2 font-bold text-accent-ink transition-[top] focus:top-3">Skip to account access</a>
      <div className="mx-auto min-h-[calc(100vh-1.5rem)] max-w-7xl overflow-hidden rounded-lg border border-line bg-paper/75 shadow-[0_28px_90px_rgba(0,0,0,0.38)] sm:min-h-[calc(100vh-3rem)]">
      <header className="border-b border-line bg-deep/45">
        <div className="mx-auto flex items-center justify-between gap-4 px-4 py-4 sm:px-8">
          <button type="button" className="min-w-0 rounded-md text-left" onClick={() => navigate('/')} aria-label="Research Guard workspace">
            <BrandLockup subtitle="Secure research access" />
          </button>
          <button type="button" className={secondaryButton} onClick={() => navigate('/')}>Research workspace</button>
        </div>
      </header>
      <div className="border-b border-line bg-soft/25 px-4 py-2.5 font-mono text-[0.62rem] uppercase tracking-[0.12em] text-accent sm:px-8">
        <span className="mr-2 inline-block size-2 rounded-full bg-accent shadow-[0_0_10px_rgba(78,222,163,0.8)]" /> Account access · session handled by Supabase
      </div>
      <main id="account-content" tabIndex={-1} className="mx-auto grid min-h-[calc(100vh-170px)] max-w-6xl items-center gap-10 px-4 py-10 sm:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:py-16">
        <section className="max-w-xl lg:pr-6">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-accent">From an answer to an evidence record</p>
          <h1 className="mt-5 font-serif text-4xl leading-tight tracking-tight text-ink sm:text-6xl">Check claims. <em className="font-normal text-accent">Inspect evidence.</em> Record your decisions.</h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-muted">A focused research workspace for separating observations from interpretations and keeping source limitations visible.</p>
          <div className="mt-8 grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
            {['Editable claims', 'Inspectable sources', 'Researcher decisions'].map((item, index) => (
              <div key={item} className="rounded-sm border border-line bg-panel/45 p-3">
                <p className="font-mono text-[0.65rem] font-black uppercase tracking-wider text-accent">0{index + 1}</p>
                <p className="mt-1 text-sm font-black text-ink">{item}</p>
              </div>
            ))}
          </div>
        </section>
        <section className="w-full rounded-lg border border-accent/15 bg-panel/80 p-5 shadow-card backdrop-blur sm:p-8">
          {children}
        </section>
      </main>
      </div>
    </div>
  )
}

function AccountProfile({ session, onSignOut, navigate }: { session: Session; onSignOut: () => Promise<void>; navigate: Navigate }) {
  const metadataName = typeof session.user.user_metadata?.full_name === 'string'
    ? session.user.user_metadata.full_name
    : typeof session.user.user_metadata?.name === 'string'
      ? session.user.user_metadata.name
      : ''
  const [profile, setProfile] = useState<ResearcherProfile>({ ...emptyProfile, full_name: metadataName })
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    loadProfile()
      .then((saved) => {
        if (active && saved) setProfile(saved)
      })
      .catch((reason) => {
        if (active) setError(reason instanceof Error ? reason.message : 'Profile details are unavailable.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      await saveProfile(profile)
      setMessage('Optional profile details saved.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Profile details could not be saved.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <p className="text-xs font-black uppercase tracking-[0.22em] text-accent">Your account</p>
      <h2 className="mt-3 font-serif text-4xl text-ink">Account details</h2>
      <p className="mt-2 break-all text-sm leading-6 text-muted">Signed in as <strong className="text-ink">{session.user.email ?? 'verified user'}</strong></p>
      <div className="mt-5 flex flex-wrap gap-3">
        <button type="button" className={secondaryButton} onClick={() => navigate('/')}>Continue to workspace</button>
        <button type="button" className={secondaryButton} disabled={busy} onClick={onSignOut}>Sign out</button>
      </div>
      <div className="my-7 h-px bg-line" />
      <h3 className="text-lg font-black text-ink">Optional research profile</h3>
      <p className="mt-2 text-sm leading-6 text-muted">These details stay in your Supabase profile and are never included in research-verification model requests. You may leave every field blank.</p>
      {loading ? <p role="status" className="mt-5 text-sm text-muted">Loading profile…</p> : (
        <form className="mt-5 space-y-4" onSubmit={submit}>
          <label className="block text-sm font-black text-ink">Full name
            <input className={fieldClass} maxLength={120} autoComplete="name" value={profile.full_name} onChange={(event) => setProfile((current) => ({ ...current, full_name: event.target.value }))} />
          </label>
          <label className="block text-sm font-black text-ink">Research role
            <select className={fieldClass} value={profile.research_role} onChange={(event) => setProfile((current) => ({ ...current, research_role: event.target.value as ResearcherProfile['research_role'] }))}>
              <option value="">Prefer not to say</option>
              {researchRoles.map((role) => <option key={role}>{role}</option>)}
            </select>
          </label>
          <label className="block text-sm font-black text-ink">Research field
            <input className={fieldClass} maxLength={160} value={profile.research_field} onChange={(event) => setProfile((current) => ({ ...current, research_field: event.target.value }))} />
          </label>
          <label className="block text-sm font-black text-ink">Institution or organization
            <input className={fieldClass} maxLength={200} autoComplete="organization" value={profile.institution} onChange={(event) => setProfile((current) => ({ ...current, institution: event.target.value }))} />
          </label>
          {error && <Alert>{error}</Alert>}
          {message && <Alert tone="notice">{message}</Alert>}
          <button type="submit" className={primaryButton} disabled={busy}>{busy ? <><Spinner /> <span className="ml-2">Saving…</span></> : 'Save optional details'}</button>
        </form>
      )}
    </>
  )
}

export default function AuthPages({
  route,
  session,
  authReady,
  backendAuthAvailable,
  passwordRecoveryReady,
  authMessage,
  clearAuthMessage,
  navigate,
  onAuthenticated,
  onSignOut,
  onExploreDemo,
}: AuthPagesProps) {
  const [capabilities, setCapabilities] = useState<AuthCapabilities | null>(null)
  const [capabilityError, setCapabilityError] = useState(false)
  const [busy, setBusy] = useState(false)
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    loadAuthCapabilities()
      .then((value) => { if (active) setCapabilities(value) })
      .catch(() => { if (active) setCapabilityError(true) })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!authReady || !session) return
    if (route === 'login' || route === 'forgot-password') {
      navigate(requestedInternalPath(window.location.search), true)
    } else if (route === 'signup') {
      navigate('/account', true)
    }
  }, [authReady, navigate, route, session])

  const resetMessages = () => {
    setFormError(null)
    setNotice(null)
    clearAuthMessage()
  }

  const startGoogle = async () => {
    resetMessages()
    setBusy(true)
    try {
      await signInWithGoogle(route === 'signup' ? '/account' : requestedInternalPath(window.location.search))
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : 'Google sign-in could not start.')
      setBusy(false)
    }
  }

  const submitLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    resetMessages()
    setBusy(true)
    try {
      const signedIn = await signInWithEmail(email, password)
      await onAuthenticated(signedIn, requestedInternalPath(window.location.search))
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : 'Sign-in failed.')
      setBusy(false)
    }
  }

  const submitSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    resetMessages()
    if (password !== confirmPassword) {
      setFormError('The password and confirmation do not match.')
      return
    }
    setBusy(true)
    try {
      const result = await signUpWithEmail(fullName, email, password)
      setPassword('')
      setConfirmPassword('')
      if (result.session) {
        await onAuthenticated(result.session, '/account')
      } else {
        setNotice('Check your email to confirm the account. For privacy, this message is the same even if the address was already registered.')
        setBusy(false)
      }
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : 'Account creation failed.')
      setBusy(false)
    }
  }

  const submitRecovery = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    resetMessages()
    setBusy(true)
    try {
      await requestPasswordReset(email)
      setNotice('If an account can receive recovery email, a password-reset message has been sent. Check the inbox and spam folder.')
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : 'Password recovery is unavailable.')
    } finally {
      setBusy(false)
    }
  }

  const submitPassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    resetMessages()
    if (password !== confirmPassword) {
      setFormError('The password and confirmation do not match.')
      return
    }
    setBusy(true)
    try {
      await updatePassword(password)
      setPassword('')
      setConfirmPassword('')
      setNotice('Password updated. You can continue to the research workspace.')
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : 'The password could not be updated.')
    } finally {
      setBusy(false)
    }
  }

  const googleEnabled = Boolean(frontendAuthConfigured && backendAuthAvailable && (capabilities?.google ?? true))
  const emailEnabled = Boolean(capabilities?.email)
  const signupEnabled = Boolean(emailEnabled && capabilities?.signup)

  let content: ReactNode
  if (route === 'account') {
    content = session
      ? <AccountProfile session={session} onSignOut={onSignOut} navigate={navigate} />
      : <><h2 className="font-serif text-4xl text-ink">Sign in required</h2><p className="mt-3 text-sm leading-6 text-muted">Account details are private. Sign in to continue.</p><button className={`${primaryButton} mt-6`} onClick={() => navigate('/login?next=/account')}>Go to sign in</button></>
  } else if (route === 'forgot-password') {
    content = (
      <>
        <p className="text-xs font-black uppercase tracking-[0.22em] text-accent">Account recovery</p>
        <h2 className="mt-3 font-serif text-4xl text-ink">Reset your password</h2>
        <p className="mt-3 text-sm leading-6 text-muted">Enter the email used for an email-and-password account. Google account passwords are recovered through Google.</p>
        <form className="mt-6 space-y-5" onSubmit={submitRecovery}>
          <label htmlFor="recovery-email" className="block text-sm font-black text-ink">Email address
            <input id="recovery-email" type="email" className={fieldClass} autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          {(formError || authMessage) && <Alert>{formError ?? authMessage}</Alert>}
          {notice && <Alert tone="notice">{notice}</Alert>}
          <button type="submit" className={primaryButton} disabled={busy || !emailEnabled}>{busy ? 'Sending…' : 'Send recovery email'}</button>
        </form>
        <button className={`${textLink} mt-4`} onClick={() => navigate('/login')}>Back to sign in</button>
      </>
    )
  } else if (route === 'update-password') {
    content = (
      <>
        <p className="text-xs font-black uppercase tracking-[0.22em] text-accent">Secure recovery</p>
        <h2 className="mt-3 font-serif text-4xl text-ink">Choose a new password</h2>
        <p className="mt-3 text-sm leading-6 text-muted">The recovery link must establish a valid Supabase session before the password can be changed.</p>
        {!session || !passwordRecoveryReady ? <Alert>The recovery session is missing or expired. Request a new password-reset email.</Alert> : (
          <form className="mt-6 space-y-5" onSubmit={submitPassword}>
            <PasswordField id="new-password" label="New password" value={password} onChange={setPassword} autoComplete="new-password" />
            <PasswordField id="confirm-new-password" label="Confirm new password" value={confirmPassword} onChange={setConfirmPassword} autoComplete="new-password" />
            <p className="text-xs leading-5 text-muted">Use at least {passwordMinimumLength} characters. Supabase will enforce any additional project password rules.</p>
            {formError && <Alert>{formError}</Alert>}
            {notice && <Alert tone="notice">{notice}</Alert>}
            <button type="submit" className={primaryButton} disabled={busy}>{busy ? 'Updating…' : 'Update password'}</button>
          </form>
        )}
        <button className={`${textLink} mt-4`} onClick={() => navigate(session && passwordRecoveryReady ? '/' : '/forgot-password')}>{session && passwordRecoveryReady ? 'Continue to workspace' : 'Request another recovery email'}</button>
      </>
    )
  } else {
    const signup = route === 'signup'
    content = (
      <>
        <p className="text-xs font-black uppercase tracking-[0.22em] text-accent">{signup ? 'New researcher account' : 'Researcher access'}</p>
        <h2 className="mt-3 font-serif text-4xl text-ink">{signup ? 'Create your Research Guard AI account' : 'Welcome back'}</h2>
        <p className="mt-3 text-sm leading-6 text-muted">{signup ? 'Review AI-generated research information with evidence you can inspect.' : 'Sign in to review research claims and access your saved reviews.'}</p>
        <button type="button" className={`${secondaryButton} mt-6 w-full gap-3`} disabled={busy || !googleEnabled} onClick={startGoogle}>
          {busy ? <Spinner /> : <GoogleIcon />} {busy ? 'Opening Google…' : 'Continue with Google'}
        </button>
        {!googleEnabled && authReady && <p className="mt-2 text-xs leading-5 text-danger">Google sign-in is unavailable until the frontend, backend, and provider configuration are all active.</p>}
        <div className="my-6 flex items-center gap-3 text-xs font-black uppercase tracking-[0.18em] text-muted"><span className="h-px flex-1 bg-line" />or<span className="h-px flex-1 bg-line" /></div>
        {emailEnabled && (signup ? signupEnabled : true) ? (
          <form className="space-y-5" onSubmit={signup ? submitSignup : submitLogin}>
            {signup && <label htmlFor="signup-name" className="block text-sm font-black text-ink">Full name
              <input id="signup-name" className={fieldClass} autoComplete="name" maxLength={120} required value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </label>}
            <label htmlFor="auth-email" className="block text-sm font-black text-ink">Email address
              <input id="auth-email" type="email" className={fieldClass} autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
            </label>
            <PasswordField id="auth-password" label="Password" value={password} onChange={setPassword} autoComplete={signup ? 'new-password' : 'current-password'} />
            {signup && <PasswordField id="confirm-password" label="Confirm password" value={confirmPassword} onChange={setConfirmPassword} autoComplete="new-password" />}
            {signup && <p className="text-xs leading-5 text-muted">Use at least {passwordMinimumLength} characters. Supabase will enforce any additional project password rules. {capabilities?.emailConfirmationRequired ? 'Confirmation by email is currently required.' : 'This project currently permits immediate sign-in after registration.'}</p>}
            {!signup && <div className="text-right"><button type="button" className={textLink} onClick={() => navigate('/forgot-password')}>Forgot password?</button></div>}
            {(formError || authMessage) && <Alert>{formError ?? authMessage}</Alert>}
            {notice && <Alert tone="notice">{notice}</Alert>}
            <button type="submit" className={primaryButton} disabled={busy}>{busy ? <><Spinner /><span className="ml-2">Please wait…</span></> : signup ? 'Create account' : 'Sign in'}</button>
          </form>
        ) : (
          <div className="rounded-xl border border-line bg-canvas px-4 py-3 text-sm leading-6 text-muted">
            {capabilityError ? 'Email sign-in options could not be verified, so nonfunctional email controls are hidden.' : 'Checking available email sign-in options…'}
          </div>
        )}
        <p className="mt-6 text-center text-sm text-muted">
          {signup ? 'Already have an account?' : 'New to Research Guard AI?'}{' '}
          <button className={textLink} onClick={() => navigate(signup ? '/login' : '/signup')}>{signup ? 'Sign in' : 'Create an account'}</button>
        </p>
        <div className="mt-5 border-t border-line pt-5 text-center">
          <button type="button" className={textLink} disabled={busy} onClick={onExploreDemo}>Explore the demo without signing in</button>
          <p className="mt-1 text-xs leading-5 text-muted">The demonstration is predefined and clearly labeled; it is not a live verification.</p>
        </div>
      </>
    )
  }

  return <AuthShell navigate={navigate}>{content}</AuthShell>
}
