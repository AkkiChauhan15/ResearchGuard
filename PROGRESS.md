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

## 2026-09-19 — Migration Phase G: user-owned Supabase Postgres persistence

Status: **BLOCKED at remote migration and live two-user verification.** The application,
repository adapter, saved-review UI, versioned migration and fixture checks are complete.
The migration is **prepared, not applied**. No live Supabase database or authenticated
saved-review browser claim is made.

### Changes made

- Reread `context.md`, `PROGRESS.md`, `MIGRATION_PLAN.md`, `ARCHITECTURE.md`, repository
  code and applicable instructions before resuming Phase G. Updated context, architecture,
  migration plan, README and API documentation to reflect the actual Phase G boundary.
- Read current official Supabase database migration, RLS, API security/key, PostgREST
  and pgTAP guidance. The backend uses asynchronous HTTPX PostgREST requests with the
  verified user's bearer token plus the public `SUPABASE_PUBLISHABLE_KEY`. There is no
  service-role/secret key, privileged RLS bypass or client-supplied owner ID.
- Added `researchguard/persistence.py`. It lists, creates, loads, updates and deletes
  schema-versioned saved envelopes while preserving the unchanged canonical `Review`.
  Returned records are reparsed with Pydantic and the existing evidence/provenance
  validator before display or export. HTTP timeouts and connection limits are bounded.
- Added authenticated FastAPI routes under `/api/saved-reviews` for explicit save,
  list, open as a temporary working copy, optimistic update, canonical JSON/TXT export
  and revision-checked deletion. HTTP 409 preserves the local review on stale updates;
  unavailable persistence returns a clear 503. Saved operations never autosave ordinary
  edits. Development CORS now includes DELETE for the two exact local frontend origins.
- Changed the temporary store key to `(session_id, review_id)` so the same saved canonical
  review can be opened independently in different browser sessions while retaining user
  ownership checks, expiry, capacity bounds and per-entry locks.
- Added React signed-in states for private saved lists, empty/loading/error/unavailable
  states, explicit Save/Update, Open, JSON/TXT export and Delete. Opening creates a local
  copy; save/update failures and stale conflicts keep that copy. Logout clears private
  saved state while the public demo remains available.
- Added `supabase/migrations/202609190001_create_saved_reviews.sql`. It creates the
  owner UUID/canonical review envelope, schema version and revision; enables and forces
  RLS; removes anonymous privileges; gives authenticated users only required column
  grants; defines separate owner-only SELECT/INSERT/UPDATE/DELETE policies; derives
  ownership from `auth.uid()`; and prevents ownership/identity changes with both column
  permissions and a trigger. No Google profile table or profile fields were added.
- Added a prepared two-user pgTAP policy test under `supabase/tests/` and static migration
  contract tests. Added `docs/PERSISTENCE_SETUP.md` with CLI migration application,
  public environment values and exact two-account verification steps. Restored/updated
  both reviewed `.env.example` files; real values remain untracked.
- Preserved source records, passages, locations, access levels, retrieval hashes,
  demo/live labels, model runs and requested/returned model identifiers because the
  complete canonical record is stored. HTTP fixtures verify that original assessment
  suggestions and researcher-edited wording both survive saved export. Material claim
  edits still invalidate the current assessment, evidence links and approval before the
  explicit saved update.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **66/66 passed**, no skips.
  Saved-review HTTP/repository fixtures cover explicit create/list/open/update/export/
  delete, two distinct users, forged UUID/owner fields, every signed-out private action,
  stale revision conflict with the local copy retained, service unavailable states,
  canonical JSON equality, provenance/model preservation, and saved invalidation.
  Existing token, source transport/retrieval, evidence validation, Gemini provider,
  temporary isolation, request-size and export tests remained green.
- Migration contract test passed: four separate authenticated RLS policies, RLS enabled
  and forced, no anonymous grants, owner derived by default, immutable owner/identity,
  restricted update columns and revision field are present. The pgTAP SQL was inspected
  by the test suite but **not executed against PostgreSQL**.
- `npm run test:auth`, `npm run typecheck`, `npm run lint` and `npm run build` in
  `frontend/`: passed. Vite 8.3.0 built 62 modules; output was 0.64 kB HTML, 25.72 kB
  CSS and 476.30 kB JavaScript before gzip.
- Built-bundle secret scan found no Gemini API key, Supabase secret/service-role key,
  Google client secret or private key. One `sb_publishable_...` value and the project
  URL are present as expected public SPA configuration; they are not privileged secrets.
- `.venv/bin/python -m compileall -q researchguard scripts tests`,
  `.venv/bin/python -m pip check`, `node --check scripts/browser_smoke.cjs`, and
  `node --check web/app.js`: passed. `git diff --check`: passed before final progress
  documentation and is rerun in the final check.
- Headless Chrome against the rebuilt FastAPI-served React bundle passed the signed-out
  state, public demo/evidence/access, edited decision/export, failed API state, keyboard/
  mobile layout and no-page-error regression. The corrected legacy smoke also passed its
  public demo/export and signed-out live rejection. These runs do not exercise the
  authenticated saved-review UI.
- The first browser invocation lacked a root `playwright-core`; rerunning with the
  existing installation then required loopback/browser sandbox permission. A legacy
  smoke assertion also still expected pre-auth live access; it was updated to assert the
  current signed-out rejection and the final run passed. These were environment/stale
  test-harness issues, not claimed product passes.

### Prepared versus applied migrations

- **Prepared:** `202609190001_create_saved_reviews.sql` and
  `001_saved_reviews_rls.test.sql` are present and pass static contract inspection.
- **Applied:** none. The Supabase CLI is absent and no local Supabase database is
  running. Ignored local files contain frontend public Supabase configuration and a
  backend URL entry, but the backend publishable-key variable is absent and this app
  does not auto-load the root `.env`. No project database connection was made, and no
  remote table, policy, trigger or migration-history entry was inspected.

### Blockers and unverified assumptions

- A real Google OAuth round trip from Phase F remains unverified. Consequently real
  access-token forwarding, PostgREST acceptance, token refresh during saved operations,
  account switching and the authenticated saved-review browser journey are unverified.
- Two actual Supabase users have not tested RLS through the project API. Remote SELECT,
  INSERT, UPDATE and DELETE isolation; forged owner attempts; migration compatibility;
  paused-project behavior; quotas; and deletion in the actual project remain unverified.
- The prepared pgTAP test uses Supabase's documented community test-helper package, but
  that helper/local stack is not installed here. Static SQL assertions and backend fake
  repositories do not prove deployed PostgreSQL policy behavior.
- The public Supabase URL and publishable key are intentionally compiled into the SPA;
  this does not establish that Google provider settings or the database migration are
  correct. No database, Google or Gemini secret was built into the frontend. No account
  identity is added to the canonical review or sent to Gemini.

### Manual action required

1. Finish the Free-project Google Auth setup in `docs/AUTH_SETUP.md`; GitHub repository
   integration is not required for local Auth or database migrations.
2. Copy the project URL and current `sb_publishable_...` key into the backend shell and
   `frontend/.env.local` exactly as shown in `docs/PERSISTENCE_SETUP.md`. Do not provide
   or configure a service-role/secret key.
3. Install/use the Supabase CLI, run `supabase init`, `supabase login`, `supabase link`,
   inspect `supabase migration list`, then run `supabase db push` from this repository.
   Confirm migration `202609190001` appears applied. Do not create the remote table by
   hand because that bypasses migration history.
4. Use two test Google accounts and complete the owner isolation, stale update, saved
   invalidation, export and deletion checklist in `docs/PERSISTENCE_SETUP.md` with only
   public/synthetic content.

Do not enable billing, add a privileged backend key, connect a public deployment, or
begin Phase H to complete this gate. Phase G remains **BLOCKED** until the migration is
applied and the real two-user checks pass. Stop after Phase G.

## 2026-09-19 — Migration Phase H: end-to-end verification and competition demonstration

Status: **BLOCKED for the complete Google → Gemini browser journey.** All independent
local work is complete. The public demonstration, current supported-source retrieval,
backend/frontend regressions, local PostgreSQL RLS and real local Supabase token/
PostgREST persistence paths passed. Google OAuth and Gemini remain external blockers;
no substitute result, billing, paid fallback or deployment was used.

### Changes made

- Reread `context.md`, this progress log, `MIGRATION_PLAN.md`, architecture/code/tests
  and repository state before Phase H and after resuming it. Updated the current records
  to replace stale Phase G claims with verified migration and local database status.
