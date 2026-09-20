import { useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api } from './api'
import { BrandLockup, WorkflowStrip } from './Brand'
import type { ChatMessageInput, ChatProviderId, ChatProviderOption, ChatProviderStatus } from './types'

interface ChatPageProps {
  session: Session | null
  authReady: boolean
  authAvailable: boolean
  navigate: (path: string, replace?: boolean) => void
  onSignOut: () => Promise<void>
}

interface DisplayMessage extends ChatMessageInput {
  id: string
  provider?: ChatProviderId
  model?: string
  fallbackUsed?: boolean
  failed?: boolean
}

const fieldClass =
  'w-full rounded-md border border-line bg-deep/80 px-3.5 py-3 text-sm text-ink shadow-sm transition placeholder:text-muted/60 hover:border-accent/50 focus:border-accent focus:shadow-[inset_0_0_10px_rgba(78,222,163,0.08)]'
const primaryButton =
  'inline-flex min-h-11 items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-black text-accent-ink shadow-[0_0_18px_rgba(78,222,163,0.14)] transition hover:bg-accent-dark hover:shadow-[0_0_24px_rgba(78,222,163,0.24)] disabled:hover:bg-accent'
const secondaryButton =
  'inline-flex min-h-11 items-center justify-center rounded-md border border-accent/25 bg-accent/5 px-4 py-2.5 text-sm font-black text-accent transition hover:border-accent/60 hover:bg-accent/10'

function Spinner() {
  return <span aria-hidden="true" className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
}

function providerState(provider: ChatProviderOption): string {
  if (provider.configured) return 'Available'
  if (provider.state === 'free_tier_unconfirmed') return 'Free tier not confirmed'
  return 'API key missing'
}

