# Architecture decisions — 2026-09-16

## Approved target and completed local migration decisions through Phase E

On 2026-09-16 the user approved **Python + FastAPI**, **React + TypeScript +
Tailwind**, **Supabase Free** for Google authentication and explicitly saved
reviews, and **Gemini Developer API through an AI Studio Free Tier project**.
Local development first. No public deployment, paid services, billing activation,
paid fallback, or credit purchases. Phase A documented the baseline. Phase B replaced
the local HTTP adapter with FastAPI. Phase C replaces the primary interface with a
Vite React/TypeScript/Tailwind SPA while preserving the FastAPI and review contracts.
Phase D verified retrieval. Phase E replaces the provider-specific runtime path with
a bounded Gemini adapter. Authentication, persistence, and deployment remain later work.

Phase B preserves `schemas.py`, retrieval/transport protections, deterministic evidence
validation, `demo.py` and its archived sources, review decision semantics, and
JSON/TXT exports. `researchguard/api.py` wraps those services in FastAPI and
`researchguard/store.py` owns temporary draft isolation. Phase C consumes that API;
it does not move retrieval, model, validation, decision, or export rules into React.
Phase E replaces only provider request, response, credential, configuration, and error
handling. OpenAI model names below describe previous candidates only; provider
selection rejects the archived adapter and there is no runtime fallback.

The Phase C application lives in `frontend/`. It uses React 19.3, TypeScript 6,
Vite 8, and Tailwind CSS 4 through Tailwind's Vite plugin. Browser requests use
relative `/api` paths. The development and preview servers bind to
`127.0.0.1:5173` and proxy those paths to FastAPI on `127.0.0.1:8000`; the production
build is generated into `frontend/dist` and FastAPI serves it at `/` when present.
No runtime provider credential, provider SDK, or `VITE_` secret is part of this SPA.

The interface displays source material as React text, keeps evidence status separate
from retrieval access state, and only associates sources with a claim through that
claim's current retrieval attempts. A material claim edit therefore removes stale
assessment and current source displays as soon as the server returns the canonical
updated review. Model, retrieval, edit, decision, and export requests remain explicit
user actions. There is no background model retry or review autosave.

The pre-React interface in `web/` is retained at `/legacy`. If no production React
build exists, FastAPI serves that legacy interface at `/` as a local setup fallback.
The generated `frontend/dist` directory is not source-controlled; run the documented
build before using the same-origin React preview.

The current `X-Review-Session` is a transient bearer capability, not Google identity.
Keep guest drafts separate from authenticated ownership. Future saved records must
derive an owner from a validated Supabase token and enforce owner-only access through
row-level security. Use explicit save/update actions; login, extraction, retrieval,
assessment, or editing must not write review bodies to Supabase automatically.
Preserve the current review payload inside a versioned persistence envelope so
database metadata does not force a rewrite of source/evidence schemas.

The Phase B API permits only the explicit local React development origins
`http://127.0.0.1:5173` and `http://localhost:5173` by default, never wildcard
credentialed CORS. The current same-origin preview remains available on port 8000.
Source URL restrictions are unchanged. Free-tier exhaustion must fail visibly.

Synchronous retrieval, PDF parsing, provider calls, and export validation run in a
bounded thread pool with route deadlines. Each review has an async mutation lock;
services mutate a deep copy, then the API validates and atomically commits it. Timeout
or validation failure cannot commit that copy. Storage remains limited, expiring,
process-local, and keyed by the transient session capability, so run one Uvicorn worker.
This is session isolation for local drafts, not authenticated ownership.

The Phase B route and environment contracts are recorded in `docs/API.md`. REST paths
changed deliberately from the legacy action endpoints and the existing frontend was
updated with them. The canonical Pydantic `Review` response and `{error: string}`
error envelope remain. Gemini configuration and failures produce explicit unavailable
states; no provider failure substitutes demo content.

Phase D retains the existing restricted transport and adapters. PubMed search still
uses ESearch followed by bounded individual EFetch calls so one oversized or malformed
record does not discard readable results. Each omission is present in source limitations
and the retrieval-attempt summary. PubMed identifiers come only from the requested
record's own `PubmedData/ArticleIdList`; cited-reference identifiers cannot overwrite
them. PMC is labeled `full text` only when the official XML contains readable body
paragraphs. A PMCID, successful HTTP response, article element, or empty body element
is insufficient. Exact passages remain unchanged and locations describe their actual
abstract, XML paragraph, HTML block, or physical PDF page positions.

`MIGRATION_PLAN.md` contains the code-backed inventory, existing API contract,
migration risks, completed Phase B–D decisions, the Phase E provider decision, reserved F–H entries, and account
setup prerequisites. The user will define later phases sequentially, one phase at a
time; no phase mapping is inferred. Phase B checks verify the FastAPI HTTP layer and
Phase C checks verify the compiled interface and browser behavior. Phase D verifies
the supported retrieval sources with fixtures and live read-only requests. Phase E
verifies Gemini behavior with fixtures only. Phase F adds fixture-verified Supabase
identity; live OAuth and saved reviews remain unverified.

## Phase E — Gemini provider boundary

`researchguard/providers/` now owns runtime selection and Gemini SDK calls.
`assessment.py` retains the scientific system/task prompts, extraction schemas, and
deterministic source-ID, quotation, location, and evidence-relationship checks. This
separation preserves the canonical review schema and lets routes continue calling the
same extraction/assessment services.

