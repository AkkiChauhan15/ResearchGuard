# Research Guard AI migration plan

Migration Phases A–D completed: 2026-09-18. Phase E is implemented and fixture-tested;
its required live check is blocked. Phase F is implemented and fixture-tested; its
real OAuth browser round trip is blocked by missing dashboard configuration.
**No phase after F has been executed.**

The user approved FastAPI, React + TypeScript + Tailwind, Supabase Free for Google
sign-in and explicit saves, and Gemini Developer API via an AI Studio Free Tier
project. The application remains local. No paid services, billing activation,
credit purchases, paid fallback, or public deployment are authorized.

The user supplies Phases B–H sequentially, one phase at a time. Phases B–F were
supplied; definitions and implementation order for G–H remain reserved
for those instructions. Do not infer or execute later work. Preserve the original
scientific requirements in `context.md`.

## Phase A — repository audit and verified baseline

Read `context.md`, `PROGRESS.md`, `ARCHITECTURE.md`, README, core modules, frontend,
checks, fixtures, and evaluation protocol. No applicable AGENTS.md was found at
repository/ancestor locations; `.agents` and `.codex` are empty. The existing
application, tests, and supporting documents are untracked in git; only a future
explicitly scoped snapshot/commit should establish a rollback point. Do not reset,
clean, or discard this working tree.

### Implemented and verified within stated limits

| Component | Actual files and behavior | Phase A verification |
| --- | --- | --- |
| Typed review records | `researchguard/schemas.py`: Pydantic records, status enums, source/run IDs, provenance, decisions | Existing tests passed; demo/export validate records. No independent successful live model run verified |
| Review logic | `researchguard/reviews.py`: editable sentence segments, targeted missing-product question, accept/edit/reject/pending; edits invalidate assessment and current source linkage | Unit/HTTP tests and browser edits/decisions passed |
| Evidence validation | `assessment.py`: known claim source IDs, whitespace-only quotation matching, exact locations, evidence relationship requirements | Unknown IDs, fabricated quotes/locations, metadata misuse and related negative tests passed; this is not scientific entailment validation |
| Retrieval adapters | `retrieval.py`: PubMed search/metadata/abstracts, PMC available XML, exact Enzo HTML and manual | Existing parser/failure fixtures passed. Cached official PDF locally reparsed into 22 page extracts; no fresh source fetch in A |
| Restricted source transport | `transport.py`: HTTPS host allowlist, public DNS address checks and IP pinning, TLS hostname validation, redirect/MIME/byte limits | Existing unsafe-URL, DNS, redirect and size/type tests passed; not a comprehensive security audit |
| Curated demo | `demo.py`, `data/demo_sources.json`: synthetic case, two archived extracts, no runtime model, pending decisions | Demo validation, source-link/export checks and browser labeling passed |
| Export | `export.py`: validated JSON and TXT with full record appendix, original suggestions preserved | HTTP/unit checks and actual browser JSON download passed |
| Existing local UI/server | `web/*`, `server.py`: vanilla UI, loopback HTTP, transient session-scoped store, one-hour expiry, explicit downloads | Chrome empty/demo/live/error/edit/export/mobile smoke passed; HTTP origin/host/session isolation tests passed |
| Evaluation assets | `data/evaluation_cases.json`, `scripts/evaluate.py`, `docs/EVALUATION.md` | 16/16 fixture consistency checks; separately counted 10 dev / 6 held-out. Zero model cases run; references await human review |

### Implemented but unverified or only partially verified

- Legacy OpenAI Responses extraction/comparison exists, with malformed/refusal/missing-key
  fixture checks. Account access, successful live structured outputs, extraction quality,
  scientific support, context matching, false alarms, and prompt-injection resistance
  remain unverified. OpenAI is a previous candidate, not the active migration provider.
- Prior progress records live PubMed, PMC and Enzo checks on 2026-09-16. The archived
  source metadata and cached document are present, but prior live success does not
  establish current availability. **No live integration was freshly verified in Phase A.**
