# Research Guard AI progress

## 2026-09-16 — Phase 1: architecture

- Read `context.md` in full before starting. No application or PROGRESS.md existed.
- Inspected working tree, git status/history, ancestor instructions, `.agents`, `.codex`,
  Python/Node versions, installed modules, and credential presence without printing secrets.
- Added architecture decision, typed Pydantic schemas, dependency pin, and ignore rules.
- Verification: imports/environment inspected; application tests do not exist yet.
- Consulted official NCBI E-utilities and OpenAI structured-output/model/data documentation.
- Live integration: none verified. PMC browser page returned a challenge; initial shell
  EFetch request failed DNS in the restricted environment. No model credentials configured.
- Next action: reread context and implement Phase 2 interface and transient review service.

| Phase | Implementation | Verification |
| --- | --- | --- |
| 1 Architecture | Decisions and schemas written | Repository/environment inspected; schemas not yet exercised |
| 2 Interface | Pending | Not tested |
| 3 Retrieval | Pending | Initial connectivity blocked |
| 4 Assessment | Pending | No model credentials |
| 5 Worked case | Pending | Source retrieval required |
| 6 Review/export | Pending | Not tested |
| 7 Evaluation | Pending | Not executed |
| 8 Release preparation | Pending | No preview yet |

## Phase 2 — interface implementation; Phase 3 starting

- Reread context before Phase 2 and again before Phase 3.
- Added `web/index.html`, `web/style.css`, `web/app.js`, and `researchguard/reviews.py`.
- Implemented empty/loading/error/demo UI, editable claims, review controls, and invalidation
  of old evidence/decisions on claim edits. Backend routes and browser verification pending.
- Executed schema JSON round trip (passed), `node --check web/app.js` (passed),
  `python3 -m compileall -q researchguard` (passed). These are not usability tests.
- Public PMC EFetch connectivity succeeded outside sandbox DNS restrictions on 2026-09-16:
  HTTP 200, XML, 8,360 bytes. Content still being inspected; adapter not yet verified.

## Phase 3 and Phase 4 — integration implementation

- Implemented restricted HTTPS transport and PubMed/PMC/Enzo adapters with provenance,
  abstract-only distinctions, hashes, bounded content, exact supported URLs, throttling,
  DNS address validation/pinning, and redirect checks.
- Reread context before Phase 4. Added Responses API extraction/comparison with configurable
  model, strict JSON schema, source/quotation/location checks, rejected-output states,
  and prompt version/model provenance. No live model claim is made: credentials absent.
- `python3 -m compileall -q researchguard` passed. Representative adapter checks started.
- Remaining scope: manuals beyond the exact HTML product page, live model verification,
  semantic evaluation, browser journey, and release checks.

## Phase 5 — curated worked case

- Reread context. Retrieved and inspected the exact public Enzo page and the Loos
  PMC record with actual adapters on 2026-09-16. PMC access was **abstract only**.
- Archived two short exact extracts with original location, retrieval timestamp, metadata,
  and response hashes in `data/demo_sources.json`; added `researchguard/demo.py`.
- Curated explanation/wording is labeled synthetic and not a live model result. It makes
  no claim that biological flux changed. Full methods and manual review remain incomplete.
- PubMed search returned identifiers, but a large batched XML response exceeded 2 MB.
  Changed retrieval to fetch individually, retain accessible results, and disclose omissions.
  This fix still requires live retest.

## Phase 6 — review, server, and export

- Reread context. Added loopback HTTP service, per-session temporary records, host/origin
  checks, request limits, one-hour expiry, and bounded review storage.
- Added server-authoritative accept/edit/reject/pending decisions and JSON/TXT exports.
  Original suggestions are preserved; TXT contains the complete canonical record too.
- Executed demo creation, evidence validation, and both export functions successfully
  (7,798 JSON characters / 9,918 TXT characters in that smoke run).
- Browser and HTTP-level verification still pending. No model call has been executed.
- Next action: Phase 7 safety tests, public/synthetic evaluation fixtures and honest denominators.

## Phase 7 — executed checks and evaluation preparation

- Reread context. Added `tests/test_guardrails.py`, `tests/test_http.py`, browser smoke,
  16 evaluation cases (10 development / 6 held-out), and fixture/model evaluation runner.
- Executed `python3 -m unittest discover -s tests -v`: **36/36 passed**, including HTTP
  checks outside the sandbox because it disallows sockets. Initial 28 guardrail tests
  also passed. No skipped tests or model integration claims are hidden in that count.
- Browser smoke executed with installed Playwright 1.57.0 and system Chrome: passed
  empty/demo/live states, edited/rejected decisions, JSON export provenance, missing
  evidence/key, claim editing, safe text rendering, and 390px mobile overflow check.
  Screenshots saved under ignored `test-results/`; no browser page errors.
- `python3 -m scripts.evaluate --output docs/evaluation-initial.json`: **16/16 fixture
  consistency checks**, **0 model cases run**. Scientific support, context matching,
  false alarms, uncertainty handling, and extraction quality remain unmeasured. References
  are agent-authored drafts, not human-validated ground truth; Phase 7 is incomplete.
- Live retest on 2026-09-16: PubMed returned three records (two abstracts, one metadata-only);
  documented PMC212403 example returned full text with 58 extracted paragraphs. The Loos
  article remains abstract-only. Enzo exact product HTML retrieval also verified live.
- One network-check approval review timed out, then the permitted single retry succeeded.
- Local preview started on 127.0.0.1:8000; no public deployment. Next: Phase 8 release
  guide, visual inspection, boundedness/review, and final state verification.

## Phase 3 follow-up during release review — exact official manual