- Started the repository's local Supabase stack. Migration
  `202609190001_create_saved_reviews.sql` applied locally. Replaced the RLS test's
  unavailable community helper with standalone pgTAP setup and two transaction-scoped
  `auth.users` fixtures. The test now covers forced RLS, anonymous denial, owner derivation,
  owner-column restrictions, forged ownership, cross-user read/update/delete, own CRUD
  and revision increments.
- Added `scripts/verify_supabase_local.py`. It obtains local public configuration without
  printing it, creates two disposable local Auth identities, verifies their real ES256
  access tokens through FastAPI/JWKS, exercises PostgREST with RLS, and prints no keys,
  passwords, tokens, account IDs or review bodies. This test is explicitly not Google OAuth.
- Updated `scripts/evaluate.py` with split/case IDs and actual selected denominators.
  Live evaluation now defaults to bounded two-case batches through `--max-cases 2`.
  It still never rewrites references or calls a model unless `--run-model` is explicit.
- Updated the React browser smoke so competition screenshots and the actual downloaded
  canonical JSON can be retained under a caller-selected directory. The output records
  a capture timestamp and explicitly states that the reconstructed demo made no model call.
- Added `scripts/capture_autophagy_case.py` and generated a bounded public autophagy
  artifact. It retains reconstructed input, the browser researcher edit, source IDs,
  URLs, access levels, timestamps, versions, hashes, exact selected passages, and a null
  model output with zero attempted calls. Fresh retrieval is kept separate from archived
  curated demo content.
- Added `docs/EVALUATION_PHASE_H.md`, `docs/COMPETITION_WALKTHROUGH.md`, and
  `docs/FEATURE_VERIFICATION.md`. Updated README, architecture, migration and persistence
  setup records with exact startup/test commands, actual denominators and live-versus-
  fixture/demo/blocked labels.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **66/66 passed**, no skips.
  This includes exact source-ID/quotation/location checks, claim-edit invalidation,
  partial results, unsafe URL/DNS/redirect/size/timeout controls, provider failures,
  token validation, session/user isolation, saved invalidation, canonical exports and
  stale revisions.
- `npm run test:auth --prefix frontend`: **1/1 passed**.
  `npm run typecheck`, `npm run lint` and `npm run build`: passed. Vite 8.3.0 built
  62 modules; output was 0.64 kB HTML, 25.72 kB CSS and 476.30 kB JavaScript before gzip.
- `.venv/bin/python -m compileall -q researchguard scripts tests`,
  `.venv/bin/python -m pip check`, and Node syntax checks: passed.
- `supabase test db`: initial run exposed a wrong planned count after the standalone
  conversion; after changing 14 to the actual 16, **16/16 pgTAP checks passed**.
- `.venv/bin/python -m scripts.verify_supabase_local`: after correcting the synthetic
  fixture field from `organism` to canonical `organism_model`, passed with **2 real local
  access tokens**. Public demo, signed-out live rejection, tampered token, forged owner,
  cross-owner read/export/delete, owner list/open/update/export/delete, stale update and
  canonical saved export all behaved as required.
- Supabase CLI migration history showed local and linked remote version `202609190001`.
  The hosted JWKS endpoint returned JSON and an anonymous REST read returned HTTP 401.
  This establishes applied migration history and anonymous denial, not hosted user isolation.
- `.venv/bin/python -m scripts.verify_retrieval_live`: passed. PubMed returned three
  individual abstract records (PMIDs 17611390, 27818143, 29909716). PMID 25484088
  resolved to PMC4502790 as abstract access. PMC8270360 returned 39 passages including
  35 body passages. PMC4502790 returned one abstract passage and no body; its full-text
  OAI request returned HTTP 400. The Enzo page returned 160 bounded blocks with visible
  May 29, 2024 version, and the manual returned 22 physical-page extracts with its HTTP
  Last-Modified value. Hashes are retained in the case artifact/evaluation report.
- Public React browser journey against an isolated FastAPI-served build: passed signed-
  out/empty state, demonstration label, observation/inference, evidence and access labels,
  edited decision/notes, canonical JSON download, failed API state, skip-link/form focus,
  390 px readable layout/no overflow and zero page errors. Three actual screenshots,
  browser metadata and export are under `artifacts/competition-demo/`.
- Fixture evaluation: **16/16 consistent**, separated as 10/10 development and 6/6
  held-out. Gemini attempted 0/16 and completed 0/16. Knowledgeable human review is
  0/16. Scientific support, context matching, false alarms and uncertainty performance
  remain unmeasured; no accuracy or time-saving percentage is reported.
- `.venv/bin/python -m scripts.verify_gemini_live`: **blocked before any call** with
  `unavailable_missing_credentials`; `live_calls_attempted` was 0 and no demo result was
  substituted.
- The temporary local Supabase stack was stopped after verification with its local state
  preserved; no unrelated containers were changed.

### Concrete failures resolved

1. The prepared RLS test depended on an uninstalled helper. It is now standalone and
   passed against actual local PostgreSQL.
2. The first revised pgTAP run planned 14 tests but emitted 16. The plan was corrected;
   all 16 passed.
3. The first local integration fixture used a nonexistent `organism` field. It now uses
   canonical `organism_model`; the complete run passed.
4. Autophagy artifact passage selection initially assumed phrases absent from current
   extracts and did not normalize PDF layout whitespace. It now selects only exact phrases
   inspected in the current sources while preserving original passage text.

### Blockers and unverified assumptions

- Google sign-in, cancellation, callback failure, session restoration/refresh, account
  switching and sign-out have not completed a real hosted browser round trip. Therefore
  the requested browser journey cannot pass as a whole.
- No Gemini key or operator confirmation of a no-billing AI Studio Free Tier project is
  present. Live extraction, assessment, returned model ID, live prompt-injection behavior,
  and real quota exhaustion are unverified. The requested autophagy model output is null.
- Hosted authenticated RLS behavior with two Google accounts is unverified even though
  local real-token/RLS checks passed and the linked migration is applied.
- Structural citation validation passed, but meaningful scientific entailment is not
  established by string matching. The curated autophagy reasoning is demonstration-only,
  and all 16 reference assessments still await a knowledgeable human reviewer.
- Browser checks cover keyboard focus and a 390 px layout, not a comprehensive WCAG or
  assistive-technology audit.

### Manual action required

1. In Supabase and Google Cloud, complete `docs/AUTH_SETUP.md` for
   `http://127.0.0.1:5173/`, then perform the real Google sign-in/cancel/reload/sign-out
   and two-Google-user saved-review checklist. Do not add a service-role/secret key.
2. In Google AI Studio, verify the project is Free Tier with no linked billing and that
   `gemini-3.8-flash` is available. Put `GEMINI_API_KEY` only in the backend environment,
   set `GEMINI_FREE_TIER_CONFIRMED=true`, run the two-call live verifier, then run the
   development evaluation in batches of at most two. Do not enable billing if unavailable.
3. Have a knowledgeable researcher review and date the 16 draft references before any
   scientific accuracy report. Freeze development decisions before model-running held-out cases.

### Phase outcome

**BLOCKED.** The local application is ready for a competition demonstration of the
clearly labeled curated workflow. It is not ready to claim a complete live Google +
Gemini + hosted-save journey or measured scientific performance. Stop after Phase H.

## 2026-09-19 — Gemini credential verification follow-up

Status: **KEY AND MODEL ACCESS VERIFIED; GENERATION BLOCKED BY PROVIDER HTTP 503.**

### Changes made

- Confirmed without printing the value that `GEMINI_API_KEY`, the operator Free Tier
  attestation and both `gemini-3.8-flash` model identifiers are present in the ignored
  root `.env`. Confirmed `.env` is ignored by git and changed its permissions from 0644
  to 0600.
- Added `researchguard/local_env.py`. The loopback server, Gemini live verifier and
  evaluation CLI now load the ignored root `.env` without shell evaluation. Existing
  process variables retain priority so deployment/test launchers remain authoritative.
- The first live call reached Google but failed HTTP 400 because the SDK's older
  `response_schema` conversion sent strict Pydantic `additionalProperties` fields through
  an incompatible OpenAPI schema path. Changed the adapter to the official
  `response_json_schema` field using `model_json_schema()` and explicitly disabled
  automatic function calling. Application-side Pydantic and evidence validation remain.
- Split HTTP 400 request/schema failures from 401/403 authentication failures. Updated
  the live verifier to return structured blocked JSON for provider failures rather than
  a traceback. No model/provider fallback was added.
- Updated README, context and Phase H verification records with the current live status.

### Checks actually executed

