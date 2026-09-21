# Research Guard AI

> **Phase H status:** the local public demonstration, current public-source retrieval,
> application checks, and real local Supabase Auth/PostgREST/RLS paths are verified.
> The linked hosted Supabase project reports migrations `202609190001` and
> `202609190002` applied. Saved-chat migration `202609210001` is prepared but is not
> yet confirmed applied. Google
> OAuth, email delivery/recovery and the hosted two-user check remain unverified. The
> earlier Gemini check reached `gemini-3.8-flash`, but generation was blocked by repeated
> HTTP 503 high-demand responses. Structured evidence tasks now support explicitly
> selected Groq, OpenRouter-free, or NVIDIA NIM providers instead of defaulting to
> Gemini; their live evidence-generation path remains unverified locally. Vercel deployed
> the latest checked commit, but its generated deployment URL is
> currently protected by Vercel SSO; public reachability and the hosted journey remain
> unverified. No billing or paid fallback has been used.

A local research-review application for making claim-to-evidence relationships,
experimental context, and limitations inspectable. Start with the clearly labeled
CYTO-ID demonstration, or create a live review and retrieve public sources.

The signed-in `/chat` page is an optional general assistant using server-side Groq,
OpenRouter, Gemini, or NVIDIA NIM adapters. Successful conversations are saved privately
to the signed-in account, can be reopened or deleted, and can be exported as PDF. Every
reply remains labeled as unverified model output and separate from evidence reviews.

## Features

- **Evidence review workspace:** paste scientific text, edit extracted claims, separate
  observations from interpretations, retrieve supported public sources, inspect exact
  passages and access limitations, and record accept/edit/reject decisions.
- **Validated provenance:** reviews retain source IDs, URLs, access levels, hashes,
  locations, retrieval attempts, timestamps, requested/returned models and deterministic
  quotation checks.
- **Public demonstration:** the curated CYTO-ID example works without an account and is
  labeled as demonstration content rather than a live result.
- **Private accounts and records:** Supabase authentication protects live model actions,
  owner-only saved reviews, optional profiles and saved chat history through RLS.
- **Multi-provider AI:** Groq is the default structured-review provider; OpenRouter-free,
  NVIDIA NIM and retained Gemini adapters are explicitly selectable. Evidence requests
  never silently switch provider or use a paid fallback.
- **Saved AI chat:** successful turns save automatically with timestamps and actual
  provider/model provenance. Users can list, reopen, continue and delete their chats.
- **Exports:** reviews export as canonical JSON or readable TXT. Saved chats export as
  paginated PDF with an explicit `not evidence-checked` warning.
- **Security boundaries:** verified JWTs, owner-only database policies, exact CORS/host
  allowlists, protected URL retrieval, bounded concurrency and stale-update detection.

This remains a local-first application with a reported free-tier deployment. The former
OpenAI API adapter is disabled. Groq, OpenRouter-free and NVIDIA structured adapters
have passed controlled fixture tests but **have not completed a local live evidence
generation**. The retained Gemini adapter also has no successful live generation.
Scientific accuracy has not been measured. See `PROGRESS.md` for actual results
and incomplete phase gates; read `context.md` before continuing any phase. The exact
free hosted setup is in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). A successful host
build does not establish public access or the complete hosted integration journey.

## Run locally

