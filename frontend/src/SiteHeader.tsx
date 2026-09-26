import type { Session } from '@supabase/supabase-js'
import { useReducedMotion } from 'motion/react'
import * as m from 'motion/react-m'
import { useEffect, useState } from 'react'
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
  'control-motion inline-flex min-h-11 items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-extrabold text-accent-ink shadow-[0_0_18px_rgba(78,222,163,0.14)] hover:bg-accent-dark hover:shadow-[0_0_24px_rgba(78,222,163,0.24)] disabled:hover:bg-accent'
const secondaryButton =
  'control-motion inline-flex min-h-11 items-center justify-center rounded-md border border-accent/25 bg-accent/5 px-4 py-2.5 text-sm font-bold text-accent hover:border-accent/60 hover:bg-accent/10'

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
  const reduceMotion = useReducedMotion()
  const [scrolled, setScrolled] = useState(() => window.scrollY > 24)

  useEffect(() => {
    let frame = 0
    const update = () => {
      if (frame) return
      frame = window.requestAnimationFrame(() => {
        frame = 0
        setScrolled(window.scrollY > 24)
      })
    }
    update()
    window.addEventListener('scroll', update, { passive: true })
    return () => {
      window.removeEventListener('scroll', update)
      if (frame) window.cancelAnimationFrame(frame)
    }
  }, [])

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
    <m.header
      className="sticky top-0 z-40 border-b"
      data-scrolled={scrolled ? 'true' : 'false'}
      initial={false}
      animate={scrolled ? {
        backgroundColor: 'rgba(7, 22, 22, 0.9)',
        borderColor: 'rgba(78, 222, 163, 0.22)',
        boxShadow: '0 10px 34px rgba(0, 0, 0, 0.28)',
        backdropFilter: 'blur(16px)',
      } : {
        backgroundColor: 'rgba(7, 22, 22, 0)',
        borderColor: 'rgba(78, 222, 163, 0)',
        boxShadow: '0 10px 34px rgba(0, 0, 0, 0)',
        backdropFilter: 'blur(0px)',
      }}
      transition={{ duration: reduceMotion ? 0 : 0.22, ease: 'easeOut' }}
    >
      <div className="mx-auto flex max-w-[94rem] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-7">
        <button type="button" className="control-motion min-w-0 rounded-md" onClick={() => navigate('/')} aria-label="Research Guard home">
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
                className={`control-motion relative min-h-10 shrink-0 rounded-sm px-3.5 py-2 text-sm font-bold ${current ? 'text-ink' : 'text-muted hover:bg-panel hover:text-ink'}`}
                onClick={() => navigate(path)}
              >
                <span className="relative z-10">{label}</span>
                {label === 'AI chat' && <span className="status-pulse relative z-10 ml-1 font-mono text-[0.55rem] uppercase text-warm-ink">unchecked</span>}
                {current && (
                  <m.span
                    layoutId="nav-underline"
                    data-testid="nav-underline"
                    aria-hidden="true"
                    className="absolute inset-x-3 bottom-0 h-0.5 rounded-full bg-accent shadow-[0_0_10px_rgba(78,222,163,0.55)]"
                    transition={{ duration: reduceMotion ? 0 : 0.22, ease: [0.22, 1, 0.36, 1] }}
                  />
                )}
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
    </m.header>
  )
}