- Current official Gemini documentation confirms `gemini-3.8-flash` is the stable model
  code, supports structured output, and is listed with Free Tier input/output. This does
  not independently inspect the user's billing state.
- Non-generative `client.models.get('gemini-3.8-flash')`: **passed**. The configured key
  is accepted and the model is visible to the project.
- Original bounded structured-output request: reached Google and returned HTTP 400 with
  `additional_properties` rejected under `generation_config.response_schema`.
- Repaired `response_json_schema` diagnostic: schema was accepted and generation reached
  the model, then returned HTTP 503 high demand.
- Two complete verifier attempts after the repair: both stopped during extraction after
  the adapter's bounded 5xx retries with HTTP 503/high demand. Assessment was not started,
  no output was produced, and no paid or demonstration fallback was used.
- Temporary loopback server on port 8011 loaded `.env`; `/api/config` reported
  `model_configured=true`, provider `gemini`, and both models `gemini-3.8-flash`.
- Targeted provider/environment tests: **17/17 passed** before the final regression run.
- Full regression after all fixes: **68/68 passed**, no skips. Compileall, dependency
  check and `git diff --check` passed. The live verifier's failure path was separately
  checked to emit structured blocked JSON without a traceback.
- Secret hygiene check passed: the ignored `.env` is mode 0600, and no credential-shaped
  values were found in `frontend/dist` or competition artifacts.

### Remaining action

Retry `.venv/bin/python -m scripts.verify_gemini_live` later. A passing gate requires
both the synthetic extraction and evidence assessment plus deterministic validation.
Do not switch models, enable billing, or add a fallback to work around HTTP 503.

## 2026-09-19 — Free deployment preparation follow-up

Status: **READY FOR MANUAL DEPLOYMENT; HOSTED JOURNEY UNVERIFIED.** No public service,
billing method, paid plan, domain, OAuth setting, or external account was changed by
the agent.

### Changes made

- Rechecked `context.md`, current progress, architecture, migration records, code,
  tests and the Git remote before making deployment claims.
- Selected Vercel Hobby for the static Vite SPA, one Render Free web service for
  FastAPI, and the existing Supabase Free project. FastAPI was not moved to Vercel
  Functions because draft records, locks and source throttling are process-local.
- Added exact hosted HTTPS origin validation, exact trusted-host validation, automatic
  use of Render's `RENDER_EXTERNAL_HOSTNAME`, and a targeted CORS/security correction
  so an explicitly allowed Vercel origin is not rejected only because the browser marks
  the request `Sec-Fetch-Site: cross-site`. Wildcards remain rejected.
- Added `VITE_API_BASE_URL` for the exact Render origin and
  `VITE_APPLICATION_ORIGIN` for the exact hosted OAuth return origin. Local Vite proxy
  behavior remains the default when these are absent. Gemini and other secrets remain
  unavailable to frontend code.
- Pinned Render's Python runtime to 3.14.3 in `.python-version` and documented the exact
  single-worker Uvicorn start command, health check, dashboard fields, public variables,
  secret placement, Supabase/Google redirects, and hosted verification sequence in
  `docs/DEPLOYMENT.md`.
- Updated context, architecture, migration, Auth setup, examples and README to reflect
  the newly authorized free-tier deployment preparation without claiming deployment.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **70/70 passed**, no skips.
  New checks cover an explicit hosted Vercel origin with a cross-site browser request,
  automatic exact Render host acceptance, and rejection of wildcard/URL host entries.
  Existing auth, RLS repository, session isolation, limits, invalidation, retrieval,
  evidence validation, provider failure and export checks remained green.
- `npm run test:auth`: **1 test file passed**. It now covers exact hosted OAuth origin
  acceptance, an unlisted preview-origin rejection and malformed hosted-origin rejection.
- `npm run typecheck` and `npm run lint`: passed.
- Hosted-style `npm run build` with synthetic public Render/Vercel origins: passed.
  Vite 8.3.0 built 62 modules; output was 0.64 kB HTML, 25.72 kB CSS and 477.04 kB
  JavaScript before gzip.
- The hosted-style bundle contained both synthetic public origins and no Gemini-key,
  Google-client-secret or Supabase-secret-shaped credential. The first broad marker
  scan correctly found the literal `sb_secret_` rejection string; the credential-shaped
  scan distinguished that guard from a key and passed.
- `.venv/bin/python -m compileall -q researchguard tests` and
  `.venv/bin/python -m pip check`: passed. `git diff --check` passed.
- The exact single-worker hosted Uvicorn form started on `0.0.0.0:8077` with a synthetic
  Render hostname. A loopback health request carrying that exact Host, the allowed
  Vercel Origin and `Sec-Fetch-Site: cross-site` returned HTTP 200 and canonical health
  JSON. Two earlier sandboxed bind attempts were unavailable; the permitted rerun passed
  and was shut down. A normal local frontend build was restored afterward and passed.

### Blockers and unverified assumptions

- Render and Vercel were not connected or deployed, so build logs, cold-start behavior,
  real CORS headers through their proxies, service health and quota behavior are unverified.
- Hosted Google OAuth, session restoration/sign-out, hosted two-user RLS isolation and
  the complete saved-review browser journey remain unverified.
- Gemini key/model metadata access is verified, but generation still has no successful
  live output after repeated provider HTTP 503 high-demand responses.
- Render Free sleeps after inactivity and has ephemeral process/filesystem state. Every
  unsaved draft can disappear on sleep, restart or redeploy; explicit Supabase saves are
  the durable path. Vercel Hobby is limited to personal, non-commercial use.
- The native Render runtime might not include the optional `pdftotext` binary. If absent,
  live ENZ-51031 manual parsing reports an explicit unavailable state; the archived demo
  and Enzo product-page retrieval do not depend on that binary.

### Manual action required

Follow `docs/DEPLOYMENT.md` in order: push a reviewed revision, create the Render Free
backend, create the Vercel Hobby frontend, add the exact Vercel origin to Render, update
Supabase URL Configuration and the Google OAuth client, then run the signed-out and
two-account hosted checklists. Do not commit `.env`, add a service-role key, put the
Gemini/Google secret in Vercel, enable billing, or use wildcard redirects/origins.

## 2026-09-19 — Login, signup, recovery and optional-profile pages

Status: **IMPLEMENTATION PASS; LIVE AUTH/EMAIL/PROFILE INTEGRATION BLOCKED.** Existing
research-review behavior was preserved. No deployment, paid mail service, billing
change, credential change or external account mutation was performed.

### Existing implementation verified and reused

- The primary frontend remains React 19 + TypeScript + Tailwind through Vite. The
  existing Supabase JS singleton, implicit Google OAuth flow, persistent session and
  automatic refresh were extended rather than replaced.
- The existing OAuth destination remains the exact application root: Google returns to
  Supabase `/auth/v1/callback`, then Supabase returns to the SPA. FastAPI's asymmetric
  JWT signature/issuer/expiry/audience/role/subject verification remains authoritative
  for live and private API routes.
- Existing server-owned review decisions, transient session/user isolation, explicit
  saved-review persistence, evidence invalidation, retrieval, model, validation and
  export services were not rewritten. The public demonstration still requires no login.
- No suitable profile table existed. The existing `saved_reviews` table remains solely
  for canonical review records; profile data was not added to it.

### Changes made

- Added responsive SPA pages at `/login`, `/signup`, `/forgot-password`,
  `/update-password`, and `/account`, plus exact FastAPI SPA routes and Vercel rewrites.
  The pages use the existing visual language, labeled fields, autocomplete, show/hide
  controls, loading/error states, keyboard-sized controls, Google branding and a public
  demonstration link.
- Reused the existing Google provider from both login and signup. Added email/password
  sign-in, registration, confirmation-aware status, neutral recovery requests and
  recovery-session password updates through the same Supabase client. The application
  reads Supabase's public Auth settings and hides email controls when that method or
  signup is disabled/unavailable.
- Added safe internal return paths and a session-scoped pending OAuth return. External,
  scheme-relative, backslash and fragment redirects fall back to `/`. A new browser
  session is accepted only after `/api/auth/me` verifies it; a rejected token is cleared
  locally instead of leaving a partial signed-in state.
- Session restore, expiry refresh, `PASSWORD_RECOVERY`, OAuth cancellation/failure,
  sign-out and already-signed-in redirects are handled in the SPA. Invalid or expired
  confirmation/sign-in callbacks show a recoverable generic error without exposing
  account existence.