- Reread context before resuming retrieval work. Inspected the official page's linked
  ENZ-51031 manual; retrieved the exact PDF (1,119,723 bytes) on 2026-09-16.
- Added optional `pdftotext` adapter with an 8-second parser deadline, 250 KB text limit,
  30-page / 45,000-character extract limits, exact document identity, and physical PDF
  page locations. Temporary public PDF file is deleted after parsing; no user input used.
- Actual downloaded PDF parsed successfully: 22 complete physical pages within budget.
  The 28-page document is not represented as a complete visual/methods review.
- UI supported-source copy and architecture updated; tests added for missing parser,
  wrong manual identity, and physical page provenance. Rerun pending.

## 2026-09-18 — Migration Phase A: verified inventory and migration baseline

Status: **passed for Phase A audit/documentation only**. Phases B–H are not started
and will be supplied by the user sequentially, one phase at a time.

### Changes made

- Reread `context.md`, this progress log, `ARCHITECTURE.md`, README, existing code,
  tests, fixtures, and evaluation notes. No applicable project/ancestor `AGENTS.md`
  was found; repository `.agents` and `.codex` directories are empty.
- Updated `context.md` and `ARCHITECTURE.md` with the approved target: FastAPI,
  React/TypeScript/Tailwind, Supabase Free Google authentication plus explicit saves,
  and Gemini Developer API through an AI Studio Free Tier project.
- Recorded the strict cost boundary: no billing activation, paid services, credit
  purchases, paid fallback, or public deployment. OpenAI models and implementation
  are previous candidates/legacy code, not active requirements or fallbacks.
- Added `MIGRATION_PLAN.md` with a code-backed component inventory, current HTTP
  contract, missing features, session/ownership/API/provider migration risks, free-tier
  prerequisites, and reserved entries for B–H. Backlog items are deliberately
  unassigned; they are not inferred phase definitions.
- Updated README migration notices so its legacy setup cannot be mistaken for active
  OpenAI guidance. No framework, provider, authentication, persistence, or deployment
  implementation was performed in Phase A.

### Checks actually executed

- `python3 -m unittest discover -s tests -v`: first sandboxed attempt failed during
  HTTP test setup because loopback socket creation was denied; it was not counted.
  Rerun with loopback permission: **39/39 passed**, no skips.
- Existing Chrome/Playwright smoke against a temporary local preview: **passed**
  empty/demo/live states, edited/rejected decisions, JSON provenance, missing evidence
  and key states, claim editing, safe text rendering, no page errors, and 390 px
  mobile overflow check. The temporary server was stopped afterward.
- `python3 -m compileall -q researchguard scripts tests`: passed.
- `node --check web/app.js`: passed.
- `python3 -m scripts.evaluate`: **16/16 fixture-consistency checks**; 10 development
  plus 6 held-out cases; **0 model cases run**. Scientific performance remains unmeasured.
- Cached official manual parser check: 22 physical-page extracts with SHA-256
  `eecaece65b7125d8abbb325917a824d2b3415adea5c79218f57094b42e574f72`.
  This was a cached-document check, not fresh network verification.
- Final resume checks: Python compile, JavaScript syntax, evaluation consistency, and
  documentation whitespace checks passed after cleanup. A temporary pre-edit hash
  snapshot had expired by the resumed session, so it is not claimed as fresh evidence.

### Verified state and limits

- Implemented and verified within test scope: Pydantic review schemas; review edits
  and decisions; deterministic source/quotation/location checks; PubMed/PMC/exact Enzo
  parsing and source-transport guardrails with fixtures; curated demo; JSON/TXT export;
  legacy transient-session HTTP/UI behavior; evaluation fixture consistency.
- Implemented but unverified or partial: legacy live OpenAI extraction/assessment;
  current external-source availability; scientific entailment/model quality; broader
  PDF robustness; successful live retrieval in the browser; concurrency/cross-worker
  behavior; authenticated ownership; real model provenance.
- Missing: FastAPI, React/TypeScript/Tailwind, Gemini adapter, Supabase/Google auth,
  database migrations/RLS, explicit save/load/update/delete, token verification,
  two-user isolation, persistence revisions, and new-provider privacy notices.

### Blockers and unverified assumptions

- FastAPI, Supabase Python support, and `google.genai` were not installed in the
  inspected environment. Gemini/Supabase configuration variables were absent.
- No Supabase or AI Studio account/project, free-tier eligibility, quota, region,
  model availability, OAuth callback, or data-term behavior was verified.
- Current `X-Review-Session` is a client-created transient capability, not authenticated
  identity. It must never become the saved-review owner identifier.
- All existing application files remain untracked except the modified `context.md`;
  do not clean/reset this working tree. Establishing a source-control snapshot was
  outside Phase A and was not performed.

### Manual action required

None to complete Phase A. When ready, provide the Phase B instruction. Later account
integration will require user-controlled free-tier projects/configuration and two test
users, but Phase A did not create accounts, apply SQL, call a model, activate billing,
purchase credits, or deploy anything.

## 2026-09-18 — Migration Phase B: FastAPI HTTP layer

Status: **PASS for Phase B's local HTTP migration. Stop after Phase B.**

### Changes made

- Reread `context.md`, this log, `MIGRATION_PLAN.md`, `ARCHITECTURE.md`, repository
  instructions, existing services, frontend and tests before implementation and after
  the resumed context. No applicable repository/ancestor `AGENTS.md` was found.
- Added `researchguard/api.py`: FastAPI routes for health/config, live and demo review
  creation, review retrieval, claim/context edits, extraction, source retrieval,
  assessment, decisions, and validated JSON/TXT export. Responses use the existing
  Pydantic `Review`; provider/retrieval/validation/decision/export logic stays outside
  route functions.