The server defaults to `LLM_PROVIDER=gemini`. The former OpenAI destination was removed
from the restricted transport allowlist and OpenAI provider selection returns an
unavailable state. Extraction and assessment model IDs are configured independently;
the Phase E allowlist contains only `gemini-3.8-flash`, which the official pricing
table listed with free input and output on 2026-09-18. Documentation is not proof that
the user's project can call it. Live requests also require the operator to verify Free
Tier/no billing in AI Studio and set `GEMINI_FREE_TIER_CONFIRMED=true` server-side.

The pinned `google-genai` SDK sends plain JSON input as untrusted data and requests a
Pydantic response schema with `application/json`. It configures no tools, Search
grounding, or cached content. Application code reparses the response, requires a normal
stop and returned model version, then runs the existing deterministic evidence checks.
Each recorded `ModelRun` retains task, requested and returned model, prompt version,
source IDs, timestamp, and validation outcomes. Source records retain access levels,
locations, hashes, and versions independently.

Limits are layered: 120,000 serialized input bytes, 64,000 output bytes, 2,048/4,096
maximum extraction/assessment output tokens, two concurrent Gemini calls, five seconds
to acquire capacity, a 60-second SDK timeout, and at most two attempts for selected 5xx
errors. HTTP 429 is not retried because it may represent daily Free Tier exhaustion.
Mapped errors never include the provider response or key. There is no provider/model
fallback and no automatic transition to paid access.

Fixture tests cover missing key, unconfirmed Free Tier, disabled OpenAI selection,
malformed output, invalid authentication, HTTP 429, model input bounds, request config,
model/source/access provenance, and the preserved evidence validators. A live script
uses only synthetic text and exits before any call unless the operator confirmation and
key are present. No Phase E live call ran because neither was available, so the phase's
external integration gate remains blocked.

## Phase F — Supabase Google identity boundary

The React SPA uses `@supabase/supabase-js` directly with the supported implicit OAuth
flow, persistent browser session and automatic refresh. It redirects only to an exact
local allowlist. The app has no invented callback endpoint: Google returns to
Supabase's `/auth/v1/callback`, then Supabase returns to the configured React URL.
Cancellation and callback failure remain visible errors. The demo does not read or
require the auth session.

FastAPI accepts bearer access tokens only for live routes. `SupabaseTokenVerifier`
obtains asymmetric public keys from the project JWKS and accepts ES256/RS256 tokens
only after verifying signature, exact issuer, expiry, `authenticated` audience and
role, and a UUID subject. Ownership always comes from that subject; browser-supplied
identity fields are absent from request schemas. Verification runs in the existing
bounded external executor with its own deadline. A JWKS outage reports unavailable,
while invalid credentials return a generic `401` with a Bearer challenge.

The temporary store now binds a live record to both its random browser session and
the verified user. Demo entries have no owner and remain public within their temporary
browser session. Logout/session expiry clears live UI state. Persistent storage is not
part of Phase F: there is no Supabase table, RLS policy, privileged key or autosave.
Future saved-review routes must reuse the verified identity boundary and explicit-save
requirement.

Frontend configuration is limited to the project URL and publishable/anon key. The
backend receives only `SUPABASE_URL`; it needs no service-role secret or JWT private
key. Fixture tests cover token validation, ownership and unauthenticated rejection.
The real OAuth browser round trip remains blocked until the user configures the Free
project and Google client exactly as recorded in `docs/AUTH_SETUP.md`.

## Previous local-preview decision — historical record

The following records the initial implementation choice. Its framework/provider
selection is superseded by the approved migration target above. Retention and
authentication descriptions below describe the existing application only.

Inspection found only `context.md` in the working tree, no existing application,
no applicable AGENTS.md, and no configured OpenAI credentials. Python 3.14.7,
Node 22.22.2, and Pydantic 2.13.4 are available.

Use Python's standard-library HTTP server bound to loopback for a **local preview**,
Pydantic for typed records and validation, and plain HTML/CSS/JavaScript for the
interface. This avoids a build service or frontend dependency tree. This server
is not a production hosting choice; authentication, durable storage, and deployment
remain outside this local preview. No public deployment is authorized.

The backend owns records, retrieval, model calls, deterministic evidence validation,
and exports. A random per-tab session header isolates transient in-memory records.
State expires; nothing is written to disk automatically. Downloading an export is
the explicit save operation. Sources are untrusted data, rendered as text.

The frontend follows DEFINE → RISK → ASSIST → VERIFY → RECORD. Review priority
does not mean a probability or clinical risk. Each claim has its own evidence
status and researcher decision; access states remain separate.

Live mode supports editable initial text segments without model access. AI extraction
and assessment require server-side credentials. Sources can be retrieved independently.
Demo uses a visibly curated record and never fills in a failed live request.

Source retrieval is restricted to exact supported public hosts and path shapes.
The transport validates DNS results, connects to a validated address with TLS hostname
verification, validates every redirect, and limits bytes, time, and content types.
PubMed uses ESearch/EFetch; PMC uses EFetch, respecting availability; Enzo starts with
its exact CYTO-ID product page and linked ENZ-51031 PDF manual. The PDF adapter uses
the optional `pdftotext` system utility with time/output/page limits and real physical
page positions. Other manufacturers and manuals are not yet supported.

Assessments use the Responses API with strict JSON schema, then application validation
of source IDs, source availability, exact passage membership, and location. Whitespace
folding is the only quotation normalization. Structural validity does not prove
scientific support; that remains a researcher review task.

Follow the eight phases in `context.md`; report implementation separately from fixture,
browser, and live verification. A missing key blocks live model verification, not
independent UI/retrieval/export work. Evaluation references require human scientific review.
