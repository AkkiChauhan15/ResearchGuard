# Research Guard local HTTP API

Phase B exposes the existing review services through FastAPI. Phase C consumes those
routes from the React interface without changing their request/response contracts. The canonical response
for review operations is the existing Pydantic `Review` record; routes do not define a
second review schema. OpenAPI is available locally at `/api/docs` and
`/api/openapi.json` while the server is running.

## Session and error contract

Every review route requires `X-Review-Session: <UUID>`. This random browser value is
an opaque capability for a temporary draft, not an authenticated user identity. Demo
routes remain public. Live creation and every later read or mutation of a live review
also require `Authorization: Bearer <Supabase access token>`. FastAPI verifies the JWT
signature through the project's JWKS plus issuer, expiry, audience, role and subject,
then binds the record to that verified subject. A review created under another browser
session or verified user returns `404`. Health and configuration routes need no token.
`GET /api/auth/me` requires a valid token and returns only the verified user ID/email.
General-chat routes also require a valid bearer token. Chat does not use the draft
session header. Successful turns are stored in the separate owner-scoped
`saved_chats` table and are never inserted into an evidence review.

JSON request bodies use `application/json`. Validation and service-rule failures return
`400 {"error": "..."}`; inaccessible/expired reviews return `404`; bodies over the
configured request limit return `413`; an external operation that exceeds its route
deadline returns `504` without committing its working copy. Unexpected failures return
a generic `500` envelope without provider details or a fabricated assessment. Saved
record revision conflicts return `409`; unavailable Supabase persistence returns `503`
and leaves the temporary working review intact.

## Routes

| Method and path | Request | HTTP 200 response |
| --- | --- | --- |
| `GET /api/health` | None | Service status and temporary-storage mode |
| `GET /api/config` | None | Local mode, retention, selected evidence-provider state plus public auth availability; never credential values |
| `GET /api/auth/me` | Verified Supabase bearer token | Verified `user_id` and optional email |
| `GET /api/chat/providers` | Verified bearer token | Safe configuration state, allowlisted models and fallback flag; never keys |
| `POST /api/chat` | Bearer token plus `provider`, allowlisted `model`, 1–24 user/assistant `messages`, optional `allow_fallback`, and paired `chat_id`/`expected_revision` when continuing | Normalized answer plus the canonical saved chat; a new chat must start with one user message |
| `GET /api/chats` | Bearer token | `{items: SavedChatSummary[]}` for the verified owner only |
| `GET /api/chats/{chat_id}` | Bearer token | Canonical owner-scoped `SavedChatRecord` |
| `GET /api/chats/{chat_id}/export.pdf` | Bearer token | PDF attachment generated from the canonical saved chat |
| `DELETE /api/chats/{chat_id}?expected_revision=1` | Bearer token | `{deleted: SavedChatSummary}`; HTTP 409 on a stale revision |
| `GET /api/saved-reviews` | Bearer token; no draft session required | `{items: SavedReviewSummary[]}` for the verified owner only |
| `POST /api/saved-reviews` | Bearer token, draft session and `{"review_id":"review_..."}` | HTTP 201 `SavedReviewRecord`; explicit snapshot of that canonical temporary review |
| `POST /api/saved-reviews/{saved_id}/open` | Bearer token and draft session | `SavedReviewRecord`; also creates an owner-bound temporary working copy in that session |
| `PUT /api/saved-reviews/{saved_id}` | Bearer token, draft session and `{"review_id":"review_...","expected_revision":1}` | Updated `SavedReviewRecord`; HTTP 409 if the saved revision changed |
| `GET /api/saved-reviews/{saved_id}/export?format=json\|txt` | Bearer token | Validated canonical saved review attachment |
| `DELETE /api/saved-reviews/{saved_id}?expected_revision=1` | Bearer token | `{deleted: SavedReviewSummary}`; HTTP 409 on a stale revision |
| `POST /api/reviews` | Bearer token plus existing `ReviewInput`: `text`, `intended_use`, optional `context` and up to three `source_urls` | User-owned transient live `Review`; client-supplied mode/IDs/user IDs are rejected |
| `POST /api/reviews/demo` | No semantic body | New curated demo `Review`; no retrieval or model call |
| `GET /api/reviews/{review_id}` | Session header | Canonical current `Review` |
| `PATCH /api/reviews/{review_id}/claims/{claim_id}` | `{"text": "1-12000 characters"}` | Updated `Review`; material edit resets that claim's assessment and decision and detaches old attempts |
| `PATCH /api/reviews/{review_id}/context` | Complete existing `Context` object | Updated `Review`; a material context change resets every assessment/decision and detaches current attempts |
| `POST /api/reviews/{review_id}/extraction` | No semantic body | Updated `Review`; existing provider service performs extraction |
| `POST /api/reviews/{review_id}/claims/{claim_id}/retrievals` | `{"query": "1-500 characters"}` | Updated `Review` with attempt/access states and any validated source records |
| `POST /api/reviews/{review_id}/claims/{claim_id}/assessment` | No semantic body | Updated `Review`; expected provider/access failures are recorded as `assessment=null` plus `assessment_error` |
| `PUT /api/reviews/{review_id}/claims/{claim_id}/decision` | `{"decision": {"status": "pending|accepted|edited|rejected", "final_wording": "...", "notes": "..."}}` | Updated `Review`; the server derives accepted final wording and enforces assessment presence |
| `GET /api/reviews/{review_id}/export?format=json` | Session header | Validated canonical JSON attachment |
| `GET /api/reviews/{review_id}/export?format=txt` | Session header | Readable attachment containing the same complete canonical JSON record |