- Added `researchguard/store.py` for expiring process-local drafts, capacity limits,
  session-capability isolation, async per-review locks, snapshots and checked commits.
  Mutations use deep-copy, service call, complete validation, byte-limit check, then
  commit. Failed or timed-out copies are not saved.
- Added `researchguard/settings.py` for validated request/review/storage/time/concurrency
  limits and exact local frontend origins. CORS allows the two configured local React
  development origins with credentials disabled; current same-origin preview requests
  also work. Wildcards and non-local origins are rejected.
- Offloaded synchronous retrieval, PDF/provider work and export validation to a bounded
  thread pool. Retrieval and model routes have configurable request deadlines. Timed-out
  thread work cannot commit its private review copy; the pool bounds still-running work.
- Added context editing to `reviews.py`. Material context changes invalidate all current
  assessments/decisions and detach old attempt linkage while retaining provenance history.
  Existing claim-edit invalidation and server-derived accepted wording remain intact.
- Replaced the standard-library server launcher with loopback-only Uvicorn, pinned the
  tested FastAPI/Uvicorn/HTTPX versions, updated the existing frontend to the new REST
  paths/methods, and kept the small same-origin preview available for parity testing.
- Replaced legacy socket-handler tests with ASGI HTTP tests and documented the actual
  contract/startup/environment variables in `docs/API.md`. Updated `context.md`,
  `ARCHITECTURE.md`, `MIGRATION_PLAN.md`, and README for the completed Phase B state.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **40/40 passed**, no skips.
  Nine FastAPI/store tests cover main routes, config/health, exact CORS and wildcard
  rejection, invalid/unsafe/oversized/content-type requests, session read/write isolation,
  claim and context invalidation, canonical JSON/TXT export equality, demo/live separation,
  missing model credentials, expiry, bounded worker count, timeout and rollback. The
  existing 31 source/evidence/runtime tests also passed, including DNS/redirect/byte/MIME,
  parsers, source IDs, exact quote/location checks, decisions and export provenance.
- Actual Uvicorn startup on `127.0.0.1:8000`: passed. Loopback `GET /api/health` returned
  `status=ok`; `/api/config` returned `unavailable_missing_credentials` with the legacy
  provider label and no credential value. The temporary server was stopped cleanly.
- Final installed-browser smoke against that FastAPI server: **passed** empty/demo/live,
  edited/rejected decisions, downloaded JSON provenance, missing evidence/key states,
  claim edits, safe text rendering, 390 px mobile overflow, failed-request tracking and
  zero page errors. The first run exposed a same-origin rejection; it was fixed, covered
  by an HTTP test, and the clean final script was rerun successfully.
- `.venv/bin/python -m compileall -q researchguard scripts tests`: passed.
- `node --check web/app.js` and `node --check scripts/browser_smoke.cjs`: passed.
- `.venv/bin/python -m scripts.evaluate`: **16/16 fixture consistency**, 10 development
  and 6 held-out fixtures, **0 model calls**; scientific performance remains unmeasured.
- `.venv/bin/python -m pip check`: no broken requirements. Tested versions: FastAPI
  0.115.12, Starlette 0.46.2, Uvicorn 0.34.2, HTTPX 0.28.1, Pydantic 2.13.4.
- `git diff --check`: passed. The project files remain largely untracked from the
  pre-existing working tree; no reset, clean, commit, deployment or paid action occurred.

### Blockers and unverified assumptions

- No Phase B blocker remains. Initial dependency installation failed under restricted
  DNS and succeeded after approved package-download access. Initial loopback bind failed
  under sandbox restrictions and succeeded with approved local-binding access; these
  failed attempts were not counted as verification.
- The HTTP source/assessment route success cases use controlled archived fixtures. No
  fresh live PubMed/PMC/Enzo retrieval or real model call was executed in Phase B.
  Existing source-validation behavior is verified by tests, not freshly verified against
  current external services.
- The retained OpenAI provider is legacy code and remains a previous candidate, not an
  active requirement or fallback. Missing credentials were verified; successful provider
  access, model quality, Gemini Free Tier and all new-provider behavior remain unverified.
- `X-Review-Session` is still a client-created temporary capability, not authentication.
  Storage, locks, worker limits and NCBI throttling are process-local, so the documented
  startup uses one Uvicorn worker. Cross-worker/session persistence is not claimed.
- A Python thread already running at route timeout cannot be forcibly stopped. It remains
  bounded by the worker pool and lower transport/parser limits, and its private review
  copy cannot commit, but repeated timeouts can temporarily occupy the pool.
- React/TypeScript/Tailwind, Supabase/Google authentication, saved-review persistence,
  RLS/two-user isolation, Gemini, free-tier account/quota verification, and public
  deployment were not part of Phase B and do not work merely because FastAPI does.

### Manual action required