- Added an optional account profile for full name, research role, research field and
  institution. Google metadata may prefill the editable name. Every field is optional;
  no email, phone, date of birth, lab/project data or payment data is copied. Profile
  data is not used by review/Gemini requests.
- Prepared `supabase/migrations/202609190002_create_researcher_profiles.sql` and a
  12-assertion pgTAP file. The table derives its primary-key owner from `auth.uid()`,
  grants authenticated users only the four optional data columns, forces RLS and has
  owner-only SELECT/INSERT/UPDATE policies plus immutable owner/creation fields. The UI
  upserts one owner row safely and never sends `user_id`.
- Updated Auth, persistence, deployment, API and README setup documents. No privacy or
  terms page exists, so no policy link or compliance statement was invented.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **71/71 passed**, no skips.
  New coverage verifies all account SPA paths return the built entry and statically
  checks the optional-table fields, forced RLS, owner policies, column grants, immutable
  owner and absence of email. Existing token, unauthenticated private-route, two-owner
  saved-review, invalidation, evidence, retrieval, model and export tests remain green.
- `npm run typecheck`, `npm run lint`, `npm run test:auth`, and `npm run build` in
  `frontend/`: passed. The auth test file covers five redirect/callback groups. Vite
  8.3.0 built 64 modules: 0.64 kB HTML, 28.08 kB CSS and 498.84 kB JavaScript before
  gzip.
- Headless Chrome against the actual FastAPI-served production build passed: login,
  signup and recovery rendering; rejection of a password update without the dedicated
  recovery event/session; enabled email controls from a mocked settings response;
  accessible password-mismatch alert; public demo navigation; evidence/access labels;
  edited decision and canonical JSON export; failed-API retention; keyboard focus;
  390 px no-overflow layout; and zero page errors. This did not submit credentials,
  send email or leave the application for Google.
- The project's live public Auth settings endpoint returned HTTP 200 and reported
  Google enabled, email enabled, signup enabled and email auto-confirm disabled. This
  confirms the controls should be visible and confirmation required; it does not prove
  OAuth, email delivery or the exact dashboard password policy.
- A built-bundle scan found no configured server credential value, Gemini-key shape,
  Supabase secret-key shape or JWT shape. Compileall, `pip check`, browser-script syntax
  and `git diff --check` passed.
- The temporary FastAPI browser-test process and only the `ResearchGuardAI` local
  Supabase containers were stopped afterward. Unrelated containers were not changed.

### Prepared versus applied migrations

- `202609190001_create_saved_reviews.sql`: previously verified in linked hosted and
  local migration history; unchanged.
- `202609190002_create_researcher_profiles.sql`: **prepared, not applied locally or to
  the linked hosted project**. Its Python source-contract test passed. The new pgTAP
  assertions did not execute against PostgreSQL.

### Blockers and unverified assumptions

- A real Google browser round trip from both pages, cancellation, refresh restoration,
  sign-out and safe requested-page return remain unverified.
- Email registration, delivery, confirmation, duplicate-account response, recovery
  delivery, successful password update and expired-link behavior remain unverified.
  The public settings endpoint does not reveal the exact configured password minimum;
  the checked-in local default is 6 and must be matched to the dashboard before build.
- Supabase's default sender may restrict recipients or rate-limit delivery. No custom
  SMTP service was configured. A paid service is not authorized.
- Optional-profile insert/upsert, blank fields, repeated save and two-user RLS isolation
  remain unverified until migration `202609190002` is applied and its pgTAP/live checks
  run. Until then `/account` reports profile storage unavailable without affecting the
  authenticated workspace or local review.
- Automated browser tests verify UI behavior only. They do not establish the external
  Google/email flows or a comprehensive accessibility audit.

### Manual action required

1. Apply only the pending profile migration through the linked CLI workflow:
   `supabase migration list`, `supabase db push`, then `supabase migration list`. The
   final list must include both `202609190001` and `202609190002`.
2. In Supabase Authentication → URL Configuration, keep the exact application root and
   add exact `/account` and `/update-password` redirect URLs for the local or deployed
   origin in use. Do not add wildcards. Keep the existing Google client and its Supabase
   callback unchanged.
3. Check the dashboard password minimum and set
   `VITE_SUPABASE_PASSWORD_MIN_LENGTH` to that number before rebuilding. Confirm email
   provider, signup and email confirmation settings; the read-only public flags currently
   show all three enabled with confirmation required.
4. Run one disposable Google flow and one disposable email confirmation/recovery flow,
   then the two-user profile isolation checklist in `docs/PERSISTENCE_SETUP.md`. If the
   default mail sender cannot deliver, record it as blocked; do not enable billing or a
   paid SMTP provider.

The attempted local `supabase migration up --local` execution was rejected by the
automatic approval reviewer because its usage limit had been reached. The migration was
not applied through another route; this is why database execution remains blocked.

## 2026-09-19 — Deployed configuration audit

Status: **DEPLOYED FRONTEND VERIFIED; PUBLIC ACCESS AND HOSTED JOURNEY NEED CONFIGURATION.**

- The user reported the project deployed. Public GitHub deployment metadata shows a
  successful Vercel Production deployment of current commit
  `1ce8ae318a3bf5fec2223644b3b1289687f544ca`.
- A direct request to the generated Vercel deployment URL returned HTTP 302 to
  `vercel.com/sso-api`. It is protected by Vercel Authentication and is not currently a
  public competition URL. The stable Production Domain was not present in the repository.
- `supabase migration list` connected to the linked hosted database and confirmed both
  `202609190001` and `202609190002` are applied remotely. Do not push either migration
  again. Hosted two-user profile/RLS behavior is still unverified.
- The Render URL and Vercel/Render dashboard environment values are not available in the
  repository. Render health, production CORS, Gemini generation and the complete hosted
  browser journey therefore remain unverified.
- No dashboard setting, environment value, deployment or billing configuration was
  changed during this audit.

## 2026-09-20 — Authenticated multi-provider AI chat

Status: **IMPLEMENTATION PASS; LIVE PROVIDER GENERATION BLOCKED.**

### Changes made

- Added the existing-SPA `/chat` route and header navigation. The responsive React UI
  has provider/model selectors, per-provider availability, bounded multi-turn history,
  separate user/assistant messages, loading/error states, Enter/Shift+Enter behavior,
  auto-scroll, clear chat, and optional fallback. Every response shows the actual
  provider/model and is labeled `not evidence-checked`.
- Kept chat separate from canonical reviews, saved records, evidence, decisions and
  exports. Chat requires the existing verified Supabase session; its history remains
  only in React memory and account identity is never sent to a model provider.
- Added authenticated `GET /api/chat/providers` and `POST /api/chat`. FastAPI validates
  provider/model allowlists, 1–24 messages, 4,000 characters per message and 24,000
  total characters. It uses the bounded external pool, fixed destinations, safe errors,
  a per-user six-request rolling-minute limit, 45-second total/20-second provider
  deadlines, streamed 64 KB response bounds and at most 1,024 output tokens.
- Added the `ChatProvider` boundary with distinct Groq, OpenRouter, Gemini and NVIDIA
  adapters. The versioned `researchguard/chat/models.json` keeps model labels/IDs easy
  to update. No frontend/API request can submit an arbitrary provider URL.
- Added free-only gates. Groq, Gemini and NVIDIA require a key plus operator
  free/no-billing confirmation; OpenRouter allows only `openrouter/free`. Fallback is
  disabled by default, requires an explicit user checkbox when enabled by the server,
  skips unconfigured providers and reports every attempted status plus the actual
  provider/model. There is no paid or silent fallback.
- Added `.env.example` placeholders, `docs/CHAT_SETUP.md`, API/deployment/README
  instructions, a bounded live-check CLI, a Vercel `/chat` rewrite, and the explicit
  scope/architecture decision. No dependency was added.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **83/83 passed** after all
  changes, including 12 chat HTTP/provider/rate-limit tests and the preserved review,
  retrieval, authentication and persistence checks.
- `npm run typecheck`, `npm run lint`, `npm run test:auth`, and `npm run build`:
  passed. Vite built 65 modules; the existing non-failing chunk-size advisory remains.
- `scripts/browser_chat_smoke.cjs` in headless Chrome: passed the signed-in `/chat`
  journey with provider/model selection, two-turn context, normalized metadata, failed
  request retention and exclusion from later model context, clear action and no
  horizontal overflow at 390 px.
- Existing `scripts/browser_react_smoke.cjs` against the FastAPI-served production
  build: passed the account UI, public demo, evidence/access, edit/decision/export,
  failed API, keyboard and mobile regression journey with no page errors.
