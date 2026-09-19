# Research Guard AI

> **Migration notice:** Phase F implements Supabase Google sign-in and verified
> backend ownership with fixtures. The real OAuth browser round trip is blocked until
> the Supabase Free project and Google provider are configured. Persistent saved reviews
> remain later work. Gemini live access is also still blocked pending its Free Tier
> project check and server-side key. No billing
> activation, paid fallback, public deployment, or later phase is authorized here.

A local research-review application for making claim-to-evidence relationships,
experimental context, and limitations inspectable. Start with the clearly labeled
CYTO-ID demonstration, or create a live review and retrieve public sources.

This is a local preview. The former OpenAI adapter is disabled. The Gemini provider
has passed controlled fixture tests but **has not made a successful live call in the
user's project**. No API key or Free Tier project confirmation was available.
Scientific accuracy has not been measured. See `PROGRESS.md` for actual results
and incomplete phase gates; read `context.md` before continuing any phase.

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

The public demonstration needs no account. Live review/model routes require Google
sign-in after configuring Supabase. Follow [`docs/AUTH_SETUP.md`](docs/AUTH_SETUP.md)
for the exact public environment variables and the separate Google-to-Supabase and
Supabase-to-application redirect settings. No OAuth secret belongs in frontend code.
The demo and public-source retrieval do not require a model key. The manual
adapter additionally requires Poppler's `pdftotext` utility (typically packaged
as `poppler-utils` on Linux or `poppler` on macOS). Missing utility errors remain visible.

For Gemini model actions, first verify in Google AI Studio that the selected project
is on Free Tier with no linked billing. Then configure the backend process only:

```sh
export LLM_PROVIDER=gemini
export GEMINI_API_KEY='set-locally-do-not-commit'
export GEMINI_FREE_TIER_CONFIRMED=true
export GEMINI_EXTRACTION_MODEL=gemini-3.8-flash
export GEMINI_ASSESSMENT_MODEL=gemini-3.8-flash
```

The confirmation variable is an operator attestation; it cannot inspect account
billing. The model settings are configurable but Phase E permits only identifiers on
the code's current verified Free Tier allowlist. Do not configure the legacy OpenAI
variables: that provider is rejected and is not a fallback. Set `NCBI_EMAIL` to an
appropriate contact email for NCBI API requests. Requests are throttled below
three/second per process; multiple processes on the same IP need coordinated rate
limiting.

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
   record so provenance is not lost. No import/restore feature is implemented yet.

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
```

After the Free Tier project and environment are confirmed, run the minimal public-safe
live check explicitly:

```sh
.venv/bin/python -m scripts.verify_gemini_live
```

It performs one synthetic extraction and one synthetic evidence assessment, then
prints model, prompt, source/access, and validation provenance without printing the
key or passage body. It exits blocked without making calls when configuration is absent.

HTTP tests require loopback socket access. In a restricted sandbox, request the
appropriate execution permission; do not disable the tests or count them as passed.
Browser smoke requires Node, Chrome, an existing `playwright-core` package, and the
server running at port 8000:

```sh
PLAYWRIGHT_PATH=/absolute/path/to/playwright-core node scripts/browser_react_smoke.cjs
PLAYWRIGHT_PATH=/absolute/path/to/playwright-core node scripts/browser_smoke.cjs
```

`CHROME_PATH` can override `/usr/bin/google-chrome`. Screenshots go to ignored
`test-results/`. The React smoke defaults to `http://127.0.0.1:5173`; set
`FRONTEND_URL=http://127.0.0.1:8000` to exercise the FastAPI-served build. The legacy
smoke uses `/legacy`. Both assume no API key is configured to test the missing-key state.

`data/evaluation_cases.json` contains 16 explicitly synthetic/public cases, split
10 development / 6 held-out. References are **agent-authored drafts awaiting knowledgeable
human review**, not validated ground truth. The fixture checker verifies consistency,
not scientific accuracy. `docs/evaluation-initial.json` records the initial run with
zero model cases. `--run-model` now uses the configured Gemini provider and remains
explicit: do not run it until Free Tier/no billing and the minimal live check are
confirmed. Freeze development decisions before a held-out run. Never change expected
labels merely to match outputs; record legitimate
corrections and reasons. See `docs/EVALUATION.md` for the human grading rubric.

## Privacy and limitations

Reviews stay in browser memory and temporary server memory, expire one hour after
creation, and are bounded to 24 records / 5 MB per review. Reload starts a new browser
draft session, while Supabase restores the Google login session separately. Live
reviews are bound to both the draft session and the verified account. Restarting the
server removes all reviews. There is no automatic disk storage
of user input and no request-content logging. Only explicit downloads save reviews.
The PDF parser briefly writes the public manual to a temporary file and deletes it.

Search terms and URLs go to public source services. Configured model actions send the
input/context or retrieved passages to the Gemini Developer API. Google's pricing
documentation states that Free Tier content is used to improve its products, so use
only public or synthetic material for Phase E checks. No local-only processing or
confidentiality guarantee is made. The API key remains server-side. This server is for
a trusted local computer, not a multi-user deployment.

Prompt instructions, structured output, and deterministic checks reduce specific failure
modes; they cannot certify reasoning, stop every prompt injection, or guarantee coverage.
Human review remains necessary. No accuracy, time-saving, adoption, clinical, or regulatory
claims have been measured or established. No public deployment has occurred.

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