None to complete Phase B. Local startup is:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m researchguard.server --port 8000
```

No secret is required for health, the curated demo, transient review editing, or fixture
tests. `docs/API.md` lists the exact non-secret environment names and defaults. Do not
configure the retained OpenAI path under the approved direction. Supply Phase C when
ready; Phase B stops here.

## 2026-09-18 — Migration Phase C: React/TypeScript/Tailwind interface

Status: **PASS for Phase C's local interface migration. Stop after Phase C.**

### Changes made

- Reread `context.md`, this log, `MIGRATION_PLAN.md`, `ARCHITECTURE.md`, repository
  instructions, the FastAPI contract, old frontend and existing tests before resuming.
  No applicable repository/ancestor `AGENTS.md` was found.
- Added `frontend/`, a Vite React/TypeScript SPA styled with Tailwind CSS. Current
  installed versions are React/React DOM 19.3.0, TypeScript 6.0.3, Vite 8.3.0,
  Tailwind CSS and its Vite plugin 4.3.3, and the React Vite plugin 6.1.1. The setup
  follows the current official React, Vite, TypeScript and Tailwind documentation
  inspected during this phase.
- Connected the SPA to the real Phase B `/api` routes with relative URLs and one
  random browser-session capability. Vite binds to `127.0.0.1:5173` and proxies
  `/api` to FastAPI on `127.0.0.1:8000`. No provider SDK, model call, key, or
  `VITE_` runtime variable was added to frontend code.
- Implemented live input, intended use, optional experimental context/source URLs,
  a prominent curated-demo label, editable live claims, observation versus
  interpretation, claim-level evidence/access states, source passages and limitations,
  suggested wording, next verification questions, decisions, and JSON/TXT exports.
  Empty, loading, request-error, partial-access and unavailable-model states are
  explicit and use beginner-friendly scientific wording.
- Kept demo records immutable under the existing server rules. Demo output is always
  labeled as predefined and is never substituted for a failed live request.
- Prevented stale evidence display by deriving visible claim sources only from the
  claim's current retrieval attempts. The server remains authoritative: a material
  live-claim edit returns a canonical review with the old assessment and decision
  cleared and historical attempts detached from the current claim.
- Updated `researchguard/api.py` to serve a generated `frontend/dist` build at `/`
  when present. The pre-React `web/` frontend remains available at `/legacy` and is
  the root fallback when no React build exists. Retrieval, model providers, evidence
  validation, decisions and export logic remain separate from the HTTP/UI layers.
- Added `scripts/browser_react_smoke.cjs` for the Phase C journey and adjusted the
  existing legacy smoke to target `/legacy`. Updated `context.md`, `ARCHITECTURE.md`,
  `MIGRATION_PLAN.md`, README and `docs/API.md` with the implemented build, preview,
  route-consumption and preservation behavior.

### Checks actually executed

- `npm run typecheck` in `frontend/`: **passed** with TypeScript project references.
- `npm run lint` in `frontend/`: **passed** with no reported warnings or errors.
- `npm run build` in `frontend/`: **passed** with Vite 8.3.0; 17 modules transformed.
  Final output: 0.64 kB HTML, 25.65 kB CSS and 249.76 kB JavaScript before gzip.
- Final Chrome/Playwright smoke against the FastAPI-served production build at
  `http://127.0.0.1:8000`: **passed** keyboard path, demo evidence/access and
  edited decision/export, separate live missing-model state, material claim-edit
  invalidation, failed API handling, 390 px layout, and zero page errors. An earlier
  development-server run at `http://127.0.0.1:5173` passed the same React journey.
- Preserved-interface Chrome smoke at `http://127.0.0.1:8000/legacy`: **passed**
  empty/demo/live states, edited/rejected decisions, canonical JSON provenance,
  missing evidence/credential states, claim edits, safe text rendering, mobile
  overflow and zero page errors.
- `.venv/bin/python -m unittest discover -s tests -v`: **40/40 passed**, no skips.
  This includes source transport/parsing, evidence source/quote/location validation,
  FastAPI session isolation, invalidation, canonical exports, request limits, CORS,
  expiry and timeout rollback. The existing upstream FastAPI/Python 3.14 coroutine
  deprecation warning remains; it did not fail the suite.
- `.venv/bin/python -m compileall -q researchguard scripts tests`, `node --check`
  for both browser scripts and `web/app.js`: **passed**.
- Focused scan of `frontend/dist`, sources and Vite configuration for `VITE_`,
  OpenAI/Gemini/Supabase credential names and common key shapes: **zero matches**.
  The bundle uses relative `/api` paths. `git diff --check`: **passed**.
- The first final browser command lacked the external `playwright-core` path and did
  not run; the documented command was rerun with the installed package path and passed.
  The temporary loopback FastAPI process was stopped cleanly after verification.

### Blockers and unverified assumptions

- No Phase C browser blocker remains; Chrome execution was available. The keyboard
  route and narrow viewport were exercised, but this is not a comprehensive assistive
  technology or manual accessibility audit.
- Successful live retrieval, current external-source availability, scientific
  assessment quality, and any live model call were outside this interface phase and
  were not verified. Demo/source fixtures do not establish those integrations.
- The visible missing-credential state reflects the retained legacy provider contract.
  Gemini Free Tier is still unimplemented. No Gemini or Supabase account, credentials,
  free quota, project settings, authentication, persistent save, or owner isolation
  was configured or tested.
- `X-Review-Session` remains a client-created temporary draft capability. React does
  not add authentication or durable storage; refresh starts a new session and FastAPI
  remains single-worker/process-local.
- Demo records cannot be materially edited by design. The requested browser coverage
  therefore uses the demo for evidence inspection/decision/export and a separate live
  review for claim editing and stale-evidence invalidation.

### Manual action required

None to complete Phase C. For the development preview, start FastAPI on port 8000 and
run `npm run dev --prefix frontend`, then open `http://127.0.0.1:5173`. For the tested
same-origin preview, run `npm run build --prefix frontend`, start FastAPI, and open
`http://127.0.0.1:8000`; the old interface is at `/legacy`. No secret is required for
the curated demo or transient editing. Supply Phase D when ready; Phase C stops here.

## 2026-09-18 — Migration Phase D: retrieval adapter verification and repair

Status: **PASS for Phase D's supported retrieval adapters. Stop after Phase D.**

### Changes made

- Reread `context.md`, this log, `MIGRATION_PLAN.md`, `ARCHITECTURE.md`, repository
  instructions, retrieval/transport code, schemas, archived demo sources and existing
  tests before implementation. No applicable repository/ancestor `AGENTS.md` was found.