- Python compileall, `pip check`, both browser-script syntax checks and
  `git diff --check`: passed. A targeted production-bundle scan found no configured
  provider-key value, provider secret-key shape, Supabase secret key, or JWT.
- Provider status from the actual ignored local environment: Gemini configured;
  Groq, OpenRouter and NVIDIA missing keys; fallback disabled. No secret value printed.
- One bounded live Gemini chat check using public synthetic input returned
  `Google Gemini is temporarily unavailable. Retry later.` No response was produced,
  no fallback ran, and no billing was enabled.
- `.venv/bin/python -m scripts.evaluate`: **16/16 fixture-consistency checks** across
  10 development and 6 held-out definitions; **0 model cases run** and scientific
  performance remains unmeasured.

### Blockers and unverified assumptions

- No provider has completed a live chat response in this implementation check. Gemini
  is configured but temporarily unavailable. Groq, OpenRouter and NVIDIA cannot be
  live-tested until their server-only free-access keys are supplied; their account
  tier/billing state is not inferable from code.
- Provider fixture tests establish request/response mapping and failure handling, not
  current external model availability, answer quality or scientific accuracy.
- The deployed Vercel/Render services do not contain these uncommitted changes yet.
  Hosted `/chat`, hosted sign-in, Render keys/CORS and browser network secrecy remain
  unverified until a reviewed commit is deployed and the manual journey passes.
- Conversation rate limiting is process-local, matching the current one-worker Render
  architecture. It is not a distributed production abuse-control system.

### Manual action required

1. Review, commit and push this revision so Vercel and Render rebuild it.
2. Add only the desired provider keys to Render using `docs/CHAT_SETUP.md`. Keep keys
   out of Vercel and all `VITE_` variables. Set a free-tier confirmation true only
   after checking that exact account has no billing. Do not purchase credits.
3. Keep fallback false for the first hosted provider check. Sign in at `/chat`, send
   one public/synthetic question and follow-up, inspect the Network response for actual
   provider/model metadata and absence of keys, then enable fallback only if every
   candidate is independently confirmed free/no-billing.

## 2026-09-20 — Stitch visual design integration

Status: **PASS LOCALLY; DEPLOYMENT UPDATE NOT YET VERIFIED.**

### Changes made

- Applied the supplied `stitch_research_guard_bioplatform` visual direction to the
  existing React application instead of replacing its working flows. Evidence review,
  AI chat, sign-in/create-account/recovery, account settings and saved-review controls
  now share deep teal surfaces, emerald actions, editorial headings, monospaced
  provenance labels, compact workflow navigation and responsive glass panels.
- Added a reusable molecular shield brand mark and lockup in `frontend/src/Brand.tsx`,
  updated the favicon and browser theme color, and kept all supplied Stitch source files
  unchanged as design references.
- Preserved the existing route names, accessible labels, FastAPI contracts, canonical
  review state, public-demo distinction, evidence/access labels, researcher decisions,
  exports, Supabase account behavior and server-only model credentials.
- Did not copy unverified claims from the mockups. The application does not claim
  HIPAA/FDA compliance, cryptographic ledgers, provider health, or product capabilities
  that are absent from the verified implementation.

### Checks actually executed

- `npm run typecheck`, `npm run lint`, `npm run test:auth`, and `npm run build`: passed.
  Vite built 66 modules; its existing non-failing bundle-size advisory remains.
- Existing `scripts/browser_react_smoke.cjs`: passed the login/signup/recovery controls,
  public demo, evidence/access display, edited decision/export, failed request state,
  keyboard route and 390 px responsive journey with no page errors.
- Existing `scripts/browser_chat_smoke.cjs`: passed the signed-in chat, provider/model
  selection, multi-turn context, failure retention, clear action and 390 px layout.
- Focused Chrome design check: `/login` rendered at desktop and 390 px without horizontal
  overflow; the signed-out `/chat` state rendered without page errors.
- `.venv/bin/python -m unittest discover -s tests -v`: **83/83 passed**, confirming the
  preserved auth, chat, evidence validation, retrieval, HTTP and persistence behavior.
- Python compileall, `pip check`, production-bundle secret-pattern scan and
  `git diff --check`: passed. No provider key or privileged Supabase-key pattern was
  found in the built frontend.

### Remaining limitations and manual action

- This is a local source change. Commit and redeploy the frontend before describing the
  hosted application as redesigned; no Vercel or Render deployment was triggered here.
- Google-hosted Newsreader, Inter and JetBrains Mono fonts use the same public font URLs
  supplied by the Stitch export. The CSS retains system fallbacks if those files cannot
  load.
- Live Google OAuth, hosted persistence and live model generation retain their previously
  recorded verification status; a visual redesign does not resolve those external
  configuration or quota blockers.

## 2026-09-20 — Non-Gemini structured evidence providers

Status: **IMPLEMENTATION PASS; LIVE NON-GEMINI GENERATION UNVERIFIED LOCALLY.**

### Changes made

- Changed the structured extraction/assessment default from Gemini to Groq
  `openai/gpt-oss-20b`. Added explicit `openrouter` and `nvidia` selections while
  retaining Gemini only as an explicitly selected migration option. Legacy OpenAI
  selection remains disabled, and evidence requests never fall back to another model.
- Added fixed-endpoint Groq, OpenRouter and NVIDIA adapters with provider-specific
  structured-output payloads, server-only credentials, model allowlists, free/no-billing
  gates, bounded input/output/concurrency/timeouts, one bounded retry for transport or
  selected 5xx failures, immediate quota reporting, safe errors and Pydantic revalidation.
  Portable schemas preserve required fields, closed objects, enums and references;
  Pydantic remains authoritative for string and array length limits.
- Preserved the existing scientific prompts and deterministic extraction-span,
  source-ID, exact quotation, location and evidence-relationship validators. Routes,
  retrieval, canonical reviews, decisions, Supabase saves and exports were not rewritten.
- Added `provider` to `ModelRun` provenance with a backward-compatible
  `legacy_unspecified` default for older saved records. New reviews record the actual
  provider plus requested/returned model and prompt version.
- Added a generic two-call synthetic live verifier and retained the old Gemini-named
  script as a compatibility wrapper. Updated environment examples, deployment/API/chat
  instructions, architecture/context/migration records, feature status, legacy UI copy
  and the default chat selector. A non-Gemini selection no longer imports the Gemini SDK
  during provider initialization.
- Rechecked current official Groq strict structured-output/model/rate-limit contracts,
  OpenRouter structured-output and zero-price router behavior, and NVIDIA NIM
  `guided_json` behavior. Documentation confirms request formats, not access in the
  user's provider accounts.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **88/88 passed**. This includes
  request-shape and schema checks for all three added providers, malformed/quota/secret
  handling, default/allowlist/free-gate checks, and a FastAPI extraction route using a
  controlled Groq response. Existing review, retrieval, validation, authentication,
  ownership, invalidation and export tests stayed green.
- `npm run typecheck`, `npm run lint`, `npm run test:auth`, and `npm run build`: passed.
  The auth utility suite passed 1/1. Vite built 66 modules; the existing non-failing
  chunk-size advisory remains.
- Python compileall and syntax checks for the React smoke, chat smoke and legacy browser
  scripts passed. `.venv/bin/python -m scripts.evaluate` reported **16/16 fixture
  definitions consistent**, **0 live model cases attempted**, and **0/16 human-reviewed
  reference assessments**.
- The generic verifier was run with explicit Groq selection and no key. It exited 2 with
  `unavailable_missing_credentials` and `live_calls_attempted: 0`; no fallback or demo
  result was substituted.
- `git diff --check` passed. A value-based scan checked the one provider credential
  configured in the ignored local environment against all four production bundle files:
  **0 matches**. No credential value was printed.

### Blockers and unverified assumptions

- The ignored local environment has no Groq, OpenRouter or NVIDIA key. The user reports
  non-Gemini keys in the deployed chat configuration, but the Render environment is not
  accessible from this workspace. Therefore no non-Gemini structured extraction or
  assessment completed live, and no hosted redeploy or endpoint behavior is claimed.
- The free/no-billing confirmation flags are operator attestations. Code cannot inspect
  billing state. Groq/NVIDIA must stay unavailable until the user confirms that exact
  account; OpenRouter evidence use is restricted to `openrouter/free`.
- Provider fixtures validate contracts and deterministic rejection behavior, not model
  quality, scientific entailment or current provider availability. Browser automation
  was not rerun because `playwright-core` is absent from this workspace; the earlier
  Phase H/Stitch browser evidence remains historical and does not establish the new live
  provider call.

