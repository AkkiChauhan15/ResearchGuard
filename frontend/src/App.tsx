import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import AuthPages, { type AuthPageRoute } from './AuthPages'
import { BrandLockup, WorkflowStrip } from './Brand'
import ChatPage from './ChatPage'
import { api, downloadExport, downloadSavedExport } from './api'
import {
  clearAuthReturn,
  clearLocalSession,
  clearOAuthErrorFromUrl,
  consumeAuthReturn,
  frontendAuthConfigured,
  readOAuthOutcome,
  restoreSession,
  signOut,
  subscribeToAuth,
} from './auth'
import { safeInternalPath } from './auth-utils'
import type {
  AccessState,
  ApiConfig,
  Claim,
  Decision,
  ExperimentalContext,
  IntendedUse,
  Review,
  SavedReviewSummary,
  Source,
} from './types'

const inputClass =
  'mt-2 w-full rounded-md border border-line bg-deep/80 px-3.5 py-3 text-sm text-ink shadow-sm transition placeholder:text-muted/65 hover:border-accent/50 focus:border-accent focus:shadow-[inset_0_0_10px_rgba(78,222,163,0.08)]'
const primaryButton =
  'inline-flex min-h-11 items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-extrabold text-accent-ink shadow-[0_0_18px_rgba(78,222,163,0.14)] transition hover:bg-accent-dark hover:shadow-[0_0_24px_rgba(78,222,163,0.24)] disabled:hover:bg-accent'
const secondaryButton =
  'inline-flex min-h-11 items-center justify-center rounded-md border border-accent/25 bg-accent/5 px-4 py-2.5 text-sm font-bold text-accent transition hover:border-accent/60 hover:bg-accent/10'
const quietButton =
  'inline-flex min-h-10 items-center justify-center rounded-md px-3 py-2 text-sm font-bold text-accent underline decoration-accent/30 underline-offset-4 transition hover:bg-soft'

const emptyContext: ExperimentalContext = {
  organism_model: '',
  assay: '',
  reagent: '',
  conditions: '',
}

const authRoutes: Record<string, AuthPageRoute> = {
  '/login': 'login',
  '/signup': 'signup',
  '/forgot-password': 'forgot-password',
  '/update-password': 'update-password',
  '/account': 'account',
}

function browserAddress(): string {
  return `${window.location.pathname}${window.location.search}`
}

function navigateBrowser(path: string, replace = false): void {
  const destination = safeInternalPath(path)
  window.history[replace ? 'replaceState' : 'pushState']({}, '', destination)
  window.dispatchEvent(new PopStateEvent('popstate'))
  window.scrollTo({ top: 0, behavior: 'instant' })
}

const accessLabels: Record<AccessState, string> = {
  ok: 'Access complete',
  no_results: 'No results',
  partial_access: 'Partial access',
  rate_limited: 'Rate limited',
  fetch_failed: 'Fetch failed',
  parse_failed: 'Parse failed',
}

function cx(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(' ')
}

function SectionLabel({ children }: { children: ReactNode }) {
  return <p className="font-mono text-[0.64rem] font-semibold uppercase tracking-[0.18em] text-accent">{children}</p>
}

function ArrowIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="size-4 fill-none stroke-current stroke-2">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  )
}

function ExternalIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="size-4 fill-none stroke-current stroke-2">
      <path d="M14 5h5v5M10 14 19 5M19 13v6H5V5h6" />
    </svg>
  )
}

