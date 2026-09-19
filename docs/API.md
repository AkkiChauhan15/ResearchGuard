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
| `GET /api/config` | None | Local mode, retention, Gemini state plus public auth availability; never credential values |
| `GET /api/auth/me` | Verified Supabase bearer token | Verified `user_id` and optional email |
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
invoke live services. Live failures never fall back to the demo. Phase E selects the
Gemini provider. Missing credentials, unconfirmed Free Tier, disallowed models,
authentication failures, and quota exhaustion are explicit unavailable states.
Extraction returns an error and assessment records the error on the claim. OpenAI
selection is rejected.

`SavedReviewSummary` contains `saved_id`, canonical `review_id`, `schema_version`,
`revision`, `mode`, `title`, `created_at` and `updated_at`. `SavedReviewRecord` adds the
unchanged canonical `review`. Saved records never accept an owner ID from the browser.
The backend forwards the verified access token to Supabase PostgREST with the public
publishable key, so database RLS derives ownership from `auth.uid()`. No privileged key
or UI-only owner filter is used. Opening does not autosave later edits; the user must
choose Update saved copy.

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
The permitted
cross-origin frontend defaults are exactly `http://127.0.0.1:5173` and
`http://localhost:5173`, with credentials disabled. These environment variables may
change local limits without putting secrets in source control:

| Name | Default |
| --- | --- |
| `RESEARCHGUARD_FRONTEND_ORIGINS` | `http://127.0.0.1:5173,http://localhost:5173` |
| `RESEARCHGUARD_SESSION_TTL_SECONDS` | `3600` |
| `RESEARCHGUARD_MAX_REVIEWS` | `24` |
| `RESEARCHGUARD_MAX_REVIEW_BYTES` | `5000000` |
| `RESEARCHGUARD_MAX_REQUEST_BYTES` | `100000` |
| `RESEARCHGUARD_EXTERNAL_CONCURRENCY` | `4` |
| `RESEARCHGUARD_RETRIEVAL_TIMEOUT_SECONDS` | `90` |
| `RESEARCHGUARD_ASSESSMENT_TIMEOUT_SECONDS` | `130` |
| `NCBI_EMAIL` | unset optional NCBI contact |
| `LLM_PROVIDER` | `gemini`; any other provider is unavailable and OpenAI is explicitly disabled |
| `GEMINI_API_KEY` | unset server-only secret |
| `GEMINI_FREE_TIER_CONFIRMED` | unset; set `true` only after checking AI Studio project tier and billing |
| `GEMINI_EXTRACTION_MODEL` | `gemini-3.8-flash` |
| `GEMINI_ASSESSMENT_MODEL` | `gemini-3.8-flash` |
| `SUPABASE_URL` | unset; exact server-side `https://<project-ref>.supabase.co` origin |
| `SUPABASE_PUBLISHABLE_KEY` | unset public `sb_publishable_...` key used with the user bearer token; secret/service-role keys are rejected |
| `RESEARCHGUARD_AUTH_TIMEOUT_SECONDS` | `10` |
| `RESEARCHGUARD_PERSISTENCE_TIMEOUT_SECONDS` | `10` |

The React build reads only `VITE_SUPABASE_URL` and
`VITE_SUPABASE_PUBLISHABLE_KEY`. These are public project values. Full dashboard and
redirect setup is documented in `docs/AUTH_SETUP.md`. Google secrets, Supabase
secret/service-role keys and JWT signing keys are not backend settings for this app.
Migration application and saved-review RLS checks are documented in
`docs/PERSISTENCE_SETUP.md`.

The provider limits serialized model input to 120,000 bytes, output to 64,000 bytes,
and local Gemini concurrency to two calls. Extraction and assessment request at most
2,048 and 4,096 output tokens respectively. The SDK deadline is 60 seconds. It makes
at most two attempts for HTTP 500/502/503/504; HTTP 429 is reported immediately as
Free Tier rate/quota exhaustion. The request config contains no tools, Google Search
grounding, or cached content. The FastAPI bounded worker pool and route deadline are
an additional outer bound.

`GEMINI_FREE_TIER_CONFIRMED` is a local attestation, not an API-derived billing check.
The official model/pricing pages and the user's AI Studio project must be rechecked
before changing model IDs. Free Tier data can be used by Google to improve products;
use only public or synthetic material in this verification phase. The old OpenAI
environment variables have no active code path.