### Manual action required

1. In Render, set `LLM_PROVIDER=groq`, keep/add `GROQ_API_KEY`, set both Groq model
   variables to `openai/gpt-oss-20b`, and set `GROQ_FREE_TIER_CONFIRMED=true` only after
   confirming free access and no billing. Remove or override the old
   `LLM_PROVIDER=gemini` value. Do not put any provider key in Vercel or a `VITE_` value.
2. Commit/push this implementation and redeploy Render. Confirm `/api/config` reports
   provider `groq`, state `configured`, and the expected extraction/assessment models.
3. Sign in and use public/synthetic input for one **Extract claims with AI** call, then
   retrieve public evidence and run one assessment. Confirm the exported `model_runs`
   records provider `groq` and the returned model. If the provider returns 429 or an
   unavailable error, wait for free quota/service recovery; do not enable billing or a
   fallback.

## 2026-09-21 — Private saved AI chats and PDF export

Status: **IMPLEMENTATION PASS LOCALLY; HOSTED MIGRATION AND BROWSER JOURNEY PENDING.**

### Changes made

- Added a separate canonical saved-chat schema and asynchronous Supabase repository.
  Successful complete user/assistant turns now save automatically under the verified
  user's access token. Users can list, reopen, continue and delete their own chats.
  Evidence reviews and their explicit-save policy remain unchanged.
- Added `GET /api/chats`, `GET /api/chats/{chat_id}`,
  `GET /api/chats/{chat_id}/export.pdf` and revision-checked `DELETE`; `POST /api/chat`
  now returns the canonical saved record. Continuing requires the exact saved history
  plus one user message and the current revision, preventing stale or forged overwrites.
- Preserved actual assistant provider, returned model, fallback flag and timestamp per
  message. User identity is used only for verified ownership and is not sent to a model.
- Added server-side ReportLab PDF export from the canonical saved record. The PDF contains
  all messages and provenance, page numbers, and a clear warning that chat output is not
  evidence-checked or scientific evidence.
- Added the responsive **Saved chats** panel and **New chat**, **Export PDF** and
  **Delete** controls. Authentication identity changes remount the page so one user's
  local chat state cannot appear in another user's session.
- Added versioned migration `202609210001_create_saved_chats.sql` with forced RLS,
  owner-only SELECT/INSERT/UPDATE/DELETE policies, ownership derived from `auth.uid()`,
  restricted column grants, immutable identity/owner fields, revision increments and
  24-message/250,000-byte limits. Added 15 dedicated pgTAP assertions.
- Updated README feature documentation, API/chat/persistence/deployment instructions,
  architecture and context records. No provider, billing, public deployment or hosted
  database setting was changed.

### Checks actually executed

- `.venv/bin/python -m unittest discover -s tests -v`: **91/91 passed**. This includes
  authenticated chat creation/continuation/list/open/PDF/delete, cross-user and signed-out
  rejection, forged/stale history rejection, repository JWT/public-key behavior, migration
  contract checks, PDF framing, and all existing auth/review/retrieval/provider tests.
- `supabase migration up --local`: applied `202609190002` and `202609210001` to the
  disposable local stack. `supabase test db`: **43/43 passed** across saved reviews,
  optional profiles and saved chats. The first pgTAP attempt correctly failed because
  the restored local database had not yet applied those two migrations; the rerun after
  local migration application passed completely.
- `npm run typecheck --prefix frontend`, `npm run lint --prefix frontend`,
  `npm run test:auth --prefix frontend` and `npm run build --prefix frontend`: passed.
  Vite built 66 modules; its existing non-failing bundle-size advisory remains.
- Python compileall, `pip check`, browser-script JavaScript syntax checks,
  `git diff --check`, and a production-bundle credential-pattern scan passed. No Gemini,
  Groq, NVIDIA, OpenRouter or privileged Supabase credential pattern was found in the
  built frontend.
- The updated browser smoke was syntax-checked but not executed because
  `playwright-core` is unavailable in this workspace. No browser or hosted round-trip is
  claimed from fixture/HTTP tests.

### Blockers and unverified assumptions

- Hosted migration `202609210001` is prepared and locally executed, but it has not been
  pushed to or confirmed in hosted Supabase migration history. Deployed chat persistence
  will return an explicit unavailable error until that table exists.
- The real hosted journey—sign in, send, reload/reopen, continue, PDF download, delete,
  sign out, and cross-account isolation—remains unverified. Browser automation could not
  run locally because its existing Playwright dependency is absent.
- The tests use controlled provider replies. They establish persistence/export behavior,
  not current external model availability or answer quality. Existing live-provider
  limitations remain unchanged.
- ReportLab 5.0.1 is installed and passed local PDF generation tests. Render must install
  the updated requirements during redeployment.

### Manual action required

1. Review, commit and push these files. In the linked Supabase project run
   `supabase migration list`, `supabase db push`, then `supabase migration list`; confirm
   `202609210001` appears remotely. Do not create the table manually or add a service-role
   key.
2. Redeploy Render so it installs `reportlab==5.0.1` and serves the new API, then redeploy
   Vercel for the new chat UI. No new environment variable is required; keep the existing
   Supabase URL/publishable key and provider secrets in their current server/public
   boundaries.
3. With two test users and public/synthetic prompts, run the hosted sequence documented
   in `docs/PERSISTENCE_SETUP.md`: save/reload/continue/export/delete as user A; verify
   user B and signed-out requests cannot access user A's chat; verify a stale revision
   returns HTTP 409.

## 2026-09-21 — Saved-chat follow-up RLS repair

Status: **FIXED AND VERIFIED AGAINST LOCAL SUPABASE; HOSTED REDEPLOY PENDING.**

### Cause and repair

- Reproduced the reported error through real local Supabase Auth, PostgREST and RLS:
  initial chat creation returned HTTP 201, while the first continuation PATCH returned
  HTTP 403 `permission denied for table saved_chats`.
- The repository reused its insert body for updates, so it sent `schema_version` even
  though the value was unchanged. The migration correctly makes that identity field
  immutable and excludes it from the authenticated UPDATE column grant. PostgreSQL
  therefore rejected the request before any model-specific behavior.
- Changed saved-chat continuation to PATCH only `title`, `message_count`,
  `last_provider`, `last_model` and `record`. Ownership, schema version, revision and
  timestamps remain server/database authoritative. No RLS policy was weakened and no
  new migration, privileged key or model-specific workaround was added.
- Extended `scripts.verify_supabase_local` with a real saved-chat create, follow-up,
  cross-owner denial and delete sequence, and added a unit regression asserting that
  immutable columns can never re-enter the PATCH body.

### Checks actually executed

- Direct disposable PostgREST reproduction after the patch: create **201**, follow-up
  update **200**, revision advanced from 1 to 2.
- `.venv/bin/python -m scripts.verify_supabase_local`: **passed** with two real local
  access tokens, including saved-chat create/follow-up/delete and cross-owner rejection.
- `.venv/bin/python -m unittest discover -s tests -v`: **92/92 passed**.
- Python compileall, `pip check`, and `git diff --check`: passed.

### Remaining action

- Redeploy the FastAPI/Render backend containing this code change. The frontend and
  database migration do not need a new setting for this repair. After Render finishes,
  reopen an existing saved chat and send a follow-up with each enabled provider; the
  common persistence PATCH should now succeed. Hosted behavior is not claimed until
  that redeploy and browser check complete.

## 2026-09-22 — Phase I: dedicated application routes

Status: **PASS LOCALLY. PHASE II AND PHASE III NOT STARTED.**

### Changes made

- Split the React interface into dedicated client routes while retaining the existing
  history-based router: marketing-only `/`, disclosures at `/about`, a signed-in hub at
  `/dashboard` (with `/reviews` as the same saved-record view), the input at
  `/review/new`, active workspaces at `/review/{review_id}`, the public demonstration at
  `/demo/cyto-id`, and the existing `/chat` and account routes.
- Added a shared responsive header. Signed-in navigation is Home, Dashboard, New review,
  AI chat with its `unchecked` badge, and About, followed by Account and Sign out.
  Signed-out navigation is Home, About and Demo with Sign in. Authentication restoration
  and ordinary sign-in now default to `/dashboard`; explicit safe `next` paths remain
  authoritative.
- Restricted `WorkflowStrip` rendering to new-review, active-review and demonstration
  workspaces. The home page contains only the marketing hero and the Start review/Open
  demo actions. The chat page no longer renders review workflow chrome.