- Manual parsing succeeds on a cached public PDF; missing-parser, identity and page
  provenance fixtures pass. Arbitrary PDF robustness, all platforms, timeout enforcement
  under hostile documents, and a fresh download-to-browser manual flow are not established.
- The existing browser smoke does not exercise successful live retrieval or live AI.
  It verifies a curated demo and live-mode failure paths. Real end-to-end AI use is absent.
- Concurrency, token lifecycle, authenticated isolation, cross-worker behavior, and saved
  record ownership are not proven by existing single-process HTTP tests.
- `ModelRun` contains claim/source IDs, but no successful real-provider provenance was
  generated. Neither model identifiers nor a configured-key flag certify access.

### Missing features

No FastAPI app/dependency, React package manifest, TypeScript/Tailwind build, Gemini
adapter, Supabase client/schema/migrations, Google sign-in, verified access-token
handling, row-level security (RLS), or persistent saved-review CRUD exists. There
is no saved-review loading/deletion flow, migration schema version, optimistic
concurrency for persisted records, free-quota enforcement workflow, or new-provider
privacy notice. The old provider can still be invoked if someone configures its key;
Phase A documents the prohibition but does not change runtime code.

Known environment variables for Gemini and Supabase were checked for presence only
and were absent. No accounts were inspected or created. FastAPI, Supabase's Python
package and `google.genai` were not installed in the inspected Python environment;
Pydantic is installed. Package absence alone does not determine future SDK choices.

### Checks actually executed

- `python3 -m unittest discover -s tests -v`: initial sandbox attempt hit
  `PermissionError` in HTTP class setup; **not counted as passing**. Rerun with
  loopback permission: **39/39 passed**, no skips.
- `python3 -m compileall -q researchguard scripts tests`: passed.
- `node --check web/app.js`: passed.
- `python3 -m scripts.evaluate`: **16/16 fixture consistency**, **0 model calls**.
  Independently counted the actual split rather than trusting the runner's hardcoded
  summary fields. References are agent-authored drafts, not independent ground truth.
- Existing `scripts/browser_smoke.cjs`, using installed Playwright and Chrome:
  passed; zero page errors; 390px overflow check passed. Temporary loopback preview
  had `OPENAI_API_KEY` unset and was stopped after testing. Screenshots are ignored
  under `test-results/`.
- Actual `manual_record` on `/tmp/researchguard-manual.pdf`: 22 physical page extracts;
  file hash `eecaece65b7125d8abbb325917a824d2b3415adea5c79218f57094b42e574f72`.
  Cached local content only; not a fresh network verification.
- `git diff --check`: passed for tracked changes. Source/test/data/dependency hashes
  were captured before documentation edits and compared afterward to enforce A scope.

The old 36-test result is historical: three manual tests were added afterward, so
39 is the current verified count. The opening progress table was an initial snapshot,
not an accurate current component inventory. No new-stack success is inferred.

## API contract and migration risks

### Existing HTTP contract to capture before replacement

| Route | Current request | Current success response |
| --- | --- | --- |
| `GET /api/config` | No session required | `{model_configured, retention_seconds, mode}`; configuration presence only |
| `POST /api/reviews` | `ReviewInput` JSON, `X-Review-Session` | Full `Review`, HTTP 200, live mode assigned server-side |
| `POST /api/demo` | JSON object, session header | Full curated `Review`, HTTP 200 |
| `POST /api/reviews/{id}/claim` | `{claim_id, text}` | Full updated `Review` |
| `POST /api/reviews/{id}/extract` | JSON object | Full `Review`; replaces claims |
| `POST /api/reviews/{id}/retrieve` | `{claim_id, query}` | Full `Review`; access errors recorded in attempts |
| `POST /api/reviews/{id}/assess` | `{claim_id}` | Full `Review`; expected failures may be HTTP 200 with `assessment=null` and `assessment_error` |
| `POST /api/reviews/{id}/decision` | `{claim_id, decision}` | Full `Review`, preserves original suggestion |
| `GET /api/reviews/{id}/export?format=json\|txt` | Session header | Attachment bytes, JSON or plain text |