Python 3.11+ and Node 22.12+ are required (tested with Python 3.14.7 and Node
22.22.2). From this directory, install both dependency sets:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci --prefix frontend
```

For development, start FastAPI in one terminal:

```sh
.venv/bin/python -m researchguard.server
```

Then start Vite in another terminal:

```sh
npm run dev --prefix frontend
```

Open http://127.0.0.1:5173. Vite proxies `/api` to the real FastAPI backend at
`127.0.0.1:8000`. For the same-origin production build preview, run:

```sh
npm run build --prefix frontend
.venv/bin/python -m researchguard.server --port 8000
```

Open http://127.0.0.1:8000. The preserved pre-React interface remains at
http://127.0.0.1:8000/legacy. FastAPI falls back to that interface at `/` when no
`frontend/dist` build exists. The Uvicorn server binds only to loopback and defaults
to one worker. Do not expose this development server publicly or add workers while
drafts and locks are process-local.

After signing in, open http://127.0.0.1:5173/chat or choose **AI chat** in the header.
The browser sends the selected allowlisted provider/model and bounded conversation
history to `POST /api/chat`; FastAPI calls the provider with its server-only key, saves
the successful turn through owner-scoped Supabase RLS, and returns the canonical chat.
Provider/model setup, persistence/PDF behavior, fallback rules, a bounded live
check, and adapter extension steps are documented in
[`docs/CHAT_SETUP.md`](docs/CHAT_SETUP.md).

The public demonstration needs no account. `/login` and `/signup` reuse the configured
Google provider and expose email/password controls only when Supabase reports that the
method is enabled. `/forgot-password`, `/update-password`, and `/account` handle account
recovery and optional profile details. Live review/model routes require a verified
Supabase session. Follow [`docs/AUTH_SETUP.md`](docs/AUTH_SETUP.md)
for the exact public environment variables and the separate Google-to-Supabase and
Supabase-to-application redirect settings. No OAuth secret belongs in frontend code.
Apply the saved-review migration and configure the backend public project values by
following [`docs/PERSISTENCE_SETUP.md`](docs/PERSISTENCE_SETUP.md). The app never
autosaves: opening a saved record creates a temporary working copy, and changes persist
only after choosing **Update saved copy**.

That no-autosave rule applies to evidence reviews. AI chat has a separate user-authorized
policy: successful turns save automatically after sign-in. Apply migration
`202609210001` before enabling hosted chat. If saving fails, the request reports the
failure rather than presenting the response as saved.

The optional account profile is stored separately from reviews and contains only name,
research role, field and institution. Every field is optional, RLS restricts access to
the authenticated owner, and profile/account identity is never sent to a model provider. The
hosted `202609190002` migration is applied; two-user hosted profile isolation still
needs browser verification.

For a disposable local Supabase verification environment, install Docker and the
Supabase CLI, then run:

```sh
supabase start
supabase test db
.venv/bin/python -m scripts.verify_supabase_local
```

The last command uses two synthetic local email identities to exercise real asymmetric
tokens, PostgREST and RLS. It is not a Google OAuth test and prints no keys or tokens.
The demo and public-source retrieval do not require a model key. The manual
adapter additionally requires Poppler's `pdftotext` utility (typically packaged
as `poppler-utils` on Linux or `poppler` on macOS). Missing utility errors remain visible.

For the recommended non-Gemini evidence provider, first verify in Groq that the exact
account is on free access with no billing. Then configure the backend process only:

```sh
export LLM_PROVIDER=groq
export GROQ_API_KEY='set-locally-do-not-commit'
export GROQ_FREE_TIER_CONFIRMED=true
export GROQ_EXTRACTION_MODEL=openai/gpt-oss-20b
export GROQ_ASSESSMENT_MODEL=openai/gpt-oss-20b
```

Alternatively select `openrouter` with `openrouter/free`, or `nvidia` with one of the
checked-in NIM model IDs and its free/no-billing confirmation. Gemini remains selectable
for migration compatibility but is no longer the default. Provider selection is explicit
and never falls back. Confirmation variables are operator attestations; code cannot
inspect account billing. Do not configure the legacy OpenAI API variables: that provider
is rejected. Set `NCBI_EMAIL` to an
appropriate contact email for NCBI API requests. Requests are throttled below
three/second per process; multiple processes on the same IP need coordinated rate
limiting.

The local server, review-provider verifier and evaluation CLI safely load the ignored root
`.env`; existing exported shell variables take priority. They parse assignments without
executing the file as shell code. Keep `.env` owner-readable only and never put model
credentials in `frontend/.env.local` or any `VITE_` variable. Run a bounded synthetic
connectivity check with `.venv/bin/python -m scripts.verify_review_provider_live`.

The FastAPI route, error, limit, local CORS, startup, and environment-variable
contracts are documented in [`docs/API.md`](docs/API.md). Interactive OpenAPI docs
are available at http://127.0.0.1:8000/api/docs while the server is running.

## Use the review

1. Paste public or synthetic text, choose intended use, and optionally add context
   and up to three supported source URLs. Initial claims are editable sentence
   segments, explicitly **not AI extraction**. With a configured key, use AI extraction.
2. Inspect/edit claims and missing-context questions. Editing invalidates previous
   evidence links, assessments, and decisions for that claim. Re-extraction replaces
   the claim set; export previous work first if you need it.
3. Enter concise search terms with organism/assay context, then retrieve evidence.
   Two PubMed queries include a limitation/contradiction/replication variant, with
   at most three records per query. Inspect the search/access history and relevance.
4. Use “Assess retrieved evidence” to call the configured model. With missing
   credentials, failed retrieval, or invalid output, no assessment is fabricated.
   A quote membership check does not establish scientific entailment.
5. Inspect passages and original sources. Accept the suggestion, save edited wording,
   reject, or reset to pending. Use a decision button to record notes before exporting.
6. Download JSON or the readable TXT review. TXT also contains the complete canonical
   record so provenance is not lost. Signed-in users may explicitly save, reopen,
   update, export or delete their own records after the Phase G migration is applied.

## Supported public sources

- Canonical `https://pubmed.ncbi.nlm.nih.gov/<PMID>/` article links; metadata and
  available abstracts via ESearch/EFetch. Search results are fetched individually so
  one oversized or malformed record does not discard successful records; omissions
  remain visible. No implied full-text/methods review.