- Inspected the current official NCBI ESearch/EFetch documentation, PMC developer
  access rules and PMC OAI-PMH reuse behavior. Kept the supported official E-utilities
  path and the existing below-three-requests/second process throttle. PMC documentation
  explicitly says that not every PMC article is available for automated full-text reuse.
- Preserved the individual PubMed fetch repair: ESearch returns up to three PMIDs and
  each PMID is retrieved by a separate EFetch call. One oversized, malformed or
  unavailable record therefore does not discard readable records from the search.
  Added omission text to both retained source limitations and the retrieval-attempt
  summary; a response missing the requested PMID is now an explicit parse failure.
- Narrowed PubMed XML paths to the requested record's own title, abstract, authors,
  date and `PubmedData/ArticleIdList`. The former descendant-wide identifier search
  could select a PMCID from a cited reference: live PMID 25484088 incorrectly appeared
  as PMC2856980 before the repair and correctly resolves to PMC4502790 afterward.
- Changed PMC access classification so a record is `full text` only when the official
  XML contains at least one readable body paragraph. A PMCID, HTTP 200, article XML,
  or empty `<body>` is insufficient. Abstract passages remain clearly labeled and
  body locations remain `XML body paragraph N` positions in the hashed response.
- Kept the exact Enzo product-page and manual allowlist. The product record now retains
  its visible page version (`Last modified: May 29, 2024`). The exact official page
  links the already-supported ENZ-51031 PDF; the parser still verifies PDF identity,
  retains physical-page locations and preserves the HTTP modification date and hash.
- Improved transport timeout reporting without changing the host allowlist, pinned-IP
  TLS connection, DNS/public-address checks, redirect validation, MIME/encoding checks,
  2 MB response limit, overall deadlines or no-proxy behavior.
- Added `scripts/verify_retrieval_live.py`, a read-only verifier that records metadata,
  access levels, locations, versions and hashes without writing retrieved documents or
  printing passage bodies. Updated context, architecture, migration plan and README to
  match the verified Phase D behavior.

### Live source access verified on 2026-09-18

- Representative PubMed query `autophagosome flux measurement`: **3/3 records
  retrieved through separate EFetch calls**, PMIDs 17611390, 27818143 and 29909716.
  All three exposed abstracts, not full text. SHA-256 values respectively:
  `549acc68b03f72518fe26a93309cc2734c55095f70d6e4d2eee5ad069f118740`,
  `b32b885cc64cb580bdbdf9570bf106d1740a0899f1f94bd88a97582eff191e23`,
  `9565ec4467494a4266b6149c6b2e0f60dfd5041cd7818116e965aa1259b418e6`.
- PubMed PMID 25484088: abstract access, PMCID **PMC4502790**, response SHA-256
  `bbb1b34b4aceaf1876ac8abbd2feee8d8ac7b91befcae892b4e91ef369d02b46`.
- PMC8270360: verified reusable **full-text body content**, 39 retained passages
  comprising abstract material and 35 actual body paragraphs, from `Abstract,
  paragraph 1` through `XML body paragraph 35`; response SHA-256
  `d4e447868dd7e9b025417ce862cba533744e63a9633003229cd72eb9f18adacf`.
- Demonstration paper PMC4502790: EFetch returned 8,360 bytes containing one abstract
  and zero body elements; adapter access remains **abstract** with response SHA-256
  `5792568f73adf82c0b18af8321742fe341fb08a6ecedac813374cfc28edbaed2`.
  PMC OAI-PMH supplied front matter (`pmc_fm`) but rejected full-text XML (`pmc`) with
  HTTP 400. A human-readable PMC page exists, but no permitted automated full-text body
  was established through the approved retrieval services.
- Exact Enzo CYTO-ID page: accessible, 160 bounded text blocks retained, visible version
  `Last modified: May 29, 2024`, response SHA-256
  `830ef0c8d7feb2d12e1d1b44c2acae12eab07c84806944b673d0cc2cf313a8a4`.
  The relevant lysosomal-inhibition passage remained present.
- Exact linked ENZ-51031 manual: accessible and safely parsed. The PDF has 28 physical
  pages; 22 complete pages fit the existing 45,000-character evidence bound, with
  locations `PDF physical page 1` through `PDF physical page 22`. HTTP version:
  `Tue, 27 Jun 2023 11:15:20 GMT`; SHA-256
  `eecaece65b7125d8abbb325917a824d2b3415adea5c79218f57094b42e574f72`.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **46/46 passed**, no skips.
  Retrieval coverage includes individual oversized-record isolation, successful-record
  preservation and explicit omissions, PubMed canonical identifier scoping, abstract
  versus nonempty PMC body classification, exact passage text/locations, visible Enzo
  version, manual identity/pages, declared and streamed size limits, timeout, HTTP 429,
  malformed/entity XML, content type, unsafe URLs, mixed/private DNS and unsafe redirect
  rejection. FastAPI/session/export/evidence checks also remained green. The existing
  upstream FastAPI/Python 3.14 deprecation warning did not fail the suite.
- `.venv/bin/python -m scripts.verify_retrieval_live`: **passed** with the live results
  and hashes above. This also asserted source IDs, retrieval-run IDs, ISO timestamps,
  64-character hashes, access levels, nonempty locations and the official product-to-
  manual link. The initial run found an overly strict verifier assertion that rejected
  intentionally preserved PDF layout whitespace; the verifier was corrected without
  changing the adapter, and the complete live run then passed.
- `.venv/bin/python -m compileall -q researchguard scripts tests`: passed.
- `git diff --check`: passed for tracked changes.
- The initial live request inside the restricted sandbox failed at DNS resolution. It
  was not counted as a code failure or live pass. The same adapter succeeded when the
  approved read-only network check was run with network access; no URL rule, DNS check,
  redirect rule or content limit was bypassed.

