interface BrandMarkProps {
  className?: string
}

export function BrandMark({ className = 'size-10' }: BrandMarkProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 48 48"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M24 3.5 41.5 13.6v20.8L24 44.5 6.5 34.4V13.6L24 3.5Z" fill="#0b2c26" stroke="currentColor" strokeWidth="1.8" />
      <path d="M24 9v11.2m0 7.6V39M10.8 16.4l9.7 5.6m7 4 9.7 5.6m0-15.2L27.5 22m-7 4-9.7 5.6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="24" cy="24" r="4.4" fill="currentColor" />
      <circle cx="24" cy="8.5" r="2" fill="#071616" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="37.5" cy="16.2" r="2" fill="#071616" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="37.5" cy="31.8" r="2" fill="#071616" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="24" cy="39.5" r="2" fill="#071616" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="10.5" cy="31.8" r="2" fill="#071616" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="10.5" cy="16.2" r="2" fill="#071616" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  )
}

export function BrandLockup({ subtitle }: { subtitle: string }) {
  return (
    <span className="flex min-w-0 items-center gap-3 text-left">
      <span className="text-accent drop-shadow-[0_0_14px_rgba(78,222,163,0.25)]">
        <BrandMark className="size-10 shrink-0" />
      </span>
      <span className="min-w-0">
        <span className="flex items-center gap-2">
          <b className="block truncate font-serif text-lg font-semibold leading-none text-ink">Research Guard</b>
          <span className="hidden rounded-sm bg-accent/10 px-1.5 py-1 font-mono text-[0.55rem] font-bold uppercase tracking-[0.14em] text-accent sm:inline">AI</span>
        </span>
        <span className="mt-1 block truncate font-mono text-[0.62rem] uppercase tracking-[0.1em] text-muted">{subtitle}</span>
      </span>
    </span>
  )
}

export function WorkflowStrip({ active = 1 }: { active?: number }) {
  return (
    <div aria-label="Review workflow" className="overflow-x-auto border-b border-line bg-deep/85 px-4 sm:px-7">
      <ol className="mx-auto flex min-w-max max-w-[94rem] items-center gap-5 py-2.5 font-mono text-[0.64rem] font-semibold uppercase tracking-[0.08em] text-muted sm:gap-8">
        {['Define', 'Risk', 'Assist', 'Verify', 'Record'].map((step, index) => {
          const number = index + 1
          const current = number === active
          return (
            <li key={step} className={current ? 'text-ink' : undefined} aria-current={current ? 'step' : undefined}>
              <span className={`mr-2 inline-grid size-5 place-items-center rounded-full ${current ? 'bg-accent text-deep' : 'bg-panel text-muted'}`}>{number}</span>
              {step}{number < 5 && <span aria-hidden="true" className="ml-5 text-line sm:ml-8">›</span>}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