Validation/missing-session failures currently use HTTP 400 and `{error: string}`;
unknown route is 404 and unsupported method on a known action is 405. No saved-review
list/get/save/delete endpoints exist. Model errors and retrieval access states must
remain distinguishable from evidence statuses.

| Risk found in code | Required migration control and check |
| --- | --- |
| Browser makes a random header; server merely compares it with stored session | Treat it as an opaque draft capability, never a user ID. Verify Supabase token signature/issuer/audience/expiry using documented support. Derive owner server-side; reject spoofed user IDs, expired tokens and cross-user access |
| Reload creates a new draft session; login currently does not exist | Deliberately define guest-to-user transition. No automatic claiming/uploading of drafts on login. Clear user-specific caches on logout/account switch and avoid responses from a previous identity updating the new session |
| Store and locks live inside one process; NCBI throttle is process-local | Keep one backend worker initially. Use bounded worker execution for blocking HTTP/PDF/model calls; preserve per-review locking, copy-validate-commit behavior, expiry and request limits. Plan cross-worker ownership/rate control before changing this assumption |
| FastAPI defaults differ from current 400 errors and response shapes | Freeze contract fixtures first. Either preserve routes/status/error envelope or version changes and migrate React/tests together. Do not expose Pydantic input echoes, tracebacks or provider secrets |
| Source and review IDs use string prefixes, not database UUID types | Preserve IDs and review payload. Propose a saved-record envelope with owner UUID, review ID text, schema version, revision, timestamps and validated JSON record. Test legacy export round trip |
| Phase A: evidence validators shared a module with the OpenAI adapter | Resolved in E: provider request/response code is isolated while prompts and deterministic validators remain in `assessment.py`; Gemini output is revalidated with Pydantic |
| Phase A: source transport allowlist contained OpenAI | Resolved in E: the OpenAI host was removed; the official Gemini SDK owns its fixed service transport and no arbitrary model URL is configurable |
| A declared free flag cannot prove the account has no billing | Require account-side Free Tier/no-billing verification and an eligible model before live use. Quota/access failure means unavailable; no upgrade, key rotation to evade limits, paid fallback, or credit purchase |
| Existing UI and README described OpenAI processing/retention | Resolved for E: notices describe Gemini Free Tier external processing and no longer claim `store=false`; revise again when Supabase explicit saves exist |
| Browser currently shares backend origin; React dev server likely differs | Choose a local proxy or explicit origin allowlist; configure OAuth redirect/callback URLs deliberately. Retain CSRF/host protections appropriate to chosen token/cookie flow; no wildcard credentialed CORS |
| React effects/retries could repeat model or save actions | User-triggered requests, duplicate-submit protection, bounded retries, and revision checks. Save only on explicit action; reject conflicting revisions instead of overwriting another edit |
| Saved JSON can outlive a schema or be altered through database access | Owner-only RLS for SELECT/INSERT/UPDATE/DELETE, immutable ownership, schema/version checks and backend evidence validation before loading/render/export. No runtime service-role bypass for ordinary user requests |
| Limits are not globally comprehensive | Review size cap is checked on mutations; failed model calls do not all count toward model-run limits. Plan request/attempt quotas separately from successful provenance logs. Do not claim current counters prevent provider usage exhaustion |
| Two source IDs can refer to the same paper; quoted passages can be irrelevant | Preserve validators but do not call their structural checks scientific verification. Distinct IDs do not establish independent evidence. Add scientific/reference review and canonical identity checks where justified later |
| Model-supplied prose and URLs become durable | React renders text without raw HTML; validate links, record integrity and provenance before UI/export. Credentials/tokens must never enter review records or snapshots |

## Phase B — FastAPI HTTP layer

Status: **implemented and verified within local fixture/browser scope**.