- Canonical `https://pmc.ncbi.nlm.nih.gov/articles/PMC<digits>/` links; available
  XML through EFetch. `full text` requires readable XML body paragraphs. Some records
  expose only metadata/abstracts: the demonstration paper PMC4502790 remained
  abstract-only in the 2026-09-18 live EFetch and reuse-aware OAI checks.
- [Exact Enzo CYTO-ID product page](https://www.enzo.com/product/cyto-id-autophagy-detection-kit/).
- [Exact ENZ-51031 manual](https://www.enzo.com/wp-content/uploads/2023/01/ENZ-51031_insert.pdf).
  Text extraction preserves physical PDF page positions; diagrams/tables need visual
inspection. The current 28-page manual supplies 22 complete pages within the
45,000-character evidence budget. Later pages are explicitly outside that extract.

The product identity in a source does not identify the reagent actually used. An
unspecified reagent triggers a question; the software does not guess a catalog number.
Other URLs are rejected before fetching. Redirect destinations and DNS addresses are
validated; HTTPS connections pin a public address while verifying the original hostname.
Responses are limited to 2 MB and supported MIME types. Documents are untrusted data.
PMC/body extracts and manual extracts are bounded; this is not an exhaustive review.

## Verification and evaluation

```sh
.venv/bin/python -m unittest discover -s tests -v
npm run typecheck --prefix frontend
npm run lint --prefix frontend
npm run build --prefix frontend
node --check web/app.js
node --check scripts/browser_react_smoke.cjs
.venv/bin/python -m scripts.evaluate
supabase test db
.venv/bin/python -m scripts.verify_supabase_local
```

After the Free Tier project and environment are confirmed, run the minimal public-safe
live check explicitly:

```sh
.venv/bin/python -m scripts.verify_review_provider_live
```

It performs one synthetic extraction and one synthetic evidence assessment, then
prints model, prompt, source/access, and validation provenance without printing the
key or passage body. It exits blocked without making calls when configuration is absent.

Model evaluation is deliberately batched. After the minimal live check succeeds, use
`--run-model --split dev --max-cases 2`; complete and review development runs before
requesting a held-out batch. Do not increase the batch to consume quota or enable billing.

HTTP tests require loopback socket access. In a restricted sandbox, request the
appropriate execution permission; do not disable the tests or count them as passed.
Browser smoke requires Node, Chrome, an existing `playwright-core` package, and the
server running at port 8000:

```sh
PLAYWRIGHT_PATH=/absolute/path/to/playwright-core node scripts/browser_react_smoke.cjs
PLAYWRIGHT_PATH=/absolute/path/to/playwright-core node scripts/browser_chat_smoke.cjs
PLAYWRIGHT_PATH=/absolute/path/to/playwright-core node scripts/browser_smoke.cjs
```

`CHROME_PATH` can override `/usr/bin/google-chrome`. Screenshots go to ignored
`test-results/`. The React smoke defaults to `http://127.0.0.1:5173`; set
`FRONTEND_URL=http://127.0.0.1:8000` to exercise the FastAPI-served build. The legacy
smoke uses `/legacy` and retains its missing-key-state assumptions.
The React smoke also checks the rendered login/signup/recovery pages, accessible
password-mismatch handling, the public demo link, and mobile overflow. It does not
create an account, send email, or complete Google OAuth.

`data/evaluation_cases.json` contains 16 explicitly synthetic/public cases, split
10 development / 6 held-out. References are **agent-authored drafts awaiting knowledgeable
human review**, not validated ground truth. The fixture checker verifies consistency,
not scientific accuracy. `docs/evaluation-initial.json` records the initial run with
zero model cases. `--run-model` uses the explicitly configured evidence provider and remains
explicit: do not run it until Free Tier/no billing and the minimal live check are
confirmed. Freeze development decisions before a held-out run. Never change expected
labels merely to match outputs; record legitimate
corrections and reasons. See `docs/EVALUATION.md` for the human grading rubric.
Phase H's actual counts, source results and blockers are in
[`docs/EVALUATION_PHASE_H.md`](docs/EVALUATION_PHASE_H.md). The competition script is
[`docs/COMPETITION_WALKTHROUGH.md`](docs/COMPETITION_WALKTHROUGH.md), and
[`docs/FEATURE_VERIFICATION.md`](docs/FEATURE_VERIFICATION.md) separates live,
fixture, demonstration-only and blocked features.

## Privacy and limitations

Unsaved reviews stay in browser memory and temporary server memory, expire one hour after
creation, and are bounded to 24 records / 5 MB per review. Reload starts a new browser
draft session, while Supabase restores the Google login session separately. Live
reviews are bound to both the draft session and the verified account. Restarting the
server removes all unsaved working reviews. There is no automatic disk storage
of user input and no request-content logging. Explicit downloads remain local files;
signed-in users may explicitly create or update private Supabase saved records after
the migration is applied. Sign-in and ordinary review edits never autosave.
Successful AI chat messages, timestamps and actual provider/model provenance are stored
in the signed-in user's owner-scoped Supabase row until that user deletes the chat.
Chat PDF export reads this saved record and does not call a model.
The PDF parser briefly writes the public manual to a temporary file and deletes it.

Search terms and URLs go to public source services. Configured model actions send the
input/context or retrieved passages to the selected external model API. Provider data
terms vary, so use only public or synthetic material for model checks and the first
hosted demonstration.
No local-only processing or confidentiality guarantee is made. The API key remains
server-side. Hosted live reviews require verified Supabase identity and saved records
use RLS, but the public deployment has not yet passed the hosted two-user journey.

Prompt instructions, structured output, and deterministic checks reduce specific failure
modes; they cannot certify reasoning, stop every prompt injection, or guarantee coverage.
Human review remains necessary. No accuracy, time-saving, adoption, clinical, or regulatory
claims have been measured or established. The deployed frontend's public reachability
and hosted integrations remain unverified.

## Official integration references

- [NCBI E-utilities parameters and response formats](https://www.ncbi.nlm.nih.gov/books/NBK25499/)
- [PMC approved retrieval services and reuse limitations](https://pmc.ncbi.nlm.nih.gov/tools/developers/)
- OpenAI references were inspected for the previous candidate implementation. They
  are not active runtime requirements; current target references are recorded in
  `MIGRATION_PLAN.md`.

Phase E checked the current official [Gemini models](https://ai.google.dev/gemini-api/docs/models),
[pricing](https://ai.google.dev/gemini-api/docs/pricing),
[billing](https://ai.google.dev/gemini-api/docs/billing),
[structured output](https://ai.google.dev/gemini-api/docs/structured-output),
[rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), and
[Google Gen AI Python SDK](https://googleapis.github.io/python-genai/) documentation
on 2026-09-18. These references support the implementation choice; they do not prove
access in the user's project.

The 2026-09-20 non-Gemini evidence-provider change checked the current official
[Groq structured-output](https://console.groq.com/docs/structured-outputs) and
[free-plan rate-limit](https://console.groq.com/docs/rate-limits) documentation,
[OpenRouter structured-output](https://openrouter.ai/docs/guides/features/structured-outputs)
and [free-router](https://openrouter.ai/openrouter/free/apps) documentation, and
[NVIDIA NIM guided JSON](https://docs.nvidia.com/nim/large-language-models/1.14.0/structured-generation.html)
documentation. Those pages support the fixed request formats and model restrictions;
they do not prove access, remaining quota, or no-billing status in a particular account.

Phase D rechecked the current official
[NCBI E-utilities documentation](https://www.ncbi.nlm.nih.gov/books/NBK25499/),
[PMC developer guidance](https://pmc.ncbi.nlm.nih.gov/tools/developers/), and
[PMC OAI-PMH reuse behavior](https://pmc.ncbi.nlm.nih.gov/tools/oai/) on 2026-09-18.
The executed live-source evidence and response hashes are recorded in `PROGRESS.md`.

Phase F checked the current official Supabase
[Google sign-in](https://supabase.com/docs/guides/auth/social-login/auth-google),
[OAuth method](https://supabase.com/docs/reference/javascript/auth-signinwithoauth),
[redirect allow-list](https://supabase.com/docs/guides/auth/redirect-urls),
[JWT](https://supabase.com/docs/guides/auth/jwts), and
[signing-key](https://supabase.com/docs/guides/auth/signing-keys) documentation on
2026-09-18. Fixture verification does not establish that the user's dashboard or
Google OAuth client is configured.

Development assistance by Codex is distinct from runtime AI use. The shipped demo
uses curated prose and archived public extracts; it has no runtime model provenance
because no model produced that review during application execution.