### Remaining limitations

- The oversized PubMed failure path is deterministic fixture coverage; the live query
  confirmed the repaired one-PMID-per-EFetch behavior but did not happen to return an
  individually oversized record on this date.
- Live results are point-in-time access checks, not availability guarantees. PubMed
  abstracts and PMC body access can change. PMC4502790 remains abstract-only for the
  application unless an approved automated service later supplies permitted body XML.
- HTML block numbers are accurate for the recorded Enzo response hash but can move when
  the page changes. The manual parser preserves text layout, not diagrams or table
  meaning, and the evidence extract omits pages beyond the 45,000-character bound.
- Retrieval proves access and provenance, not relevance, scientific support, article
  quality or experimental applicability. Model assessment and scientific evaluation
  remain outside Phase D.

### Manual action required

None to complete Phase D. `NCBI_EMAIL` remains the optional non-secret contact setting
recommended for routine E-utilities use. No account, key, paid access, paywall bypass,
deployment or later migration phase was used. Supply Phase E when ready; Phase D stops
here.

## 2026-09-18 — Migration Phase E: Gemini integration

Status: **BLOCKED at live verification.** Implementation and controlled fixture checks
pass, but the required minimal live extraction and assessment could not run because no
Gemini key or verified AI Studio Free Tier/no-billing project was available. Stop after
Phase E.

### Changes made

- Reread `context.md`, this log, `MIGRATION_PLAN.md`, `ARCHITECTURE.md`, repository
  instructions, the assessment/retrieval/export services, HTTP contract, interfaces,
  tests, and evaluation runner before resuming. No applicable repository/ancestor
  `AGENTS.md` was found.
- Inspected current official Gemini model, pricing, billing, structured-output, rate-
  limit, API-error, token, and Google Gen AI Python SDK documentation. Pinned and
  installed `google-genai==2.24.0`, the current official SDK release inspected on
  2026-09-18.
- Selected stable text endpoint `gemini-3.8-flash` for both tasks because the official
  model page lists that endpoint and the current pricing table lists Free Tier input
  and output as free of charge. This is a documentation-backed default only; actual
  availability in the user's project is unverified.
- Added `researchguard/providers/` with a provider interface, explicit selection, and
  bounded Gemini structured-output adapter. `LLM_PROVIDER` defaults to `gemini`;
  extraction and assessment models are independently configurable. The current
  verified-free allowlist contains only `gemini-3.8-flash`.
- Added a live-use gate: `GEMINI_API_KEY` must be server-side and
  `GEMINI_FREE_TIER_CONFIRMED=true` must be set only after checking the actual AI Studio
  project has Free Tier and no billing. The flag is an operator attestation and does
  not itself inspect billing.
- Disabled the old OpenAI runtime path. Selecting `openai`/`legacy_openai` returns an
  unavailable state, the source transport no longer permits `api.openai.com`, and no
  active Python runtime references the old key/model variables. There is no provider,
  model, paid, credit, or demonstration fallback.
- Preserved `assessment.py` prompts and the existing extraction, source-ID, exact
  quotation/location, evidence-relationship, review, decision, invalidation, retrieval,
  and export behavior. Routes still call the same services; provider credentials stay
  outside the canonical review.
- Gemini requests serialize retrieved evidence as untrusted JSON data, request the
  Pydantic output schema with `application/json`, and configure no tools, Google Search
  grounding, or cached content. Application code requires a normal stop, nonempty
  bounded output, returned model version, and a second Pydantic parse before existing
  deterministic evidence validation runs.
- Added bounds: 120,000 input bytes, 64,000 output bytes, 2,048 extraction or 4,096
  assessment output tokens, two concurrent provider calls, five seconds to acquire a
  slot, 60-second SDK timeout, and at most two attempts for HTTP 500/502/503/504.
  HTTP 429 is not retried and produces an explicit Free Tier rate/quota exhausted
  message. Provider response details are not echoed into errors.
- Model runs record task, requested and returned model, prompt version
  `researchguard-2026-09-18-gemini-v1`, timestamp, source IDs, and validation results.
  Existing source records continue to hold access levels, exact passages/locations,
  timestamps, document versions and hashes. Added a synthetic-only live verifier that
  reports this provenance without printing its key or passage body.
- Updated `/api/config`, React and legacy unavailable-service states, README,
  `docs/API.md`, `context.md`, `ARCHITECTURE.md`, and `MIGRATION_PLAN.md`. No key or
  `VITE_` secret was added to the frontend.

### Fixture and local checks actually executed

- Final `.venv/bin/python -m unittest discover -s tests -v`: **54/54 passed**, no
  skips. New provider fixtures cover missing key, unconfirmed Free Tier, disabled
  OpenAI selection, malformed model JSON, invalid-key HTTP 401, rate/quota HTTP 429,
  input/output limits, incomplete output, structured schema/MIME, output-token settings,
  no tools/cache, bounded retry policy, non-allowlisted model rejection, returned-model/
  prompt provenance, source IDs/access levels, validation outcomes, and key absence
  from exports. Provider-path unknown source IDs and nonexistent quotations are rejected;
  the existing wrong-location, session-isolation, invalidation, retrieval and export
  checks remained green. The existing upstream FastAPI/Python 3.14 deprecation warning
  did not fail the suite.
- One intermediate full-suite run was **50 passed / 1 failed** because a new test
  incorrectly treated the public environment-variable name `GEMINI_API_KEY` in a safe
  status message as a credential leak. The assertion was corrected to check the actual
  fixture secret value; the complete final suite then passed.