`researchguard/api.py` now exposes the existing review services through FastAPI and
Uvicorn. `researchguard/store.py` preserves temporary process-local storage, session
capability checks, one-hour expiry, bounded capacity, and per-review mutation locks.
External synchronous work uses a bounded thread pool with request deadlines; mutations
use copy, validate, size-check, commit semantics. `researchguard/settings.py` validates
limits and exact local frontend origins. The canonical schemas, retrieval adapters,
legacy provider functions, evidence validators, demo, decisions, and exporters remain
separate modules and were not rewritten for the framework change.

The paths were intentionally normalized rather than retaining legacy action endpoints.
Their tested bodies, statuses, error envelope, session requirement, invalidation rules,
limits, CORS behavior, and environment variables are frozen in `docs/API.md` and the
generated local OpenAPI document. The existing vanilla preview calls the new paths so
browser parity can be checked before the later React migration.

Verification evidence: the complete suite passed 40/40, including nine FastAPI/store
tests covering health/config/static delivery, exact CORS, demo/live separation, create
and retrieve review, claim/context edits, fixture retrieval/assessment, decisions,
canonical JSON/TXT exports, invalid/unsafe/oversized input, session isolation, missing
legacy credentials, expiry, bounded worker configuration, request timeout and rollback.
Existing source URL/DNS/redirect/MIME/size/parser and evidence source/quote/location
validation tests remain green. No live retrieval or model call is implied by these tests.

The FastAPI layer is local-only and intentionally single-worker because drafts, locks,
and NCBI throttling are process-local. `X-Review-Session` remains an unauthenticated
temporary capability. React, Gemini, Supabase identity/persistence, cross-worker state,
and public deployment are outside Phase B.

## Phase C — React, TypeScript, and Tailwind interface

Status: **implemented and verified within local build/browser scope**.

`frontend/` now contains a Vite React/TypeScript SPA styled with Tailwind CSS. It uses
the Phase B `/api` contract and keeps its random transient session capability in the
API module. Provider credentials and model SDKs remain server-side; the frontend has
no `VITE_` configuration or provider secret. The Vite development/preview server binds
to `127.0.0.1:5173` and proxies `/api` to FastAPI on port 8000. A production build is
served by FastAPI at `/`, while the retained vanilla interface is available at
`/legacy`.

The SPA implements live input, intended use, optional experiment context and source
URLs; an explicit curated-demo path; editable live claims; observation/inference;
claim-level evidence and access states; quoted passages, limitations, revised wording,
next questions; decisions; and JSON/TXT downloads. Empty, loading, request-error,
partial-access, and missing-model-service states are visible. Demo claims remain
server-protected and prominently labeled, so the browser flow inspects and decides on
the demo before using a separate live review to verify edit invalidation.

The browser only displays sources connected through a claim's current retrieval
attempts. This mirrors the server's invalidation contract: after a material claim edit,
the old assessment and decision are cleared and detached historical sources do not
appear as current evidence. Canonical exports continue to come from FastAPI.

Verification evidence: TypeScript checking, lint, and the production build passed.
Installed Chrome/Playwright completed the React journey against both Vite and the
FastAPI-served production bundle, including keyboard focus, demo evidence/access,
decision/export, live missing-model state, claim-edit invalidation, failed API handling,
and a 390 px mobile overflow check with no page errors. The preserved legacy browser
smoke and all 40 backend/source-validation tests also passed. No live provider or fresh
external-source call is implied.

## Phase D — retrieval adapter verification and repair

Status: **implemented and verified with fixtures plus representative live sources**.

The existing PubMed, PMC, Enzo product-page, and Enzo manual adapters remain in place.
Phase D narrows PubMed XML paths to the requested article so identifiers from cited
references cannot replace the article's own PMID/PMCID/DOI. PubMed search continues to
use one EFetch request per ESearch result under the existing process-wide throttle.
Oversized, malformed, or unavailable individual records are omitted while successful
records remain; omissions appear in both source limitations and the retrieval-attempt
detail. A response that does not contain its requested PMID is now an explicit parse
failure rather than a silent omission.

PMC access level now depends on readable content: only nonempty XML body paragraphs
qualify as `full text`. Abstract content remains `abstract`, including responses with
an empty body element. The exact Enzo product parser now preserves the page's visible
modification date when present. The already-supported manual is linked by the exact
official product page, validates ENZ-51031/CYTO-ID identity, preserves physical PDF
page locations and records its HTTP modification date and response hash.