- Reused the canonical review, saved-review and saved-chat services. No API review
  schema, database schema, migration, storage bound, expiry, ownership rule, save policy,
  evidence behavior, model adapter or export contract changed. Review saves remain
  explicit; successful chat turns retain their separately authorized autosave policy.
- Added FastAPI SPA fallbacks and Vercel rewrites for every new route. Extended the HTTP
  and browser smoke checks and updated README, API documentation, feature verification
  and project context. The hosted deployment was not changed or checked.

### Checks actually executed

Required backend suite:

```text
$ .venv/bin/python -m unittest discover -s tests -v
----------------------------------------------------------------------
Ran 92 tests in 2.139s

OK
```

The suite includes the extended static-route contract for `/about`, `/dashboard`,
`/reviews`, `/review/new`, `/review/{id}`, `/demo/cyto-id` and `/chat`, plus all existing
auth, session isolation, persistence, invalidation, retrieval, provenance and export
tests.

Required frontend checks:

```text
$ npm run typecheck --prefix frontend
> tsc -b --pretty false

$ npm run lint --prefix frontend
> oxlint

$ npm run build --prefix frontend
vite v8.3.0 building client environment for production...
✓ 67 modules transformed.
dist/index.html                   1.04 kB │ gzip:   0.53 kB
dist/assets/index-CFuUqaEU.css   40.35 kB │ gzip:   7.57 kB
dist/assets/index-CNVPfeZs.js   529.94 kB │ gzip: 146.91 kB
✓ built in 193ms
```

Vite retained its existing non-failing advisory that one minified chunk exceeds 500 kB.
Additional checks:

```text
$ npm run test:auth --prefix frontend
# tests 1
# pass 1
# fail 0

$ node --check scripts/browser_react_smoke.cjs
[no output; exit 0]

$ git diff --check
[no output; exit 0]

$ PLAYWRIGHT_PATH=... node scripts/browser_react_smoke.cjs
React browser smoke passed: routed home/about/dashboard/chat/new-review/demo surfaces, workflow-only step strip, login/signup/recovery UI, mismatch validation, logged-out public demo, evidence/access, edited decision/export, failed API state, safe mobile layout; no page errors.
```

The passing browser run used the documented local Vite address
`http://127.0.0.1:5173` with FastAPI at `http://127.0.0.1:8000`. It created and exported
the predefined demo only; it did not perform OAuth or an external model call.

### Blockers and unverified assumptions

- No Phase I source change has been committed, pushed or redeployed in this run. The
  hosted Vercel/Render route behavior remains unverified, as do the previously recorded
  Phase H external-integration items.
- A separate exploratory smoke against the FastAPI-served production build reached the
  end of the functional journey, then failed its no-console-error assertion because the
  existing production CSP blocks the existing Google Fonts stylesheet. The documented
  Vite smoke passed with no page errors, and system font fallbacks render the FastAPI
  page. This pre-existing CSP/font mismatch was not changed in the routing-only phase.
- A refreshed unsaved `/review/{id}` cannot restore its temporary draft because page
  reload intentionally creates a new browser draft-session capability. Saved reviews
  remain reopenable from the authenticated dashboard after their configured persistence
  path succeeds.

### Manual action required

- None for local Phase I use. To publish these routes, commit and redeploy both the
  frontend and backend, then verify direct loads of every route on the stable hosted
  domain. Keep the current Supabase redirect allowlist pointed only at trusted app URLs;
  no migration or new environment variable is required for Phase I.

### Phase result

**PASS** for local Phase I acceptance: the first-time home view has no review workflow,
authentication defaults to the dashboard, all dedicated paths render, and the workflow
strip is confined to review/demo workspaces. Stop after Phase I.

## 2026-09-22 — Phase II: publication integrity cross-check

Status: **PASS LOCALLY; HOSTED REDEPLOYMENT UNVERIFIED. PHASE III NOT STARTED.**

### Changes made

- Added `researchguard/integrity.py` with the required deterministic states: `clean`,
  `retracted`, `correction`, `expression_of_concern`, `not_applicable` and
  `check_failed`. Each result records every check method, timestamp, outcome, details,
  bounded notice metadata and safe notice links.
- PubMed sources parse `CommentsCorrectionsList` from the EFetch XML already used to
  construct the source. `RetractionIn`, `ExpressionOfConcernIn` and correction/erratum
  relationships map deterministically; unrelated comment links do not create a flag.
- Moved NCBI access into one shared process throttle so direct PMC sources can check
  their PMID without bypassing the existing below-three-requests/second limit. When a
  PubMed record has no relevant notice and the source has a valid DOI, a bounded
  Crossref fallback checks both `updated-by` and `update-to`. It uses one concurrent
  request and at most four requests/second, below Crossref's current public
  single-record limit. `CROSSREF_MAILTO` uses the polite pool when configured and
  otherwise reuses `NCBI_EMAIL` when present.
- Crossref, PubMed, parse, timeout or rate-limit failure attaches `check_failed` to the
  successfully retrieved source instead of discarding it or marking it clean.
  Manufacturer/synthetic records are explicitly `not_applicable`. Older saved records
  may omit the new optional field and render unavailable/not confirmed clean.
- Added neutral, amber and red integrity panels to React source cards and a compact
  legacy-interface status. The review workspace and About page explain that this check
  covers PubMed/Crossref-indexed notices only, is not exhaustive, and does not establish
  that an unflagged paper is correct.
- Integrity provenance round-trips through canonical JSON and readable TXT exports,
  which also preserves it in explicitly saved review snapshots. No API route, database
  table, migration, review save rule, model call, provider fallback or billing setting
  was added.
- Added a reproducible bounded live verifier and updated README, API, deployment,
  architecture, feature-verification and context records. Official NCBI and Crossref
  documentation was checked before implementation.

### Checks actually executed

Required backend suite:

```text
$ .venv/bin/python -m unittest discover -s tests -v
----------------------------------------------------------------------
Ran 101 tests in 1.962s

OK
```

The nine new fixture tests cover all six states, the documented retracted PMID,
PubMed-to-Crossref fallback provenance, malformed Crossref content, `check_failed`
remaining distinct from `clean`, and JSON/TXT export round-tripping. All existing
retrieval, unsafe-URL, redirect, content-limit, validation, session, RLS and export tests
remain green.

Required frontend checks:

```text
$ npm run typecheck --prefix frontend
> tsc -b --pretty false

$ npm run lint --prefix frontend
> oxlint

$ npm run build --prefix frontend
vite v8.3.0 building client environment for production...
✓ 67 modules transformed.
dist/index.html                   1.04 kB │ gzip:   0.53 kB
dist/assets/index-C7WfX_UN.css   40.89 kB │ gzip:   7.62 kB
dist/assets/index-DvptT8UZ.js   532.20 kB │ gzip: 147.51 kB
✓ built in 212ms
```

Vite retained its existing non-failing advisory that one minified chunk exceeds 500 kB.
The updated browser journey rendered the explicit archived-source failure and
manufacturer not-applicable panels:

```text
$ PLAYWRIGHT_PATH=... node scripts/browser_react_smoke.cjs
React browser smoke passed: routed home/about/dashboard/chat/new-review/demo surfaces, workflow-only step strip, login/signup/recovery UI, mismatch validation, logged-out public demo, evidence/access, edited decision/export, failed API state, safe mobile layout; no page errors.
```

Python compileall, legacy/browser JavaScript syntax checks and `git diff --check` also
exited 0.

Bounded external verification, after the sandboxed attempt reported `Public source DNS
lookup failed`, passed with network access explicitly allowed:

```text
$ .venv/bin/python -m scripts.verify_integrity_live
{
  "pubmed": {
    "source_pmid": "38510612",
    "source_url": "https://pubmed.ncbi.nlm.nih.gov/38510612/",
    "source_hash": "e265048d7321213b074a09bba3b4cc5b741f43a2928f01e04bd0edcb0316a6d5",
    "integrity_status": "retracted",
    "checked_via": "pubmed",
    "checked_at": "2026-09-22T17:17:34.955131+00:00",
    "notice_relations": ["RetractionIn"],
    "notice_identifiers": ["PMID 38868598"],
    "notice_urls": ["https://pubmed.ncbi.nlm.nih.gov/38868598/"]
  },
  "crossref": {
    "source_doi": "10.1177/1758835920922055",
    "integrity_status": "retracted",
    "checked_via": "crossref",
    "checked_at": "2026-09-22T17:17:36.168805+00:00",
    "notice_relations": ["updated-by", "updated-by"],
    "notice_identifiers": [
      "DOI 10.1177/17588359231172420",
      "DOI 10.1177/17588359231172420"
    ],
    "notice_sources": ["crossref:retraction-watch", "crossref:publisher"]
  },
  "passages_printed": false,
  "model_calls": 0
}
```