- `npm run typecheck --prefix frontend`: passed. `npm run lint --prefix frontend`:
  passed. `npm run build --prefix frontend`: passed with Vite 8.3.0; 17 modules,
  0.64 kB HTML, 25.65 kB CSS and 249.70 kB JavaScript before gzip.
- `.venv/bin/python -m compileall -q researchguard scripts tests`: passed.
  `node --check` passed for `web/app.js` and both browser scripts.
- `.venv/bin/python -m scripts.evaluate`: **16/16 fixture consistency**, 10
  development and 6 held-out fixtures, **0 model cases**. Scientific entailment,
  context matching, false alarms and uncertainty quality remain unmeasured.
- `.venv/bin/python -m pip check`: no broken requirements. Installed SDK version was
  confirmed as `google-genai 2.24.0`.
- Frontend source/build scan for `GEMINI_API_KEY`, `OPENAI_API_KEY`, common Google key
  prefixes and the fixture secret: **zero matches**. Backend scan found zero credential
  logging/export patterns and zero active OpenAI runtime URL/key/model references.
  `git diff --check` passed for tracked changes.

### Live check and blockers

- `env -u GEMINI_API_KEY -u GEMINI_FREE_TIER_CONFIRMED -u LLM_PROVIDER \
  .venv/bin/python -m scripts.verify_gemini_live`: exited **2 / blocked**, reporting
  `unavailable_missing_credentials` and `live_calls_attempted: 0`. This was an
  intentional preflight result, not a failed provider request and not a live pass.
- No API key, AI Studio project state, Free Tier eligibility, billing linkage, actual
  project model list, project rate/quota limits, returned model snapshot, successful
  structured extraction, or successful source-grounded assessment was verified live.
- Fixture responses prove local request construction, parsing, error mapping and
  deterministic validation behavior. They do not prove the service accepts the schema,
  the selected model is enabled in the actual project, or that model output is
  scientifically correct.
- Free Tier documentation says submitted content is used to improve Google's products.
  Phase E therefore authorizes only public or synthetic material for the live check;
  private/unpublished laboratory text remains outside the verified workflow.

### Manual action required

1. In Google AI Studio, select the intended project and verify it is **Free Tier**, has
   **no linked billing**, and shows `gemini-3.8-flash` as available. Google AI Pro app
   access is not evidence of Gemini API access.
2. Set `GEMINI_API_KEY` only in the local backend environment. Do not paste it into
   chat, put it in a `VITE_` variable, commit it, or enable billing/credits.
3. Set `LLM_PROVIDER=gemini`, `GEMINI_FREE_TIER_CONFIRMED=true`, and optionally set both
   model variables to the documented default. Then run:

   ```sh
   .venv/bin/python -m scripts.verify_gemini_live
   ```

If that command reports unavailable access or exhausted quota, leave the integration
unavailable. Do not activate billing, buy/redeem credits, select a paid model, or use a
provider/demo fallback. Phase E remains **BLOCKED** until the command completes both
synthetic calls and records their actual returned models and validation outcomes.

## 2026-09-19 — Migration Phase F: Supabase Auth with Google sign-in

Status: **BLOCKED at live OAuth verification.** The independent SPA, backend token
verification, ownership, failure-state and public-demo work is implemented and passes
local/fixture checks. A real valid sign-in, restored session and sign-out cannot be
claimed until the user configures the Supabase Free project and Google OAuth client and
the complete browser redirect round trip succeeds. Stop after Phase F.

### Changes made

- Reread `context.md`, this progress log, `MIGRATION_PLAN.md`, `ARCHITECTURE.md`, the
  FastAPI/React/store code and repository state before implementation and again after
  resuming. No applicable repository or ancestor `AGENTS.md` was found.
- Read the current official Supabase Google login, JavaScript `signInWithOAuth`, redirect
  allow-list, JWT/JWKS and signing-key documentation. Pinned
  `@supabase/supabase-js==2.116.0`, the current release inspected for Phase F, and
  `PyJWT[crypto]==2.14.0`.
- Added a React SPA Supabase client using the supported implicit OAuth flow. The client
  persists and refreshes sessions, restores on reload, clears rejected/expired local
  sessions, handles provider cancellation/callback failure, and signs out remotely with
  local cleanup on failure. There is no application OAuth callback route and no
  Next.js/server-component code.
- Restricted OAuth return destinations to exact local origins on ports 5173 and 8000.
  The primary configured development address is `http://127.0.0.1:5173/`; unsafe hosts,
  paths, schemes and ports are rejected before starting OAuth.
- Added explicit React states for checking sign-in, signed out, signed in, auth error and
  unavailable auth configuration. Live creation is disabled while logged out. Ending or
  losing a session clears a displayed live review. The curated demo and its decisions/
  exports remain available without a token, including when stale auth restoration fails.
- Added `researchguard/auth.py`. FastAPI retrieves the configured project's asymmetric
  JWKS and accepts only ES256/RS256 access tokens after verifying signature, exact issuer,
  expiry, `authenticated` audience and role, and a UUID subject. It never accepts a user
  ID from browser input or trusts an unverified JWT decode. JWKS verification runs in the
  existing bounded thread pool with a 10-second outer timeout.
- Added `GET /api/auth/me`. Live review creation and every subsequent live read/mutation,
  model request and export require a bearer token. Temporary live records are bound to
  both the opaque browser session and verified JWT subject; a different verified user
  receives `404`. Demo records remain public within their temporary browser session.
- Preserved the canonical review schema, retrieval/model/evidence services, edit
  invalidation, decisions and exports. No Supabase table, persistent saved-review route,
  RLS policy, privileged key, autosave, public deployment or later-phase feature was
  added.
