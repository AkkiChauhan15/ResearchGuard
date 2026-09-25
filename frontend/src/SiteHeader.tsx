import type { Session } from '@supabase/supabase-js'
import { BrandLockup } from './Brand'

type Navigate = (path: string, replace?: boolean) => void

interface SiteHeaderProps {
  session: Session | null
  authReady: boolean
  authAvailable: boolean
  authBusy?: boolean
  currentPath: string
  subtitle: string
  navigate: Navigate
  onSignOut: () => Promise<void>
}

const primaryButton =
  'inline-flex min-h-11 items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-extrabold text-accent-ink shadow-[0_0_18px_rgba(78,222,163,0.14)] transition hover:bg-accent-dark hover:shadow-[0_0_24px_rgba(78,222,163,0.24)] disabled:hover:bg-accent'
const secondaryButton =
  'inline-flex min-h-11 items-center justify-center rounded-md border border-accent/25 bg-accent/5 px-4 py-2.5 text-sm font-bold text-accent transition hover:border-accent/60 hover:bg-accent/10'

function isCurrent(currentPath: string, target: string): boolean {
  if (target === '/review/new') return currentPath === target || /^\/review\/[^/]+$/.test(currentPath)
  return currentPath === target
}

export default function SiteHeader({
  session,
  authReady,
  authAvailable,
  authBusy = false,
  currentPath,
  subtitle,
  navigate,
  onSignOut,
}: SiteHeaderProps) {
  const signedInLinks = [
    ['Home', '/'],
    ['Dashboard', '/dashboard'],
    ['New review', '/review/new'],
    ['AI chat', '/chat'],
    ['About', '/about'],
  ] as const
  const signedOutLinks = [
    ['Home', '/'],
    ['About', '/about'],
    ['Demo', '/demo/cyto-id'],
  ] as const
  const links = session ? signedInLinks : signedOutLinks

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-canvas/90 shadow-[0_10px_34px_rgba(0,0,0,0.28)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-[94rem] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-7">
        <button type="button" className="min-w-0 rounded-md" onClick={() => navigate('/')} aria-label="Research Guard home">
          <BrandLockup subtitle={subtitle} />
        </button>
        <nav aria-label="Primary navigation" className="order-3 flex w-full items-center gap-1 overflow-x-auto rounded-md bg-deep p-1 md:order-none md:w-auto">
          {links.map(([label, path]) => {
            const current = isCurrent(currentPath, path)
            return (
              <button
                key={path}
                type="button"
                aria-current={current ? 'page' : undefined}
                className={`min-h-10 shrink-0 rounded-sm px-3.5 py-2 text-sm font-bold transition ${current ? 'bg-accent text-accent-ink' : 'text-muted hover:bg-panel hover:text-ink'}`}
                onClick={() => navigate(path)}
              >
                {label}
                {label === 'AI chat' && <span className="ml-1 font-mono text-[0.55rem] uppercase text-warm-ink">unchecked</span>}
              </button>
            )
          })}
        </nav>
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden text-right font-mono text-[0.62rem] leading-5 text-muted sm:block">
            <p className="font-bold text-ink">{!authReady ? 'Checking sign-in…' : session ? 'Signed in' : 'Signed out'}</p>
            {session?.user.email && <p className="max-w-48 truncate">{session.user.email}</p>}
          </div>
          {session ? (
            <>
              <button type="button" className={secondaryButton} onClick={() => navigate('/account')}>Account</button>
              <button type="button" className={secondaryButton} disabled={authBusy} onClick={() => void onSignOut()}>Sign out</button>
            </>
          ) : (
            <button type="button" className={primaryButton} disabled={!authReady || !authAvailable} onClick={() => navigate('/login?next=/dashboard')}>
              Sign in
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