export default function ChatPage({ session, authReady, authAvailable, navigate, onSignOut }: ChatPageProps) {
  const [status, setStatus] = useState<ChatProviderStatus | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [providerId, setProviderId] = useState<ChatProviderId>('gemini')
  const [model, setModel] = useState('')
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [allowFallback, setAllowFallback] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!session) return
    let active = true
    api.chatProviders()
      .then((value) => {
        if (!active) return
        setStatus(value)
        const preferred = value.providers.find((item) => item.id === 'gemini' && item.configured)
          ?? value.providers.find((item) => item.configured)
          ?? value.providers[0]
        if (preferred) {
          setProviderId(preferred.id)
          setModel(preferred.models[0]?.id ?? '')
        }
      })
      .catch((reason) => {
        if (active) setStatusError(reason instanceof Error ? reason.message : 'Provider status could not be loaded.')
      })
    return () => { active = false }
  }, [session])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, busy])

  const provider = useMemo(
    () => status?.providers.find((item) => item.id === providerId) ?? null,
    [providerId, status],
  )

  const changeProvider = (next: ChatProviderId) => {
    const selected = status?.providers.find((item) => item.id === next)
    setProviderId(next)
    setModel(selected?.models[0]?.id ?? '')
    setError(null)
  }

  const send = async (event?: FormEvent) => {
    event?.preventDefault()
    const content = draft.trim()
    if (!content || busy || !provider?.configured || !model) return
    const userMessage: DisplayMessage = { id: crypto.randomUUID(), role: 'user', content }
    const requestHistory = [...messages.filter((message) => !message.failed), userMessage].slice(-24)
    setMessages((current) => [...current, userMessage].slice(-24))
    setDraft('')
    setBusy(true)
    setError(null)
    try {
      const result = await api.chat(
        providerId,
        model,
        requestHistory.map(({ role, content: text }) => ({ role, content: text })),
        allowFallback,
      )
      const assistantMessage: DisplayMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: result.answer,
        provider: result.provider,
        model: result.model,
        fallbackUsed: result.fallback_used,
      }
      setMessages((current) => [...current, assistantMessage].slice(-24))
    } catch (reason) {
      setMessages((current) => current.map((message) => (
        message.id === userMessage.id ? { ...message, failed: true } : message
      )))
      setError(reason instanceof Error ? reason.message : 'The chat request failed without a response.')
    } finally {
      setBusy(false)
    }
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void send()
    }
  }

  return (
    <div className="min-h-screen">
      <a href="#chat-main" className="fixed -top-20 left-3 z-50 rounded-md bg-accent px-4 py-2 font-bold text-accent-ink transition-[top] focus:top-3">Skip to chat</a>
      <header className="sticky top-0 z-40 border-b border-line bg-canvas/90 shadow-[0_10px_34px_rgba(0,0,0,0.28)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-[94rem] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-7">
          <button type="button" className="min-w-0 rounded-md" onClick={() => navigate('/')} aria-label="Research Guard evidence review">
            <BrandLockup subtitle="General AI assistant" />
          </button>
          <nav aria-label="Primary navigation" className="order-3 flex w-full items-center gap-1 overflow-x-auto rounded-md bg-deep p-1 md:order-none md:w-auto">
            <button type="button" className="min-h-10 shrink-0 rounded-sm px-3.5 py-2 text-sm font-bold text-muted transition hover:bg-panel hover:text-ink" onClick={() => navigate('/')}>Evidence review</button>
            <button type="button" aria-current="page" className="min-h-10 shrink-0 rounded-sm bg-accent px-3.5 py-2 text-sm font-bold text-accent-ink">AI chat <span className="ml-1 font-mono text-[0.55rem] uppercase">unchecked</span></button>
          </nav>
          <nav aria-label="Account actions" className="flex flex-wrap items-center gap-2">
            {session ? (
              <>
                <button type="button" className={secondaryButton} onClick={() => navigate('/account')}>Account</button>
                <button type="button" className={secondaryButton} onClick={() => void onSignOut()}>Sign out</button>
              </>
            ) : (
              <button type="button" className={primaryButton} disabled={!authReady || !authAvailable} onClick={() => navigate('/login?next=/chat')}>Sign in</button>
            )}
          </nav>
        </div>
        <WorkflowStrip active={3} />
      </header>

      <main id="chat-main" tabIndex={-1} className="mx-auto max-w-[94rem] px-4 py-7 sm:px-7 sm:py-10">
        <div className="mb-6 grid gap-5 border-b border-line pb-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-3xl">
          <p className="font-mono text-[0.68rem] font-black uppercase tracking-[0.18em] text-warm-ink">Unchecked general model inference</p>
          <h1 className="mt-3 font-serif text-4xl leading-tight text-ink sm:text-5xl">Research assistant chat</h1>
          <p className="mt-3 text-sm leading-6 text-muted sm:text-base">Ask general research questions using a configured AI provider. These replies are model output and are not evidence-checked.</p>
          </div>
          <div className="rounded-md border border-warm-ink/20 bg-warm/45 px-4 py-3 font-mono text-xs leading-5 text-warm-ink">Use chat to explore a question.<br />Use evidence review to check claims.</div>
        </div>

        {!authReady ? (
          <div role="status" className="flex min-h-80 items-center justify-center gap-3 rounded-2xl border border-line bg-paper shadow-card"><Spinner /> Checking your sign-in…</div>
        ) : !session ? (
          <section className="grid min-h-80 place-items-center rounded-lg border border-line bg-paper p-8 text-center shadow-card">
            <div className="max-w-md">
              <h2 className="font-serif text-3xl text-ink">Sign in to use AI chat</h2>
              <p className="mt-3 text-sm leading-6 text-muted">Authentication protects the server-side provider keys and applies request limits to each account. The public evidence demonstration remains available without signing in.</p>
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <button type="button" className={primaryButton} disabled={!authAvailable} onClick={() => navigate('/login?next=/chat')}>Sign in or create account</button>
                <button type="button" className={secondaryButton} onClick={() => navigate('/')}>Open evidence review</button>
              </div>
            </div>
          </section>
        ) : (
          <section className="overflow-hidden rounded-lg border border-line bg-paper/90 shadow-card">
            <div className="grid gap-4 border-b border-line bg-panel/70 p-4 md:grid-cols-[1fr_1fr_auto] md:items-end sm:p-5">
              <div>
                <label htmlFor="chat-provider" className="text-sm font-black text-ink">AI provider</label>
                <select id="chat-provider" className={`${fieldClass} mt-2`} value={providerId} onChange={(event) => changeProvider(event.target.value as ChatProviderId)} disabled={!status || busy}>
                  {status?.providers.map((item) => <option key={item.id} value={item.id}>{item.display_name} — {providerState(item)}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="chat-model" className="text-sm font-black text-ink">Model</label>
                <select id="chat-model" className={`${fieldClass} mt-2`} value={model} onChange={(event) => setModel(event.target.value)} disabled={!provider || busy}>
                  {provider?.models.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
                </select>
              </div>
              <button type="button" className={secondaryButton} disabled={busy || messages.length === 0} onClick={() => { setMessages([]); setError(null) }}>Clear chat</button>
              {status?.fallback_enabled && (
                <label className="flex min-h-11 items-center gap-2 text-sm text-muted md:col-span-3">
                  <input type="checkbox" checked={allowFallback} onChange={(event) => setAllowFallback(event.target.checked)} />
                  Try another configured free-tier provider after a timeout, outage, rate limit, or unavailable model. The actual provider will be shown.
                </label>
              )}
            </div>

            {statusError && <div role="alert" className="m-4 rounded-xl border border-danger/25 bg-danger-soft px-4 py-3 text-sm font-bold text-danger">{statusError}</div>}
            {provider && !provider.configured && (
              <div role="status" className="m-4 rounded-xl border border-warm-ink/20 bg-warm/60 px-4 py-3 text-sm text-warm-ink">
                <b>{provider.display_name} is unavailable.</b> {provider.state === 'missing_api_key' ? 'Its API key is missing from the backend.' : 'Its free-tier/no-billing confirmation is missing from the backend.'}
              </div>
            )}

            <div className="min-h-[24rem] max-h-[58vh] space-y-4 overflow-y-auto p-4 sm:p-6" aria-live="polite" aria-busy={busy}>
              {messages.length === 0 && (
                <div className="grid min-h-72 place-items-center text-center">
                  <div className="max-w-md"><div className="mx-auto grid size-14 place-items-center rounded-full bg-soft text-xl text-accent">?</div><h2 className="mt-4 font-serif text-2xl text-ink">What would you like to understand?</h2><p className="mt-2 text-sm leading-6 text-muted">Use public or synthetic information. Do not paste patient data, unpublished results, or private laboratory details.</p></div>
                </div>
              )}
              {messages.map((message) => (
                <article key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[88%] rounded-lg px-4 py-3 text-sm leading-6 sm:max-w-[76%] ${message.role === 'user' ? 'rounded-br-sm bg-accent text-accent-ink' : 'rounded-bl-sm border border-line bg-panel text-ink'}`}>
                    <p className="whitespace-pre-wrap break-words">{message.content}</p>
                    {message.role === 'user' && message.failed && (
                      <p className="mt-2 border-t border-accent-ink/25 pt-2 text-xs">Request failed; this message will not be included in later model context.</p>
                    )}
                    {message.role === 'assistant' && message.provider && (
                      <p className="mt-3 border-t border-line pt-2 text-xs text-muted">Generated by {message.provider} · {message.model}{message.fallbackUsed ? ' · fallback used' : ''} · not evidence-checked</p>
                    )}
                  </div>
                </article>
              ))}
              {busy && <div role="status" className="flex items-center gap-3 text-sm font-bold text-muted"><Spinner /> Waiting for {provider?.display_name ?? 'the provider'}…</div>}
              <div ref={endRef} />
            </div>

            <form className="border-t border-line bg-panel/70 p-4 sm:p-5" onSubmit={send}>
              {error && <div role="alert" className="mb-3 rounded-xl border border-danger/25 bg-danger-soft px-4 py-3 text-sm font-bold text-danger">{error}</div>}
              <label htmlFor="chat-message" className="sr-only">Message</label>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                <textarea id="chat-message" rows={3} maxLength={4000} className={fieldClass} value={draft} disabled={busy} placeholder="Ask a research question…" onChange={(event) => setDraft(event.target.value)} onKeyDown={handleKeyDown} />
                <button type="submit" className={`${primaryButton} shrink-0 sm:min-w-28`} disabled={busy || !draft.trim() || !provider?.configured || !model}>{busy ? <><Spinner /> <span className="ml-2">Sending</span></> : 'Send'}</button>
              </div>
              <div className="mt-2 flex flex-wrap justify-between gap-2 text-xs text-muted"><span>Enter to send · Shift+Enter for a new line</span><span>{draft.length}/4000</span></div>
            </form>
          </section>
        )}
      </main>
    </div>
  )
}