function Spinner() {
  return <span aria-hidden="true" className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null
  return (
    <div>
      <h4 className="text-sm font-black text-ink">{title}</h4>
      <ul className="mt-2 space-y-2 text-sm leading-6 text-muted">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span aria-hidden="true" className="mt-2 size-1.5 shrink-0 rounded-full bg-accent/60" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function SourceCard({ source }: { source: Source }) {
  return (
    <article className="rounded-lg border border-line bg-panel p-4 shadow-[inset_0_1px_0_rgba(78,222,163,0.05)] sm:p-5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-soft px-2.5 py-1 text-[0.68rem] font-black uppercase tracking-wider text-accent-dark">
          {source.access_level} access
        </span>
        <span className="text-xs font-bold uppercase tracking-wider text-muted">{source.category}</span>
      </div>
      <h5 className="mt-3 text-base font-black leading-snug text-ink">{source.title}</h5>
      <p className="mt-2 break-all text-xs leading-5 text-muted">
        DOI {source.doi ?? 'unavailable'} · PMID {source.pmid ?? 'unavailable'} · PMCID {source.pmcid ?? 'unavailable'}
      </p>
      <a
        href={source.url}
        target="_blank"
        rel="noreferrer"
        className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-lg text-sm font-black text-accent underline decoration-accent/30 underline-offset-4"
      >
        Open original source <ExternalIcon />
      </a>
      {source.limitations.length > 0 && (
        <div className="mt-4 rounded-lg bg-warm/65 p-3">
          <p className="text-xs font-black uppercase tracking-wider text-warm-ink">Access limitations</p>
          <ul className="mt-2 space-y-1.5 text-sm leading-5 text-warm-ink">
            {source.limitations.map((limitation) => <li key={limitation}>• {limitation}</li>)}
          </ul>
        </div>
      )}
      <details className="mt-4 border-t border-line pt-3">
        <summary className="min-h-10 py-2 text-sm font-black text-ink">
          Retrieved passages ({source.passages.length})
        </summary>
        <div className="mt-2 space-y-3">
          {source.passages.length === 0 && <p className="text-sm text-muted">No readable passage was available.</p>}
          {source.passages.map((passage, index) => (
            <div key={`${passage.location}-${index}`} className="rounded-lg bg-canvas p-3">
              <p className="text-xs font-black uppercase tracking-wider text-muted">{passage.location}</p>
              <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-ink">{passage.text}</p>
            </div>
          ))}
        </div>
      </details>
    </article>
  )
}

type RunReviewAction = (label: string, action: () => Promise<Review>, success: string) => Promise<void>

interface ClaimCardProps {
  review: Review
  claim: Claim
  index: number
  busy: boolean
  runReviewAction: RunReviewAction
}

function ClaimCard({ review, claim, index, busy, runReviewAction }: ClaimCardProps) {
  const [editText, setEditText] = useState(claim.text)
  const [query, setQuery] = useState(
    [claim.text, review.original_input.context.organism_model, review.original_input.context.assay]
      .filter(Boolean)
      .join(' '),
  )
  const [finalWording, setFinalWording] = useState(claim.decision.final_wording || claim.assessment?.suggested_wording || '')
  const [notes, setNotes] = useState(claim.decision.notes)

  const attempts = review.attempts.filter((attempt) => attempt.claim_id === claim.claim_id)
  const currentSourceIds = new Set(attempts.flatMap((attempt) => attempt.source_ids))
  const currentSources = review.sources.filter((source) => currentSourceIds.has(source.source_id))
  const hasLimitedAccess = attempts.some((attempt) => attempt.access_state !== 'ok')
  const noReadableSources = attempts.length > 0 && currentSources.every((source) => source.passages.length === 0)

  const decision = (status: Decision['status']): Decision => ({
    status,
    final_wording: finalWording,
    notes,
  })

  return (
    <article className="overflow-hidden rounded-2xl border border-line bg-paper shadow-card">
      <header className="border-b border-line bg-panel/75 px-5 py-5 sm:px-7">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="grid size-8 place-items-center rounded-full bg-accent font-mono text-xs font-black text-accent-ink">{index + 1}</span>
            <span className="rounded-full border border-line px-2.5 py-1 text-[0.68rem] font-black uppercase tracking-wider text-muted">
              {claim.type}
            </span>
          </div>
          <p className="text-xs font-bold text-muted">Researcher decision: <span className="text-ink">{claim.decision.status}</span></p>
        </div>
        <h3 className="mt-4 break-words font-serif text-2xl leading-tight text-ink sm:text-3xl">{claim.text}</h3>
        {review.mode === 'live' && (
          <details className="mt-4 rounded-xl border border-line bg-canvas/70 p-3">
            <summary className="min-h-10 py-2 text-sm font-black text-accent">Edit this claim</summary>
            <div className="mt-2">
              <label htmlFor={`claim-${claim.claim_id}`} className="text-sm font-bold text-ink">Claim wording</label>
              <textarea
                id={`claim-${claim.claim_id}`}
                rows={3}
                maxLength={12000}
                className={inputClass}
                value={editText}
                onChange={(event) => setEditText(event.target.value)}
              />
              <p className="mt-2 text-xs leading-5 text-muted">
                A material edit clears the current assessment, decision, and visible evidence links. Historical provenance remains in exports.
              </p>
              <button
                type="button"
                disabled={busy || editText.trim() === claim.text}
                className={cx(primaryButton, 'mt-3')}
                onClick={() => runReviewAction(
                  'Updating the claim and invalidating earlier evidence…',
                  () => api.editClaim(review.review_id, claim.claim_id, editText),
                  'Claim updated. Earlier evidence and decisions are no longer shown as current.',
                )}
              >
                Apply claim edit
              </button>
            </div>
          </details>
        )}
      </header>

      <div className="space-y-7 px-5 py-6 sm:px-7">
        {(claim.observations.length > 0 || claim.inferences.length > 0) ? (
          <section aria-labelledby={`reasoning-${claim.claim_id}`}>
            <h4 id={`reasoning-${claim.claim_id}`} className="sr-only">Observation and interpretation</h4>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-line bg-panel p-4">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-accent">Reported observation</p>
                {claim.observations.length > 0 ? (
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-ink">{claim.observations.map((item) => <li key={item}>• {item}</li>)}</ul>
                ) : <p className="mt-3 text-sm text-muted">No observation was separated.</p>}
              </div>
              <div className="rounded-lg border border-line bg-panel p-4">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-warm-ink">Interpretation or inference</p>
                {claim.inferences.length > 0 ? (
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-ink">{claim.inferences.map((item) => <li key={item}>• {item}</li>)}</ul>
                ) : <p className="mt-3 text-sm text-muted">No interpretation was separated.</p>}
              </div>
            </div>
          </section>
        ) : (
          <p className="rounded-lg border border-dashed border-line bg-panel/60 p-4 text-sm leading-6 text-muted">
            Observation and interpretation have not been separated yet. The initial live claims are editable sentence segments.
          </p>
        )}

        {claim.missing_context.length > 0 && <ListBlock title="Questions about missing context" items={claim.missing_context} />}

        {review.mode === 'live' && (
          <section className="rounded-lg border border-line bg-panel p-4 sm:p-5" aria-labelledby={`retrieve-${claim.claim_id}`}>
            <h4 id={`retrieve-${claim.claim_id}`} className="text-base font-black text-ink">Retrieve and assess public evidence</h4>
            <label htmlFor={`query-${claim.claim_id}`} className="mt-4 block text-sm font-bold text-ink">PubMed search terms</label>
            <textarea
              id={`query-${claim.claim_id}`}
              rows={2}
              maxLength={500}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className={inputClass}
            />
            <p className="mt-2 text-xs leading-5 text-muted">Include the claim, organism or model, and assay where relevant. Search results are not an exhaustive review.</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy || !query.trim()}
                className={secondaryButton}
                onClick={() => runReviewAction(
                  'Retrieving public sources…',
                  () => api.retrieve(review.review_id, claim.claim_id, query),
                  'Retrieval finished. Check each access state and source limitation.',
                )}
              >
                Retrieve evidence
              </button>
              <button
                type="button"
                disabled={busy}
                className={primaryButton}
                onClick={() => runReviewAction(
                  'Comparing the claim with retrieved passages…',
                  () => api.assess(review.review_id, claim.claim_id),
                  'Assessment request finished. Inspect evidence and limitations before deciding.',
                )}
              >
                Assess retrieved evidence
              </button>
            </div>
          </section>
        )}

        {attempts.length > 0 && (
          <section aria-labelledby={`access-${claim.claim_id}`}>
            <div className={cx('rounded-xl border p-4', hasLimitedAccess ? 'border-warm-ink/25 bg-warm/55' : 'border-line bg-soft/65')}>
              <h4 id={`access-${claim.claim_id}`} className="text-sm font-black text-ink">
                {hasLimitedAccess ? 'Partial result or access limitation' : 'Source access completed'}
              </h4>
              {noReadableSources && <p className="mt-2 text-sm leading-6 text-warm-ink">No readable source passage is currently available. This is an access state, not evidence that the claim is false.</p>}
              <div className="mt-3 space-y-2">
                {attempts.map((attempt) => (
                  <div key={`${attempt.retrieval_run_id}-${attempt.adapter}-${attempt.query_or_url}`} className="rounded-md bg-panel/75 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-black uppercase tracking-wider text-ink">{attempt.adapter}</span>
                      <span className="rounded-full border border-line px-2 py-0.5 text-xs font-bold text-muted">{accessLabels[attempt.access_state]}</span>
                    </div>
                    <p className="mt-2 break-words text-sm leading-5 text-muted">{attempt.detail}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {claim.assessment_error && (
          <div role="status" className="rounded-xl border border-danger/20 bg-danger-soft p-4 text-sm leading-6 text-danger">
            <p className="font-black">Assessment unavailable</p>
            <p className="mt-1">{claim.assessment_error}</p>
          </div>
        )}

        {claim.assessment ? (
          <section className="space-y-6" aria-labelledby={`assessment-${claim.claim_id}`}>
            <div>
              <span className="inline-flex rounded-full border border-accent/25 bg-accent/10 px-3 py-1.5 font-mono text-xs font-black uppercase tracking-wider text-accent">
                {claim.assessment.status}
              </span>
              <h4 id={`assessment-${claim.claim_id}`} className="mt-4 font-serif text-2xl text-ink">What the retrieved material shows</h4>
              <p className="mt-3 text-sm leading-7 text-ink">{claim.assessment.explanation}</p>
            </div>

            {claim.assessment.evidence.map((evidence, evidenceIndex) => {
              const source = currentSources.find((item) => item.source_id === evidence.source_id)
              return (
                <blockquote key={`${evidence.source_id}-${evidence.location}-${evidenceIndex}`} className="border-l-4 border-accent bg-soft/60 p-4 sm:p-5">
                  <p className="text-xs font-black uppercase tracking-[0.16em] text-accent">{evidence.relationship} · exact source quotation</p>
                  <p className="mt-3 whitespace-pre-wrap break-words font-serif text-lg leading-7 text-ink">“{evidence.passage}”</p>
                  <footer className="mt-3 text-xs leading-5 text-muted">
                    {source?.title ?? 'Source record unavailable'} · {evidence.location}
                    {source && <> · <strong>{source.access_level} access</strong></>}
                  </footer>
                </blockquote>
              )
            })}

            <div className="grid gap-5 md:grid-cols-2">
              <ListBlock title="Context mismatches" items={claim.assessment.context_mismatches} />
              <ListBlock title="Limitations" items={claim.assessment.limitations} />
            </div>

            <div className="rounded-lg border border-accent/20 bg-deep p-5 text-ink shadow-[inset_0_1px_0_rgba(78,222,163,0.12)] sm:p-6">
              <p className="font-mono text-xs font-black uppercase tracking-[0.18em] text-accent/70">Suggested qualified wording</p>
              <p className="mt-3 font-serif text-xl leading-8">{claim.assessment.suggested_wording}</p>
            </div>
            <div className="rounded-lg border border-accent/25 bg-panel p-5">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-accent">Next verification question</p>
              <p className="mt-3 text-base font-bold leading-7 text-ink">{claim.assessment.next_verification_step}</p>
            </div>

            <section className="rounded-xl border border-line bg-canvas p-4 sm:p-5" aria-labelledby={`decision-${claim.claim_id}`}>
              <h4 id={`decision-${claim.claim_id}`} className="text-base font-black text-ink">Record your conclusion</h4>
              <p className="mt-1 text-sm leading-6 text-muted">The suggestion remains in the record even when you edit or reject it.</p>
              <label htmlFor={`wording-${claim.claim_id}`} className="mt-4 block text-sm font-bold text-ink">Your final wording</label>
              <textarea
                id={`wording-${claim.claim_id}`}
                rows={4}
                maxLength={12000}
                className={inputClass}
                value={finalWording}
                onChange={(event) => setFinalWording(event.target.value)}
              />
              <label htmlFor={`notes-${claim.claim_id}`} className="mt-4 block text-sm font-bold text-ink">Researcher notes</label>
              <textarea
                id={`notes-${claim.claim_id}`}
                rows={2}
                maxLength={5000}
                className={inputClass}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
              />
              <div className="mt-4 flex flex-wrap gap-2">
                {([
                  ['Accept suggestion', 'accepted'],
                  ['Save edited wording', 'edited'],
                  ['Reject', 'rejected'],
                  ['Reset to pending', 'pending'],
                ] as const).map(([label, status]) => (
                  <button
                    key={status}
                    type="button"
                    disabled={busy || (status === 'edited' && !finalWording.trim())}
                    className={status === 'accepted' ? primaryButton : secondaryButton}
                    onClick={() => runReviewAction(
                      'Recording your review decision…',
                      () => api.decide(review.review_id, claim.claim_id, decision(status)),
                      `Researcher decision recorded: ${status}.`,
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </section>
          </section>
        ) : (
          <div className="rounded-lg border border-dashed border-line bg-panel/60 p-4 text-sm leading-6 text-muted">
            No evidence assessment is currently attached to this claim. Missing evidence or a failed request does not establish that the claim is true or false.
          </div>
        )}

        {currentSources.length > 0 && (
          <section aria-labelledby={`sources-${claim.claim_id}`}>
            <h4 id={`sources-${claim.claim_id}`} className="font-serif text-2xl text-ink">Current source records</h4>
            <p className="mt-2 text-sm leading-6 text-muted">Access level describes what was retrieved. It does not certify that a source supports the claim.</p>
            <div className="mt-4 space-y-3">{currentSources.map((source) => <SourceCard key={source.source_id} source={source} />)}</div>
          </section>
        )}
      </div>
    </article>
  )
}

function EmptyReview() {
  return (
    <section className="grid min-h-[34rem] place-items-center rounded-2xl border border-line bg-paper p-8 text-center shadow-card">
      <div className="max-w-md">
        <div className="mx-auto grid size-16 place-items-center rounded-full bg-soft text-2xl text-accent">↗</div>
        <SectionLabel>Evidence before conclusion</SectionLabel>
        <h2 className="mt-4 font-serif text-4xl leading-tight text-ink">A claim is a starting point.</h2>
        <p className="mt-4 text-base leading-7 text-muted">Create a live review or open the curated demonstration. Each claim will keep its evidence, access limits, and your decision together.</p>
      </div>
    </section>
  )
}

function App() {
  const [location, setLocation] = useState(browserAddress)
  const [review, setReview] = useState<Review | null>(null)
  const [config, setConfig] = useState<ApiConfig | null>(null)
  const [configError, setConfigError] = useState(false)
  const [busyLabel, setBusyLabel] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState('Ready for a public or synthetic research claim.')
  const [answer, setAnswer] = useState('')
  const [intendedUse, setIntendedUse] = useState<IntendedUse>('topic understanding')
  const [context, setContext] = useState<ExperimentalContext>(emptyContext)
  const [sourceUrls, setSourceUrls] = useState('')
  const [showContext, setShowContext] = useState(false)
  const [authSession, setAuthSession] = useState<Session | null>(null)
  const [authReady, setAuthReady] = useState(false)
  const [authBusy, setAuthBusy] = useState(false)
  const [passwordRecoveryReady, setPasswordRecoveryReady] = useState(false)
  const [authMessage, setAuthMessage] = useState<string | null>(null)
  const [savedReviews, setSavedReviews] = useState<SavedReviewSummary[]>([])
  const [activeSaved, setActiveSaved] = useState<SavedReviewSummary | null>(null)
  const [savedLoading, setSavedLoading] = useState(false)
  const [savedError, setSavedError] = useState<string | null>(null)

  useEffect(() => {
    const updateLocation = () => setLocation(browserAddress())
    window.addEventListener('popstate', updateLocation)
    return () => window.removeEventListener('popstate', updateLocation)
  }, [])

  // oxlint-disable react/set-state-in-effect -- authentication and remote persistence are external state
  useEffect(() => {
    let active = true
    api.config()
      .then((value) => {
        if (active) setConfig(value)
      })
      .catch(() => {
        if (active) setConfigError(true)
      })
    return () => { active = false }
  }, [])

  useEffect(() => {
    let active = true
    const callbackOutcome = readOAuthOutcome()
    const unsubscribe = subscribeToAuth((event, session) => {
      if (!active) return
      if (event === 'SIGNED_OUT') {
        setAuthSession(null)
        setPasswordRecoveryReady(false)
      }
      if (event === 'PASSWORD_RECOVERY') {
        setAuthSession(session)
        setPasswordRecoveryReady(Boolean(session))
        navigateBrowser('/update-password', true)
      }
    })
    restoreSession()
      .then(async (session) => {
        if (!active) return
        if (session) {
          try {
            await api.authMe()
            if (active) {
              setAuthSession(session)
              const destination = consumeAuthReturn('/')
              if (window.location.pathname === '/' && destination !== '/') {
                navigateBrowser(destination, true)
              }
            }
          } catch {
            await clearLocalSession()
            if (active) {
              setAuthSession(null)
              setAuthMessage('The saved session was rejected or expired. Please sign in again.')
            }
          }
        }
      })
      .catch((reason) => {
        if (active) setAuthMessage(reason instanceof Error ? reason.message : 'The saved session could not be restored.')
      })
      .finally(() => {
        if (active) {
          if (callbackOutcome) {
            clearAuthReturn()
            setAuthMessage(callbackOutcome.message)
            navigateBrowser('/login', true)
          }
          clearOAuthErrorFromUrl()
          setAuthReady(true)
        }
      })
    return () => {
      active = false
      unsubscribe()
    }
  }, [])

  useEffect(() => {
    if (authReady && !authSession && (review?.mode === 'live' || activeSaved)) {
      setReview(null)
      setActiveSaved(null)
      setSavedReviews([])
      setNotice('The live review was closed because the sign-in session ended.')
    }
  }, [authReady, authSession, review, activeSaved])

  useEffect(() => {
    if (!authSession || !config?.persistence_configured) {
      setSavedReviews([])
      return
    }
    let active = true
    setSavedLoading(true)
    setSavedError(null)
    api.listSavedReviews()
      .then((result) => {
        if (active) setSavedReviews(result.items)
      })
      .catch((reason) => {
        if (active) setSavedError(reason instanceof Error ? reason.message : 'Saved reviews could not be listed.')
      })
      .finally(() => {
        if (active) setSavedLoading(false)
      })
    return () => { active = false }
  }, [authSession, config?.persistence_configured])

  useEffect(() => {
    if (activeSaved && review && activeSaved.review_id !== review.review_id) setActiveSaved(null)
  }, [activeSaved, review])
  // oxlint-enable react/set-state-in-effect

  const busy = busyLabel !== null
  const authAvailable = Boolean(config?.auth_configured && frontendAuthConfigured)
  const refreshSavedReviews = async () => {
    if (!authSession || !config?.persistence_configured || savedLoading) return
    setSavedLoading(true)
    setSavedError(null)
    try {
      const result = await api.listSavedReviews()
      setSavedReviews(result.items)
      if (activeSaved) {
        const current = result.items.find((item) => item.saved_id === activeSaved.saved_id)
        if (current) setActiveSaved(current)
      }
    } catch (reason) {
      setSavedError(reason instanceof Error ? reason.message : 'Saved reviews could not be refreshed.')
    } finally {
      setSavedLoading(false)
    }
  }
  const activeEvidenceCount = useMemo(() => {
    if (!review) return 0
    const currentClaimIds = new Set(review.claims.map((claim) => claim.claim_id))
    return new Set(
      review.attempts
        .filter((attempt) => currentClaimIds.has(attempt.claim_id))
        .flatMap((attempt) => attempt.source_ids),
    ).size
  }, [review])

  const runReviewAction: RunReviewAction = async (label, action, success) => {
    if (busy) return
    setBusyLabel(label)
    setError(null)
    setNotice(label)
    try {
      setReview(await action())
      setNotice(success)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The request failed. No result was substituted.')
      setNotice('Request failed. Review the error before retrying.')
    } finally {
      setBusyLabel(null)
    }
  }

  const runExport = async (format: 'json' | 'txt') => {
    if (!review || busy) return
    setBusyLabel('Validating and preparing the export…')
    setError(null)
    try {
      await downloadExport(review, format)
      setNotice(`${format.toUpperCase()} export downloaded from the canonical review.`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The export failed.')
      setNotice('Export failed. No incomplete download was presented.')
    } finally {
      setBusyLabel(null)
    }
  }

  const updateSavedList = (saved: SavedReviewSummary) => {
    setSavedReviews((items) => [saved, ...items.filter((item) => item.saved_id !== saved.saved_id)])
  }

  const saveCurrentReview = async () => {
    if (!review || busy) return
    setBusyLabel(activeSaved ? 'Updating the saved review…' : 'Saving this review…')
    setError(null)
    try {
      const saved = activeSaved
        ? await api.updateSavedReview(activeSaved.saved_id, review.review_id, activeSaved.revision)
        : await api.saveReview(review.review_id)
      setActiveSaved(saved)
      updateSavedList(saved)
      setNotice(activeSaved ? `Saved copy updated to revision ${saved.revision}.` : 'Review saved explicitly to your private Supabase records.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The review could not be saved. Your local review was kept.')
      setNotice('Save failed. Your local review remains open and unchanged.')
    } finally {
      setBusyLabel(null)
    }
  }

  const openSaved = async (summary: SavedReviewSummary) => {
    if (busy) return
    setBusyLabel('Opening the saved review as a temporary working copy…')
    setError(null)
    try {
      const saved = await api.openSavedReview(summary.saved_id)
      setReview(saved.review)
      setActiveSaved(saved)
      updateSavedList(saved)
      setNotice(`Saved revision ${saved.revision} opened. Changes remain temporary until you choose Update saved copy.`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The saved review could not be opened.')
      setNotice('Open failed. The current local review was kept.')
    } finally {
      setBusyLabel(null)
    }
  }

  const deleteSaved = async (summary: SavedReviewSummary) => {
    if (busy) return
    setBusyLabel('Deleting the selected saved copy…')
    setError(null)
    try {
      await api.deleteSavedReview(summary.saved_id, summary.revision)
      setSavedReviews((items) => items.filter((item) => item.saved_id !== summary.saved_id))
      if (activeSaved?.saved_id === summary.saved_id) setActiveSaved(null)
      setNotice('Saved copy deleted. Any open local working copy was kept.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The saved copy could not be deleted.')
      setNotice('Delete failed. No local review was removed.')
    } finally {
      setBusyLabel(null)
    }
  }

  const exportSaved = async (summary: SavedReviewSummary, format: 'json' | 'txt') => {
    if (busy) return
    setBusyLabel('Validating and exporting the saved canonical record…')
    setError(null)
    try {
      await downloadSavedExport(summary.saved_id, summary.mode, format)
      setNotice(`Saved ${format.toUpperCase()} export downloaded.`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The saved export failed.')
      setNotice('Saved export failed. No incomplete download was presented.')
    } finally {
      setBusyLabel(null)
    }
  }

  const submitReview = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await runReviewAction(
      'Creating an editable live review…',
      () => api.createReview({
        text: answer,
        intended_use: intendedUse,
        context,
        source_urls: sourceUrls.split('\n').map((value) => value.trim()).filter(Boolean),
      }),
      'Live review created. Initial claims are editable sentence segments, not AI conclusions.',
    )
  }

  const endSession = async () => {
    setAuthBusy(true)
    setAuthMessage(null)
    try {
      await signOut()
      setAuthSession(null)
      setPasswordRecoveryReady(false)
      if (review?.mode === 'live' || activeSaved) setReview(null)
      setActiveSaved(null)
      setSavedReviews([])
      setNotice('Signed out. The public demonstration remains available.')
    } catch (reason) {
      setAuthSession(null)
      setPasswordRecoveryReady(false)
      if (review?.mode === 'live' || activeSaved) setReview(null)
      setActiveSaved(null)
      setSavedReviews([])
      setAuthMessage(reason instanceof Error ? reason.message : 'The browser session was cleared.')
    } finally {
      setAuthBusy(false)
    }
  }

  const completeAuthentication = async (session: Session, destination: string) => {
    try {
      await api.authMe()
      setAuthSession(session)
      setAuthMessage(null)
      navigateBrowser(destination, true)
    } catch (reason) {
      await clearLocalSession()
      setAuthSession(null)
      throw new Error(
        reason instanceof Error
          ? `The backend rejected the new session: ${reason.message}`
          : 'The backend rejected the new session. Please sign in again.',
      )
    }
  }

  const exploreDemo = async () => {
    if (busy) return
    setBusyLabel('Opening the curated demonstration…')
    setError(null)
    try {
      setReview(await api.createDemo())
      setNotice('Demonstration loaded. Its assessment is predefined and clearly labeled.')
      navigateBrowser('/', true)
    } catch (reason) {
      setAuthMessage(reason instanceof Error ? reason.message : 'The public demonstration could not be opened.')
    } finally {
      setBusyLabel(null)
    }
  }

  const pathname = new URL(location, window.location.origin).pathname
  const authRoute = authRoutes[pathname]
  if (authRoute) {
    return (
      <AuthPages
        route={authRoute}
        session={authSession}
        authReady={authReady}
        backendAuthAvailable={authAvailable}
        passwordRecoveryReady={passwordRecoveryReady}
        authMessage={authMessage}
        clearAuthMessage={() => setAuthMessage(null)}
        navigate={navigateBrowser}
        onAuthenticated={completeAuthentication}
        onSignOut={endSession}
        onExploreDemo={exploreDemo}
      />
    )
  }

  if (pathname === '/chat') {
    return (
      <ChatPage
        session={authSession}
        authReady={authReady}
        authAvailable={authAvailable}
        navigate={navigateBrowser}
        onSignOut={endSession}
      />
    )
  }

  return (
    <div className="min-h-screen">
      <a href="#main-content" className="fixed -top-20 left-3 z-50 rounded-md bg-accent px-4 py-2 font-bold text-accent-ink transition-[top] focus:top-3">Skip to review</a>
      <header className="sticky top-0 z-40 border-b border-line bg-canvas/90 shadow-[0_10px_34px_rgba(0,0,0,0.28)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-[94rem] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-7">
          <button type="button" className="min-w-0 rounded-md" onClick={() => navigateBrowser('/')} aria-label="Research Guard evidence review">
            <BrandLockup subtitle="Evidence review workspace" />
          </button>
          <nav aria-label="Primary navigation" className="order-3 flex w-full items-center gap-1 overflow-x-auto rounded-md bg-deep p-1 md:order-none md:w-auto">
            <button type="button" aria-current="page" className="min-h-10 shrink-0 rounded-sm bg-accent px-3.5 py-2 text-sm font-bold text-accent-ink">Evidence review</button>
            <button type="button" className="min-h-10 shrink-0 rounded-sm px-3.5 py-2 text-sm font-bold text-muted transition hover:bg-panel hover:text-ink" onClick={() => navigateBrowser('/chat')}>
              AI chat <span className="ml-1 font-mono text-[0.55rem] uppercase text-warm-ink">unchecked</span>
            </button>
            {authSession && <button type="button" className="min-h-10 shrink-0 rounded-sm px-3.5 py-2 text-sm font-bold text-muted transition hover:bg-panel hover:text-ink" onClick={() => document.getElementById('saved-reviews-title')?.scrollIntoView({ behavior: 'smooth' })}>Saved reviews <span className="ml-1 rounded-full bg-accent/15 px-1.5 text-xs text-accent">{savedReviews.length}</span></button>}
          </nav>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden text-right font-mono text-[0.62rem] leading-5 text-muted sm:block">
              <p className="font-bold text-ink">{!authReady ? 'Checking sign-in…' : authSession ? 'Signed in' : 'Signed out'}</p>
              {authSession?.user.email && <p className="max-w-48 truncate">{authSession.user.email}</p>}
            </div>
            {authSession ? (
              <>
                <button type="button" className={secondaryButton} onClick={() => navigateBrowser('/account')}>Account</button>
                <button type="button" className={secondaryButton} disabled={authBusy} onClick={endSession}>Sign out</button>
              </>
            ) : (
              <button type="button" className={primaryButton} disabled={!authReady || !authAvailable} onClick={() => navigateBrowser('/login')}>
                Sign in
              </button>
            )}
          </div>
        </div>
        <WorkflowStrip />
      </header>

      <main id="main-content" tabIndex={-1} className="mx-auto max-w-[94rem] px-4 py-7 sm:px-7 sm:py-10">
        <section className="relative mb-8 overflow-hidden rounded-lg border border-line bg-paper/75 px-5 py-8 shadow-card sm:px-8 sm:py-11 lg:px-12">
          <div aria-hidden="true" className="absolute -right-24 -top-32 size-96 rounded-full bg-accent/8 blur-3xl" />
          <div className="max-w-4xl">
            <SectionLabel>Evidence before conclusion // review workspace</SectionLabel>
            <h1 className="relative mt-4 font-serif text-5xl leading-[0.98] tracking-tight text-ink sm:text-7xl">
              Check the evidence.<br /><span className="italic text-accent">Keep the qualifications.</span>
            </h1>
            <p className="relative mt-5 max-w-2xl text-base leading-7 text-muted sm:text-lg">Separate what was observed from what was inferred. Inspect source access and limitations, then record your own conclusion.</p>
          </div>
        </section>

        <div aria-live="polite" aria-atomic="true" className="mb-5 min-h-12">
          {busyLabel ? (
            <div role="status" className="flex items-center gap-3 rounded-xl border border-accent/20 bg-soft px-4 py-3 text-sm font-bold text-accent-dark"><Spinner />{busyLabel}</div>
          ) : error ? (
            <div role="alert" className="rounded-xl border border-danger/25 bg-danger-soft px-4 py-3 text-sm font-bold text-danger">{error}</div>
          ) : (
            <p role="status" className="rounded-xl border border-line bg-paper/70 px-4 py-3 text-sm text-muted">{notice}</p>
          )}
        </div>

        {authMessage && (
          <div role="alert" className="mb-5 rounded-xl border border-danger/25 bg-danger-soft px-4 py-3 text-sm font-bold text-danger">
            {authMessage}
          </div>
        )}

        {authReady && !authSession && (
          <div className="mb-5 rounded-xl border border-line bg-paper/70 px-4 py-3 text-sm leading-6 text-muted">
            <strong className="text-ink">You are signed out.</strong>{' '}
            The curated demonstration is public. Sign in with Google to create live reviews or call the model service.
            {!authAvailable && ' Supabase public configuration has not been added to both the frontend and backend yet.'}
          </div>
        )}

        {(configError || (config && !config.model_configured)) && (
          <div className="mb-5 rounded-xl border border-warm-ink/20 bg-warm/55 px-4 py-3 text-sm leading-6 text-warm-ink">
            <strong>{configError ? 'Local service status unavailable.' : 'Live model service unavailable.'}</strong>{' '}
            {configError ? 'The interface could not read backend configuration.' : config?.model_detail}
            {' '}The curated demonstration and public-source retrieval remain available.
          </div>
        )}

        {authSession && config && !config.persistence_configured && (
          <div className="mb-5 rounded-xl border border-warm-ink/20 bg-warm/55 px-4 py-3 text-sm leading-6 text-warm-ink">
            <strong>Saved-review service unavailable.</strong>{' '}
            Configure the backend Supabase publishable key and apply the Phase G migration. Unsaved reviews remain temporary.
          </div>
        )}

        <div className="grid items-start gap-6 lg:grid-cols-[22rem_minmax(0,1fr)] xl:grid-cols-[24rem_minmax(0,1fr)]">
          <aside className="rounded-lg border border-line bg-paper/85 p-5 shadow-card lg:sticky lg:top-32 sm:p-6">
            <SectionLabel>01 / Define</SectionLabel>
            <h2 className="mt-3 font-serif text-3xl text-ink">What needs checking?</h2>
            <p className="mt-2 text-sm leading-6 text-muted">Use public or synthetic research text. Do not enter patient data or private laboratory information.</p>
            <form className="mt-6" onSubmit={submitReview}>
              <label htmlFor="answer" className="text-sm font-black text-ink">Answer or claim to review</label>
              <textarea id="answer" required maxLength={12000} rows={7} className={inputClass} placeholder="Paste a research answer here…" value={answer} onChange={(event) => setAnswer(event.target.value)} />
              <label htmlFor="intended-use" className="mt-4 block text-sm font-black text-ink">Intended use</label>
              <select id="intended-use" className={inputClass} value={intendedUse} onChange={(event) => setIntendedUse(event.target.value as IntendedUse)}>
                <option>topic understanding</option>
                <option>assay interpretation</option>
                <option>presentation preparation</option>
                <option>experiment planning</option>
              </select>

              <button type="button" className={cx(quietButton, 'mt-3')} aria-expanded={showContext} onClick={() => setShowContext((value) => !value)}>
                {showContext ? 'Hide' : 'Add'} experimental context <span aria-hidden="true">{showContext ? '−' : '+'}</span>
              </button>
              {showContext && (
                <div className="mt-2 space-y-3 rounded-xl border border-line bg-canvas p-3">
                  {([
                    ['organism_model', 'Organism or model'],
                    ['assay', 'Assay'],
                    ['reagent', 'Reagent and catalog identifier'],
                    ['conditions', 'Conditions'],
                  ] as const).map(([key, label]) => (
                    <label key={key} className="block text-xs font-black text-ink">{label}
                      <input className={cx(inputClass, 'mt-1.5')} maxLength={key === 'conditions' ? 1500 : 500} value={context[key]} onChange={(event) => setContext((value) => ({ ...value, [key]: event.target.value }))} />
                    </label>
                  ))}
                </div>
              )}

              <label htmlFor="source-urls" className="mt-4 block text-sm font-black text-ink">Public source URLs <span className="font-normal text-muted">optional; one per line</span></label>
              <textarea id="source-urls" rows={3} className={inputClass} placeholder="https://pubmed.ncbi.nlm.nih.gov/…" value={sourceUrls} onChange={(event) => setSourceUrls(event.target.value)} />
              <p className="mt-2 text-xs leading-5 text-muted">Up to three supported PubMed, PMC, or exact CYTO-ID manufacturer links.</p>
              <button type="submit" disabled={busy || !answer.trim() || !authSession} className={cx(primaryButton, 'mt-5 w-full gap-2')}>Start live review <ArrowIcon /></button>
              {!authSession && <p className="mt-2 text-xs leading-5 text-muted">Google sign-in is required for live requests. The demonstration below stays public.</p>}
            </form>

            <div className="my-6 flex items-center gap-3 text-xs font-bold uppercase tracking-widest text-muted"><span className="h-px flex-1 bg-line" />or<span className="h-px flex-1 bg-line" /></div>
            <SectionLabel>Curated worked example</SectionLabel>
            <h3 className="mt-3 text-lg font-black leading-snug text-ink">More fluorescent spots.<br />More cellular activity?</h3>
            <p className="mt-2 text-sm leading-6 text-muted">Synthetic context with archived public extracts. It makes no live request.</p>
            <button type="button" disabled={busy} className={cx(secondaryButton, 'mt-4 w-full gap-2')} onClick={() => runReviewAction('Opening the curated demonstration…', api.createDemo, 'Demonstration loaded. Its assessment is predefined and clearly labeled.')}>Open demonstration <ArrowIcon /></button>

            {authSession && (
              <section className="mt-6 border-t border-line pt-6" aria-labelledby="saved-reviews-title">
                <SectionLabel>Private records</SectionLabel>
                <h3 id="saved-reviews-title" className="mt-3 text-lg font-black text-ink">Your saved reviews</h3>
                <p className="mt-2 text-sm leading-6 text-muted">Opening creates a temporary working copy. Changes are stored only when you choose Update saved copy.</p>
                <button type="button" className={cx(quietButton, 'mt-2')} disabled={busy || savedLoading || !config?.persistence_configured} onClick={refreshSavedReviews}>Refresh saved reviews</button>
                {savedLoading && <p role="status" className="mt-3 text-sm text-muted">Loading saved reviews…</p>}
                {savedError && <p role="alert" className="mt-3 text-sm font-bold text-danger">{savedError}</p>}
                {!savedLoading && !savedError && savedReviews.length === 0 && (
                  <p className="mt-3 rounded-lg border border-dashed border-line p-3 text-sm text-muted">No reviews have been explicitly saved.</p>
                )}
                <div className="mt-3 space-y-3">
                  {savedReviews.map((saved) => (
                    <article key={saved.saved_id} className="rounded-md border border-line bg-panel p-3">
                      <p className="break-words text-sm font-black text-ink">{saved.title}</p>
                      <p className="mt-1 text-xs text-muted">{saved.mode} · revision {saved.revision} · schema {saved.schema_version}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button type="button" className={quietButton} disabled={busy || activeSaved?.saved_id === saved.saved_id} onClick={() => openSaved(saved)}>Open</button>
                        <button type="button" className={quietButton} disabled={busy} onClick={() => exportSaved(saved, 'json')}>JSON</button>
                        <button type="button" className={quietButton} disabled={busy} onClick={() => exportSaved(saved, 'txt')}>TXT</button>
                        <button type="button" className={cx(quietButton, 'text-danger')} disabled={busy} onClick={() => deleteSaved(saved)}>Delete saved copy</button>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            )}
          </aside>

          <section aria-busy={busy} className="min-w-0">
            {!review ? <EmptyReview /> : (
              <div className="space-y-5">
                <header className={cx('rounded-lg border p-5 shadow-card sm:p-7', review.mode === 'demo' ? 'border-warm-ink/20 bg-warm/60' : 'border-line bg-paper')}>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <span className={cx('inline-flex rounded-full px-3 py-1.5 font-mono text-xs font-black uppercase tracking-wider', review.mode === 'demo' ? 'bg-warm-ink text-deep' : 'bg-accent text-accent-ink')}>
                        {review.mode === 'demo' ? 'Demonstration — not a live verification' : 'Live review'}
                      </span>
                      <h2 className="mt-4 font-serif text-3xl text-ink sm:text-4xl">{review.claims.length} claim{review.claims.length === 1 ? '' : 's'} to inspect</h2>
                      <p className="mt-2 text-sm leading-6 text-muted">{review.extraction_method}</p>
                      <p className="mt-2 text-xs font-bold text-muted">{activeEvidenceCount} current source record{activeEvidenceCount === 1 ? '' : 's'} · {review.mode === 'demo' ? 'curated result' : 'retrieved material only'}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {authSession && config?.persistence_configured && (
                        <button type="button" disabled={busy} className={primaryButton} onClick={saveCurrentReview}>
                          {activeSaved ? `Update saved copy (revision ${activeSaved.revision})` : 'Save this review'}
                        </button>
                      )}
                      <button type="button" disabled={busy} className={secondaryButton} onClick={() => runExport('json')}>Export JSON</button>
                      <button type="button" disabled={busy} className={secondaryButton} onClick={() => runExport('txt')}>Export readable TXT</button>
                    </div>
                  </div>
                  {review.mode === 'demo' && <p className="mt-4 rounded-md bg-panel/65 p-3 text-sm font-bold leading-6 text-warm-ink">This predefined demonstration uses synthetic experimental context and archived public extracts. It is never substituted for a failed live review.</p>}
                  {review.missing_fields.length > 0 && <p className="mt-4 text-sm text-muted"><strong className="text-ink">Context not supplied:</strong> {review.missing_fields.join(', ')}</p>}
                  {review.mode === 'live' && (
                    <button type="button" disabled={busy} className={cx(secondaryButton, 'mt-4')} onClick={() => runReviewAction('Extracting claims with the configured model…', () => api.extract(review.review_id), 'Claims extracted. Review and edit each one before retrieval.')}>Extract claims with AI</button>
                  )}
                </header>

                {review.claims.map((claim, index) => (
                  <ClaimCard
                    key={[
                      claim.claim_id,
                      claim.text,
                      claim.assessment?.suggested_wording ?? 'unassessed',
                      claim.assessment_error ?? '',
                      claim.decision.status,
                      claim.decision.final_wording,
                      claim.decision.notes,
                      ...Object.values(review.original_input.context),
                    ].join('|')}
                    review={review}
                    claim={claim}
                    index={index}
                    busy={busy}
                    runReviewAction={runReviewAction}
                  />
                ))}

                <footer className="rounded-lg border border-line bg-paper p-5 text-sm leading-6 text-muted sm:p-6">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="max-w-2xl">
                      <SectionLabel>05 / Record</SectionLabel>
                      <h2 className="mt-2 font-serif text-2xl text-ink">Keep the evidence trail</h2>
                      <p className="mt-2">Exports include the mode, original input, source passages, access history, model provenance, validation results, and researcher decisions.</p>
                    </div>
                    <details>
                      <summary className="min-h-10 py-2 font-black text-accent">Validation and provenance</summary>
                      <pre className="mt-3 max-h-80 max-w-full overflow-auto whitespace-pre-wrap break-words rounded-xl bg-canvas p-4 text-xs text-ink">{JSON.stringify({ model_runs: review.model_runs, validation: review.validation_results, notices: review.notices }, null, 2)}</pre>
                    </details>
                  </div>
                </footer>
              </div>
            )}
          </section>
        </div>
      </main>
      <footer className="mt-10 border-t border-line bg-deep/80">
        <div className="mx-auto flex max-w-[94rem] flex-wrap justify-between gap-3 px-4 py-6 text-xs leading-5 text-muted sm:px-7">
          <span className="font-mono uppercase tracking-wider text-accent">Research Guard AI</span>
          <span>Research support with researcher judgment at every step.</span>
          <span className="font-mono">Temporary drafts · explicit private saves only</span>
        </div>
      </footer>
    </div>
  )
}

export default App