Read-only live verification retrieved three PubMed abstracts through three individual
EFetch calls; resolved PMID 25484088 to its correct PMCID PMC4502790; retrieved 35 body
paragraphs plus four abstract paragraphs for reusable full-text example PMC8270360;
and confirmed that PMC4502790 supplies one abstract and no body through EFetch. PMC's
reuse-aware OAI endpoint supplied front matter for PMC4502790 but rejected full-text
XML with HTTP 400, so the demo paper remains explicitly abstract-only in automated
retrieval. The official Enzo product page and linked 28-page PDF were accessible; the
bounded manual extract retained 22 complete physical pages. No browser-page scraping,
paywall bypass, allowlist expansion, or transport weakening was added.

## Phase E — Gemini integration

Status: **implemented and verified with fixtures; live verification blocked**.

The model-specific HTTP body in `assessment.py` was replaced with a provider interface
under `researchguard/providers/`. Gemini uses the official `google-genai==2.24.0` SDK.
The existing extraction schemas, prompts, assessment service, source-ID checks, exact
quotation/location matching, evidence-relationship rules, review decisions, and export
schema were preserved. The old OpenAI provider cannot be selected and its host was
removed from the source transport allowlist.

Both task model identifiers are configurable. Phase E defaults and restricts them to
`gemini-3.8-flash`, which current official model/pricing documentation listed with a
Free Tier on 2026-09-18. This is a documentation-backed selection, not evidence that
the user's project has access. Live use requires `GEMINI_API_KEY` plus an operator-set
`GEMINI_FREE_TIER_CONFIRMED=true` after checking the actual project in AI Studio. No
billing action, credit, paid model, provider fallback, Search grounding, tool, or cache
is configured.

Provider input/output bytes, output tokens, local concurrency, capacity wait, SDK
timeout, and retries are bounded. Only selected 5xx errors receive one retry; HTTP 429
returns a clear Free Tier rate/quota exhaustion message. Structured JSON output is
requested with the Pydantic schema and parsed again in application code. A normal stop,
nonempty output, returned model version, structural schema, and the existing evidence
validators are all required before an assessment is stored.

Controlled tests cover missing/unconfirmed configuration, disabled OpenAI selection,
malformed output, invalid key response, quota/rate response, size/retry/tool/cache
settings, provenance and secret exclusion from records/exports. The existing fabricated
source ID and quotation/location tests remain green. `scripts/verify_gemini_live.py`
provides a two-call synthetic verification and records requested/returned models,
prompt version, source ID/access/hash, and validation results. It exited blocked with
zero calls because no key or actual Free Tier confirmation was present.

## Migration phase status

| Phase | Definition | Execution status |
| --- | --- | --- |
| B | FastAPI HTTP adapter around existing services | Completed and locally verified in Phase B |
| C | React/TypeScript/Tailwind interface using the FastAPI contract | Completed and locally verified in Phase C |
| D | Verify and narrowly repair existing retrieval adapters | Completed with fixture and live verification in Phase D |
| E | Gemini Developer API Free Tier provider | Fixture-verified; live call blocked pending actual Free Tier project confirmation and key |
| F | Supabase Free Google sign-in and verified backend identity | Fixture-verified; live OAuth blocked pending dashboard configuration and browser round trip |
| G | Awaiting the user's Phase G instruction | Not started |
| H | Awaiting the user's Phase H instruction | Not started |

For each future phase: reread `context.md`, this plan, the architecture decision,
repository instructions and `PROGRESS.md`; reconcile the supplied scope with actual
code; implement only that phase; run relevant checks; record implementation and
verification separately; report blockers/manual actions and stop at its gate.

The following is an **unassigned migration backlog**, not a replacement E–H sequence:

- Phase F resolved the authentication boundary with verified server identity,
  deliberate Supabase client session handling, refresh/logout/account-switch cleanup,
  public-demo separation and fixture user-isolation tests. Live OAuth remains blocked;
  login does not persist or claim a draft.