The live verifier output recorded PubMed source SHA-256
`e265048d7321213b074a09bba3b4cc5b741f43a2928f01e04bd0edcb0316a6d5` and UTC check
timestamps. It printed no article passages, API credentials or model output.

### Blockers and unverified assumptions

- PubMed/Crossref metadata can be incomplete, delayed or internally duplicated. The
  live Crossref record returned the same notice from two named sources; both assertions
  are retained rather than silently collapsed. No absence-of-notice state is presented
  as proof that a paper is valid.
- The archived demonstration paper predates this feature, so its card honestly reports
  `check_failed`/not confirmed clean rather than attaching a new live result to an old
  archived retrieval. Its manufacturer source reports `not_applicable`.
- Hosted Render/Vercel behavior is unverified until the source changes are redeployed.
  Existing Phase H OAuth, email, two-user hosted and live-model blockers are unchanged.

### Manual action required

1. Set `CROSSREF_MAILTO` to a monitored contact email in Render, or keep a valid
   `NCBI_EMAIL` for reuse. This is identification for Crossref's polite pool, not a
   credential. Do not add it to a `VITE_` variable.
2. Redeploy Render and Vercel. Retrieve one public PubMed source and one PMC/DOI source,
   verify their integrity panels and exports, and confirm failed Crossref access renders
   unavailable/not confirmed clean. No Supabase migration or billing change is needed.

### Phase result

**PASS** for local Phase II acceptance. PubMed and Crossref notice paths are live
verified with bounded public requests; fixtures cover every required state and failure
semantics; the browser and canonical exports preserve the results. Stop after Phase II.

## 2026-09-25 — Phase III: explicit multi-provider assessment comparison

Status: **PASS LOCALLY; LIVE PROVIDER CALL AND HOSTED MIGRATION/JOURNEY UNVERIFIED.**

### Changes made

- Added an authenticated, explicit second-opinion route for completed primary
  assessments. The user selects one different provider from the existing Groq,
  OpenRouter-free, NVIDIA, or retained Gemini allowlist. The provider must pass the
  existing credential, configured-model, and operator-confirmed free/no-billing gates.
  It never runs automatically, never falls back, and never replaces the primary result.
- Both primary and second-provider results now use one structured assessment schema and
  independently pass the existing source-ID, exact quotation, and source-location
  validator. The second request uses the primary assessment's exact source IDs. Invalid
  secondary output is rejected while the primary assessment remains intact.
- Added canonical provider-assessment and attempt provenance: actual provider/model,
  primary flag, structural label, qualitative uncalibrated confidence, quote-check
  result, source IDs, timestamp, outcome, and safe failure detail. A visible attempt is
  recorded for unavailable, quota, malformed-output, and validation failures so the
  additional call or blocked preflight is not hidden. Claim/context edits and fresh
  retrieval clear every result tied to stale evidence.
- Added a side-by-side React comparison with provider/model tags, label, qualitative
  confidence, and quote-check result. The warning is computed in TypeScript from only
  `label`, `confidence`, and `quote_check_passed`; wording differences alone do not
  trigger it. No model writes a disagreement summary or combined verdict. The UI states
  that the action makes one extra provider call and may consume free quota.
- Added `supabase/migrations/202609250001_multi_provider_assessments.sql`. The normalized
  table is derived from explicitly saved canonical reviews, forces RLS, and has separate
  authenticated-owner SELECT, INSERT, UPDATE, and DELETE policies. Database triggers
  derive and preserve ownership; the client cannot assign another owner.
- Canonical JSON/TXT exports validate and preserve each provider result plus attempt
  history. `docs/EVALUATION.md` now excludes second opinions from `--run-model` batches.
  README, architecture, API, persistence, deployment, feature-status, and context records
  describe the actual contract and prepared-versus-applied state.
- Removed the frontend's remote Google Fonts request after the final browser rerun found
  it could abort independently of the application. The design now uses deterministic
  system font stacks and the no-page-error browser gate passes without an external font
  dependency.

### Checks actually executed

Required backend suite on the final Phase III backend implementation:

```text
$ .venv/bin/python -m unittest discover -s tests -v
----------------------------------------------------------------------
Ran 108 tests in 3.285s

OK
```

This includes five focused mocked-provider tests for matching structured fields despite
different wording, changed label/confidence, fabricated quotation rejection through the
same validator, visible quota failure that preserves the primary, unavailable provider
handling, and same-provider rejection. HTTP tests
also cover the authenticated second-opinion route and signed-out denial. Existing
retrieval, integrity, unsafe-URL, invalidation, persistence, export, and authentication
tests remain green.

Required frontend checks were rerun after removing the external font dependency:

```text
$ npm run typecheck --prefix frontend
> tsc -b --pretty false

$ npm run lint --prefix frontend
> oxlint

$ npm run build --prefix frontend
vite v8.3.0 building client environment for production...
✓ 68 modules transformed.
dist/index.html                   0.64 kB │ gzip:   0.38 kB
dist/assets/index-DiBZftIC.css   40.95 kB │ gzip:   7.61 kB
dist/assets/index-IvaIyw6M.js   537.04 kB │ gzip: 148.60 kB
✓ built in 330ms
```

Vite retained its existing non-failing advisory for a minified chunk over 500 kB.

The dedicated structural comparison test passed:

```text
$ npm run test:comparison --prefix frontend
1..1
# tests 1
# pass 1
# fail 0
```

The final actual React/FastAPI browser run passed after fresh local services started:

```text
$ PLAYWRIGHT_PATH=... node scripts/browser_react_smoke.cjs
React browser smoke passed: routed home/about/dashboard/chat/new-review/demo surfaces,
workflow-only step strip, login/signup/recovery UI, mismatch validation, logged-out
public demo, evidence/access, structural provider comparison, edited decision/export,
failed API state, safe mobile layout; no page errors.
```

Python compileall, JavaScript syntax checks, auth frontend tests, and `git diff --check`
also exited 0 during the Phase III verification run.

The versioned database migration was applied only to the disposable local Supabase
stack. The complete local policy suite passed:

```text
$ supabase migration up --local
Applying migration 202609250001_multi_provider_assessments.sql...

$ supabase test db
Files=4, Tests=57, Result: PASS
```

A read-only linked migration query showed `202609190001`, `202609190002`, and
`202609210001` in both local and remote history. It showed `202609250001` locally and no
remote entry. No hosted migration was pushed in this phase.

### Blockers and unverified assumptions

- No live second-provider request was made. Fixture tests establish provider selection,
  validation, failure, provenance, and UI behavior; they do not establish current Groq,
  OpenRouter, NVIDIA, or Gemini access, free quota, output quality, or agreement rates.
- Qualitative `low|medium|high` confidence is an uncalibrated model self-rating used only
  for structural comparison. It is not a probability, truth score, or scientific
  confidence interval.
- Migration `202609250001` is not applied to hosted Supabase. Hosted RLS syncing, saved
  comparison reload/export, and the complete browser journey remain unverified until it
  is pushed, the services are redeployed, and two authenticated users test isolation.
- Existing Phase H Google OAuth, email delivery/recovery, hosted two-user isolation,
  public Vercel reachability, Render health, and live model-generation blockers remain
  outside this phase and unchanged.

### Manual action required

1. Review the migration, run `supabase migration list`, then `supabase db push`, and run
   `supabase migration list` again. Confirm only `202609250001` changes from local-only
   to present remotely. Do not create the table manually or add a service-role key.
2. On Render, configure at least two desired evidence providers using server-only keys,
   allowlisted model IDs, and a `*_FREE_TIER_CONFIRMED=true` value only after verifying
   that exact account has free access with no billing. Put no provider key in Vercel or
   any `VITE_` variable.
3. Redeploy backend and frontend. With public/synthetic input and a signed-in disposable
   user, complete a primary assessment, request one second opinion, inspect the recorded
   provider/model and exact structural warning, explicitly save/reload/export it, and
   verify a second user cannot access the record. Stop if free quota is unavailable;
   do not enable billing or another-provider fallback.

### Phase result

**PASS** for local Phase III acceptance. The explicit second-provider path, equal
deterministic validation, structural comparison, visible quota provenance, exports, and
owner-scoped migration all pass controlled local checks. Live external provider behavior
and hosted migration/deployment remain explicitly unverified. Optional Phase IV was not
started. Stop after Phase III.