- Added `docs/AUTH_SETUP.md` and `frontend/.env.example`. The setup guide distinctly
  identifies Google's redirect to
  `https://<PROJECT_REF>.supabase.co/auth/v1/callback` and Supabase's redirect back to
  `http://127.0.0.1:5173/`. It documents only `SUPABASE_URL`,
  `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`; secrets stay in dashboards or
  server-only environments.
- Updated `context.md`, `ARCHITECTURE.md`, `MIGRATION_PLAN.md`, README, API documentation
  and the React browser smoke journey to match the actual Phase F boundary.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **59/59 passed**, no skips.
  New cryptographic fixtures cover a valid signed token and rejection of expired,
  malformed, tampered, wrong-issuer, wrong-audience, wrong-role, non-UUID-subject and
  HS256 tokens. HTTP checks cover valid fixture identity, missing bearer rejection,
  public demo access without a token, live-route enforcement, same-user browser-session
  isolation and different-user ownership isolation. Existing source-validation,
  invalidation, export and provider checks remained green.
- `npm run test:auth --prefix frontend`: passed. Tests cover the exact local redirect
  allowlist and distinct cancelled/failure callback states.
- `npm run typecheck --prefix frontend`: passed. `npm run lint --prefix frontend`:
  passed with no warnings. `npm run build --prefix frontend`: passed with Vite 8.3.0;
  62 modules, 0.64 kB HTML, 25.68 kB CSS and 470.17 kB JavaScript before gzip.
- Actual loopback FastAPI startup and `/api/health`: passed. Headless Chrome against
  `http://127.0.0.1:8000` passed the signed-out UI, disabled live action, public demo,
  evidence/access display, edited decision, JSON export, failed-demo-request handling,
  keyboard path and 390 px overflow checks with zero page errors. The first smoke run
  exposed an obsolete assertion that expected a failed refresh to erase the current
  demo; the assertion was corrected to verify that the canonical demo remains visible,
  and the complete browser run then passed.
- `.venv/bin/python -m compileall -q researchguard scripts tests`, `node --check` for
  the React smoke and legacy frontend script, and `.venv/bin/python -m pip check` passed.
  `git diff --check` passed.
- Dependency installation reported zero npm audit vulnerabilities. A later standalone
  `npm audit --omit=dev` could not reach the npm registry (`EAI_AGAIN`) and is recorded
  as an environmental network failure, not an audit pass.
- No real Supabase URL/key was present during the build. A build scan found no actual
  Google API key or Supabase project token. Public configuration variable names and
  strings shipped inside the official Supabase client are not credential values.

### Blockers and unverified assumptions

- The intended Supabase project, Free-plan state, project reference, publishable key,
  asymmetric signing-key configuration, Google client/provider settings, consent-screen
  test users and redirect allow lists were not available for inspection.
- Valid Google sign-in, Google cancellation, Supabase callback error, session restoration
  after a reload, automatic refresh, expiry in a real browser, account switching and
  valid remote sign-out remain **live-unverified**. Cancellation/failure parsing and
  token expiry are fixture-tested only.
- The live JWKS endpoint, its current key algorithm/rotation, the exact token claims from
  the user's project and a real FastAPI verification against that token remain
  unverified. The implementation intentionally reports JWKS access failure as an
  unavailable state and never falls back to decoding without verification.
- Supabase Auth session persistence uses browser storage through the official SDK. This
  local application does not establish protection for a hostile script or public
  multi-user deployment. No public deployment is authorized.
- Phase F authenticates transient live/model requests but does not implement private
  saved reviews because persistence was not part of this phase. Saved-review ownership
  and RLS must be implemented and separately verified in a later user-supplied phase.
- Phase E's Gemini API live verification remains independently blocked by its missing
  Free Tier/no-billing confirmation and server-side key.

### Manual action required

Follow `docs/AUTH_SETUP.md` using the actual **Supabase Free** project:

1. Configure an asymmetric ES256 or RS256 signing key and enable Google in Supabase.
   Store the Google client ID/secret only in the Supabase dashboard.
2. In Google Cloud, set the Authorized JavaScript origin to
   `http://127.0.0.1:5173` and the Google redirect URI to
   `https://<PROJECT_REF>.supabase.co/auth/v1/callback`.
3. In Supabase Auth URL Configuration, set the Site URL and exact allowed redirect to
   `http://127.0.0.1:5173/`.
4. Set backend `SUPABASE_URL`; set only frontend `VITE_SUPABASE_URL` and
   `VITE_SUPABASE_PUBLISHABLE_KEY` in `frontend/.env.local`. Do not share or commit the
   Google secret, Supabase secret/service-role key, JWT private key or Gemini key.
5. Start FastAPI and Vite with the commands in `docs/AUTH_SETUP.md`, then verify sign-in,
   reload restoration, authenticated live creation, sign-out, cancellation and callback
   failure in the browser.

Do not enable billing, buy credits, configure a public redirect or expose the local
server to complete this check. Phase F remains **BLOCKED** until that browser round trip
passes. No Phase G work has started.

### Phase F handoff placeholder follow-up

- Added a root `.env.example` for the backend's public Supabase URL, exact local CORS
  origins, auth timeout and existing Gemini/NCBI configuration names. Secret fields use
  inert replacement text; no real credential was added.
- Confirmed `frontend/.env.example` already contains the only two permitted browser
  values: `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`.
- Expanded `.gitignore` so `.env.local` and other `.env.*` files cannot be committed,
  while both reviewed `.env.example` templates remain eligible for source control.
- Added a later-deployment dashboard placeholder table to `docs/AUTH_SETUP.md`. It keeps
  Google's redirect to Supabase distinct from Supabase's redirect to the application.
  Public origins remain inactive until a later phase explicitly authorizes deployment
  and updates/tests the code allowlists.
- Phase G has not started because its concrete instructions have not yet been supplied.