- Prepare reviewable saved-record migrations/RLS, explicit save/update/list/load/delete,
  schema/revision handling and revalidation. Verify owner-only access through both
  backend and database API, immutable ownership, no autosave, concurrent-save behavior,
  record/export round trips and quota/paused-service failure states.
- Execute integration and scientific evaluation separately. Have a knowledgeable
  researcher review the 16 provisional references; freeze development choices before
  held-out runs. Report raw denominators, failures and unmeasured dimensions. No
  model-agreement or structural validation result substitutes for scientific review.
- Prepare a reproducible local handoff with no-secret environment examples, setup,
  local callbacks, rollback, explicit-save/deletion behavior, data terms and limits.
  A completed local journey requires real retrieval/provider/auth/save verification;
  otherwise record the remaining gate as partial. Public deployment is excluded.

External setup and integration must remain free-only. When account or scientific
review access is missing, record the blocker and continue only independent work
within the currently authorized phase. Never begin another phase automatically.

## Manual actions and unresolved decisions

**Manual action is required to complete Phases E and F's external gates.** In Google AI Studio,
verify that the intended project is on Free Tier and has no linked billing, and that
`gemini-3.8-flash` is available. Configure `GEMINI_API_KEY` only in the local backend
environment, set `GEMINI_FREE_TIER_CONFIRMED=true`, and run
`.venv/bin/python -m scripts.verify_gemini_live`. Do not paste the key into chat or a
frontend variable. Do not enable billing if the model is unavailable.

For Phase F, configure the Free project and Google OAuth client exactly as documented
in `docs/AUTH_SETUP.md`, using `http://127.0.0.1:5173/` as the application URL, then
complete sign-in, reload restoration, sign-out, cancellation and failure checks in a
browser. No client secret or privileged Supabase key should be shared or committed.

Later phases, supplied one at a time, will require:

1. The already-required user-controlled Supabase **Free** project will also need any
   persistence schema and RLS explicitly authorized by a later phase. Phase F creates
   no database table and saves no review.
2. An AI Studio project verified to be on **Free Tier with no linked billing**, an
   eligible model and region, and its API key configured server-side. If the account
   requires billing or credits for the intended model, stop that integration rather
   than enabling payment. No existing project/account state has been verified in A.
3. Two test users for owner-isolation checks and a knowledgeable researcher for
   scientific reference review. Cloud review storage should contain only explicitly
   saved public/synthetic material during verification.

Precise project quota limits, auth token-storage strategy,
Supabase region/schema deployment and current provider data terms must be verified
at the relevant later phase. No project creation, OAuth console changes, SQL
application, live provider calls, billing changes or deployment occurred through E.

Official references inspected for planning and Phase E implementation, not proof of
access in the user's project:

- [Gemini billing/free-tier distinction](https://ai.google.dev/gemini-api/docs/billing):
  free access is model/account constrained; paid activation is not an allowed remedy.
- [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output):
  verify supported schema features and still validate output in application code.
- [Gemini data terms](https://ai.google.dev/gemini-api/terms): review free-service data
  treatment before sending inputs; do not claim confidential or local-only processing.
- [Supabase pricing](https://supabase.com/pricing): Free has limits and inactivity
  pausing; verify the user's project rather than assuming availability.
- [Supabase Google sign-in](https://supabase.com/docs/guides/auth/social-login/auth-google):
  provider and redirect configuration are prerequisites, not yet completed here.
- [Supabase row-level security](https://supabase.com/docs/guides/database/postgres/row-level-security):
  enforce database ownership as well as application checks; privileged credentials
  must not bypass isolation in ordinary review requests.

**Phase F outcome: blocked at the required live OAuth verification gate.** Token and
HTTP behavior are fixture-verified, but actual project/provider setup and the browser
round trip remain unverified. Phase E's Gemini live gate also remains blocked.
Phases G–H await sequential user instructions. Persistence and scientific evaluation
remain unverified. Stop here.