Demo claims/context cannot be edited, and demo retrieval/assessment/extraction cannot
invoke live services. Live failures never fall back to the demo. `LLM_PROVIDER`
explicitly selects Groq, OpenRouter-free, NVIDIA NIM, or the retained Gemini adapter.
Missing credentials, unconfirmed free access, disallowed models, authentication failures,
and quota exhaustion are explicit unavailable states. Extraction returns an error and
assessment records the error on the claim. Provider failures never switch providers.
The legacy OpenAI API selection remains rejected.

`SavedReviewSummary` contains `saved_id`, canonical `review_id`, `schema_version`,
`revision`, `mode`, `title`, `created_at` and `updated_at`. `SavedReviewRecord` adds the
unchanged canonical `review`. Saved records never accept an owner ID from the browser.
The backend forwards the verified access token to Supabase PostgREST with the public
publishable key, so database RLS derives ownership from `auth.uid()`. No privileged key
or UI-only owner filter is used. Opening does not autosave later review edits; the user
must choose Update saved copy.

`SavedChatSummary` contains `chat_id`, `schema_version`, `revision`, `title`,
`message_count`, the last actual provider/model, and timestamps. `SavedChatRecord` adds
the complete alternating message list. Assistant messages retain actual provider/model
and fallback provenance. The backend accepts no owner ID. Continuing a chat requires an
exact extension of its stored history and matching revision; stale or forged history
receives HTTP 409 rather than overwriting the saved conversation.

## Limits and concurrency

Defaults are a one-hour lifetime, 24 process-local reviews, 5,000,000 bytes per
canonical review, 100,000 bytes per HTTP request, 60 retrieval histories per review,
and 30 recorded model runs per review. One asyncio lock serializes mutations of each
review. A mutation operates on a deep copy, validates the complete review, then commits;
failure or timeout leaves the canonical record unchanged.

Synchronous retrieval, PDF parsing, provider calls, and export validation run outside
the event loop in a bounded thread pool. The default pool limit is four. Retrieval has
a 90-second request deadline and extraction/assessment have a 130-second deadline.
Timed-out worker functions cannot commit their private review copy. Use one Uvicorn
worker because temporary records, locks, and NCBI throttling are process-local.

Chat messages are limited to 8,000 characters each and 24,000 characters total. Saved
conversations are limited to 24 alternating messages and 250,000 serialized bytes. The
default authenticated-user limit is six requests per rolling minute. Chat runs in the
same bounded external pool, has a 45-second total deadline, a 20-second provider
deadline, and at most 1,024 output tokens. Provider failures return safe `429`, `503`,
or `504` errors. No failed chat call substitutes demo content. A new request preflights
the saved-chat/RLS path before using model quota; the UI presents only a response that
the persistence layer confirmed.

## Local startup and configuration

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m researchguard.server --port 8000
```

Equivalent direct startup:

```sh
.venv/bin/python -m uvicorn researchguard.api:app --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

The built React preview is served from `http://127.0.0.1:8000` when
`frontend/dist/index.html` exists. The pre-React interface remains at `/legacy`, and
is also used at `/` if no React build is present. For development, Vite runs at
`http://127.0.0.1:5173` and proxies relative `/api` requests to this FastAPI process.
FastAPI serves the same SPA entry at `/login`, `/signup`, `/forgot-password`,
`/update-password`, `/account`, and `/chat`; Vercel uses equivalent exact rewrites. These are
client-side account views. Backend authorization still occurs on `/api` through the
verified Supabase bearer token.
The permitted
cross-origin frontend defaults are exactly `http://127.0.0.1:5173` and
`http://localhost:5173`, with credentials disabled. These environment variables may
change local limits without putting secrets in source control:

| Name | Default |
| --- | --- |
| `RESEARCHGUARD_FRONTEND_ORIGINS` | `http://127.0.0.1:5173,http://localhost:5173`; exact HTTPS origins are allowed for deployment, never wildcards |
| `RESEARCHGUARD_ALLOWED_HOSTS` | local hosts; exact additional hostnames only. Render's `RENDER_EXTERNAL_HOSTNAME` is added automatically |
| `RESEARCHGUARD_SESSION_TTL_SECONDS` | `3600` |
| `RESEARCHGUARD_MAX_REVIEWS` | `24` |
| `RESEARCHGUARD_MAX_REVIEW_BYTES` | `5000000` |
| `RESEARCHGUARD_MAX_REQUEST_BYTES` | `100000` |
| `RESEARCHGUARD_EXTERNAL_CONCURRENCY` | `4` |
| `RESEARCHGUARD_RETRIEVAL_TIMEOUT_SECONDS` | `90` |
| `RESEARCHGUARD_ASSESSMENT_TIMEOUT_SECONDS` | `130` |
| `NCBI_EMAIL` | unset optional NCBI contact |
| `LLM_PROVIDER` | `groq` default; accepts `groq`, `openrouter`, `nvidia`, or retained `gemini`; no fallback; legacy OpenAI is disabled |
| `GROQ_API_KEY` | unset server-only secret used by chat and, when selected, structured review |
| `GROQ_FREE_TIER_CONFIRMED` | `false`; required for Groq after confirming free access with no billing |
| `GROQ_EXTRACTION_MODEL` | `openai/gpt-oss-20b` |
| `GROQ_ASSESSMENT_MODEL` | `openai/gpt-oss-20b` |
| `OPENROUTER_API_KEY` | unset server-only secret; evidence and chat are restricted to `openrouter/free` |
| `OPENROUTER_EXTRACTION_MODEL` | `openrouter/free` |
| `OPENROUTER_ASSESSMENT_MODEL` | `openrouter/free` |
| `NVIDIA_NIM_API_KEY` | unset server-only secret used by chat and, when selected, structured review |
| `NVIDIA_NIM_FREE_TIER_CONFIRMED` | `false`; required for NVIDIA after confirming free access with no billing |
| `NVIDIA_NIM_EXTRACTION_MODEL` | `meta/llama-3.3-70b-instruct` |
| `NVIDIA_NIM_ASSESSMENT_MODEL` | `meta/llama-3.3-70b-instruct` |
| `GEMINI_API_KEY` | unset server-only secret |
| `GEMINI_FREE_TIER_CONFIRMED` | unset; set `true` only after checking AI Studio project tier and billing |
| `GEMINI_EXTRACTION_MODEL` | `gemini-3.8-flash` |
| `GEMINI_ASSESSMENT_MODEL` | `gemini-3.8-flash` |
| `SUPABASE_URL` | unset; exact server-side `https://<project-ref>.supabase.co` origin |
| `SUPABASE_PUBLISHABLE_KEY` | unset public `sb_publishable_...` key used with the user bearer token; secret/service-role keys are rejected |
| `RESEARCHGUARD_AUTH_TIMEOUT_SECONDS` | `10` |
| `RESEARCHGUARD_PERSISTENCE_TIMEOUT_SECONDS` | `10` |
| `RESEARCHGUARD_CHAT_FALLBACK_ENABLED` | `false`; requires per-request user opt-in too |
| `RESEARCHGUARD_CHAT_REQUESTS_PER_MINUTE` | `6` per verified user, process-local |
| `RESEARCHGUARD_CHAT_TIMEOUT_SECONDS` | `45` total |
| `RESEARCHGUARD_CHAT_PROVIDER_TIMEOUT_SECONDS` | `20` per attempted provider |
| `RESEARCHGUARD_CHAT_MAX_OUTPUT_TOKENS` | `1024` |

The React build reads the public project values `VITE_SUPABASE_URL` and
`VITE_SUPABASE_PUBLISHABLE_KEY`. A hosted split deployment additionally uses the exact
public origins `VITE_API_BASE_URL` and `VITE_APPLICATION_ORIGIN`; local development
leaves both absent. Full dashboard and
redirect setup is documented in `docs/AUTH_SETUP.md`. Google secrets, Supabase
secret/service-role keys and JWT signing keys are not backend settings for this app.
Migration application and saved-review/saved-chat RLS checks are documented in
`docs/PERSISTENCE_SETUP.md`.
The full Vercel/Render configuration is documented in `docs/DEPLOYMENT.md`.
Optional chat-provider setup and extension instructions are in `docs/CHAT_SETUP.md`.

The selected evidence provider limits serialized model input to 120,000 bytes, output
to 64,000 bytes, and local provider concurrency to two calls. Extraction and assessment
request at most 2,048 and 4,096 output tokens respectively. The provider deadline is
60 seconds. Compatible providers make one bounded retry for selected 5xx/network
failures; HTTP 429 is reported immediately as free rate/quota exhaustion. Requests
contain no tools, search grounding, or cached content. The FastAPI bounded worker pool
and route deadline are an additional outer bound.

Provider free-access confirmations are local attestations, not API-derived billing
checks. Official model/pricing pages and the actual account must be rechecked before
changing model IDs. Provider data terms vary; use only public or synthetic material in
this verification phase. The old OpenAI API environment variables have no active path.
