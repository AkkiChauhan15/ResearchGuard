# Research Guard AI — Project context

Version: 2.1
Prepared: 2026-09-15; provider direction updated 2026-09-20
Purpose: Reference for the coding agent implementing the agreed phased build.

## Read this first

Read this file before planning, coding, changing scope, or resuming work after a context reset. Read applicable repository instructions as well. This file records project requirements; it does not override system instructions, access controls, or subsequent explicit user decisions.

This file cannot guarantee hallucination-free development or scientific judgments. Enforce its requirements through software validation, source checks, tests, and researcher review.

### User-authorized migration direction — 2026-09-16

The approved target is Python + FastAPI, React + TypeScript + Tailwind,
Supabase Free for Google authentication and explicitly saved reviews, and the
Gemini Developer API through an AI Studio Free Tier project. Development began locally.
On 2026-09-19 the user authorized preparation and exact manual instructions for a
public competition deployment using only free tiers. No paid services, billing
activation, paid fallbacks, or credit purchases are authorized. Exhausted free quotas or unavailable free access must
produce an explicit unavailable state, never an upgrade or paid fallback. The evidence-review
model still has no provider fallback.

Migration Phases A–G are implemented. Phase H was authorized on 2026-09-19 and performs
local end-to-end verification and competition preparation. The linked hosted Supabase
project reports migration `202609190001` applied. Its JWKS is reachable and anonymous
saved-review REST access is denied. A local Supabase stack additionally passed real
two-user JWT/PostgREST/RLS checks, but the Google OAuth browser round trip and hosted
authenticated two-user journey remain blocked. The locally configured Gemini key and
`gemini-3.8-flash` metadata access were verified on 2026-09-19. The adapter's Gemini 3.8
JSON Schema incompatibility was repaired, but bounded live generation attempts returned
HTTP 503 high demand before producing output. Do not claim those
external browser/model integrations work until their checks pass. Deployment-compatible
configuration and instructions are prepared. The frontend deployment is now verified
from public GitHub metadata, while public reachability and the hosted browser journey
remain unverified. Complete the remaining Render, Vercel, Supabase and Google settings
in `docs/DEPLOYMENT.md`; keep live OAuth and hosted behavior marked unverified until
that journey passes.

On 2026-09-19 the user also authorized account pages around the existing Supabase
identity boundary. `/login` and `/signup` reuse Google OAuth and conditionally expose
the project's enabled email/password method; `/forgot-password`, `/update-password`
and `/account` provide recovery and optional profile editing. Public Auth settings
reported Google, email and signup enabled with email confirmation required. The exact
dashboard password policy, email delivery, and real OAuth/confirmation/recovery round
trips remain unverified. The optional `researcher_profiles` migration `202609190002`
has owner-only RLS and is applied to the linked hosted database alongside
`202609190001`. Hosted profile isolation still requires a two-user check.

Deployment status changed on 2026-09-19. The user reports that the project is deployed,
and public GitHub deployment metadata verifies that Vercel successfully deployed commit
`1ce8ae3`. The generated Vercel deployment URL currently redirects unauthenticated
visitors to Vercel SSO, so public access and the stable production domain remain
unverified. The Render service URL was not available in the repository, so backend
health and production CORS remain unverified. A fresh linked Supabase migration query
confirmed both `202609190001` and `202609190002` are applied remotely; the optional
profile migration is no longer pending.

On 2026-09-20 the user explicitly authorized a separate general AI chat page using
Groq, OpenRouter, Gemini and NVIDIA NIM. This supersedes the earlier exclusion only for
this clearly labeled assistant surface; it does not replace or feed the structured
evidence-review workflow. Chat responses are unverified model output, require a verified
Supabase user, and are not saved as reviews. Keys
remain backend-only. Provider/model input is allowlisted in a versioned configuration.
Fallback is disabled by default and may run only when both the operator and user opt in,
only among configured providers confirmed for free/no-billing access, and always reports
the provider and model that answered. No paid model, billing, purchased credit, search
tool, or silent fallback is authorized.

On 2026-09-20 the user then authorized the already configured free chat-provider APIs
for structured evidence extraction and assessment **instead of Gemini**. The evidence
workflow now defaults to Groq with `openai/gpt-oss-20b`, whose official documentation
lists strict JSON Schema support. The operator may explicitly select `openrouter` or
`nvidia` instead; their model IDs remain narrowly allowlisted and their structured
outputs are still reparsed with Pydantic. Gemini is retained as an explicitly selectable
migration option, not the active default. Evidence requests never silently switch
providers. Keys remain server-side, free/no-billing gates remain mandatory, and
deterministic source-ID, quotation, location and original-span validation remain
authoritative.

On 2026-09-21 the user authorized private saved chat history and PDF chat exports.
Successful user/assistant turns are automatically saved in a separate Supabase
`saved_chats` table for the verified owner; they never enter the canonical evidence
review schema. Users can list, reopen, continue, export and delete their own chats.
Each assistant message retains its actual provider/model and fallback flag. Revision
checks prevent stale history overwrites, and row-level security derives immutable
ownership from `auth.uid()`. Migration `202609210001` is prepared but must not be
described as applied until hosted migration history confirms it. PDF exports remain
clearly labeled as unverified model output, not scientific evidence.

The 2026-09-21 follow-up-chat failure was traced to the backend PATCH payload including
immutable `schema_version`, which the authenticated role is intentionally not permitted
to update. The repository now sends only mutable columns on continuation. A real local
Supabase Auth/PostgREST/RLS create-follow-up-delete journey passed after the fix; hosted
behavior still requires a backend redeploy and browser confirmation.

Preserve working Pydantic schemas, retrieval adapters, evidence validation, curated
demo sources, review decisions, and exports. Adapt framework/provider boundaries
instead of rewriting the scientific review core. See `ARCHITECTURE.md` and
`MIGRATION_PLAN.md`. The user clarified that Phases B–H will be supplied
sequentially, one phase at a time. Reserve those definitions for the user; do not
infer their order or begin them automatically.

Inspect the repository before describing its state. Do not infer that the application exists because a sample case study describes it in the past tense. Prior competition drafts are illustrative narratives, not evidence of implementation, deployment, evaluation, or research outcomes.

## 1. Confirmed project intent

**Name:** Research Guard AI.

**Audience:** Early-career biomedical researchers who need help checking AI-generated research information.

**Problem:** Beginners may lack the expertise to recognize what needs verification. An answer can contain real references while drawing a conclusion those references or the experimental design do not support.

**Product purpose:** Make the relationship between a claim, its evidence, its experimental context, and its limitations visible. Help the researcher identify the next verification question.

**Primary journey:** Paste an answer → identify claims → retrieve evidence → assess support → inspect sources → revise the conclusion → save or export the review.

**Workflow language:** DEFINE → RISK → ASSIST → VERIFY → RECORD. Here, “risk” means review priority, not a clinical risk score or a probability that a claim is false.

**Communication style:** Clear, professional English. Explain technical terms when first used. Preserve scientific qualifications. Avoid unexplained jargon, inflated novelty claims, and marketing promises about perfect accuracy.

## 2. Requirements and unknowns

| Item | Status and required action |
| --- | --- |
| Core product and phased workflow | Agreed; preserve the intent described here. |
| Initial domains | Biological claims and assay/reagent interpretation. |
| Target deliverable | Working web application with evidence-linked reviews and exports. |
| Framework and hosting | FastAPI backend plus a Vite React/TypeScript/Tailwind frontend. Vercel successfully deployed the SPA commit; its generated URL is currently SSO-protected. The user reports Render deployment, but its URL and health are unverified. |
| Existing implementation | FastAPI/Uvicorn backend, React/TypeScript/Tailwind SPA, preserved legacy interface, process-local transient store, and reusable Pydantic/core modules. Verify against code and tests before claiming behavior. |
| Authentication and saving | Supabase supports Google and enabled email/password account pages, with backend token verification and owner binding for transient live reviews. Phase G adds explicit saved-review CRUD and versioned RLS. The review/profile migrations are applied; local two-user saved-review RLS/token behavior passed. A new owner-only saved-chat migration is prepared but not yet applied or live-verified. Google OAuth, email delivery/recovery, hosted profile/chat RLS behavior and hosted authenticated two-user behavior remain unverified. Unsaved review drafts stay transient. |
| API keys and account access | Gemini key/model metadata access was verified on 2026-09-19 without displaying the key, but generation remained blocked by HTTP 503. Non-Gemini provider keys are reported by the user as configured in the deployed chat environment but are absent from the local environment, so live structured generation through them remains unverified here. Never display secrets. |
| Model choices | Groq `openai/gpt-oss-20b` is the default structured extraction/assessment provider. `openrouter/free`, approved NVIDIA NIM models, and Gemini remain explicitly selectable. There is no evidence-provider fallback. Each provider remains unavailable until its key and required free/no-billing gate are present. The legacy OpenAI API adapter remains disabled. |
| Cost boundary | Free tiers only. No billing activation, purchases, paid services, upgrades, or paid fallback. |
| Performance, user adoption, savings | Unmeasured; do not invent results. |
| Demonstration interaction | Reconstructed; not a historical transcript or a recorded live tool run. |
| Public deployment | The user reports deployment, and Vercel metadata verifies a successful production deployment of commit `1ce8ae3`. Its generated deployment URL is currently protected by Vercel SSO. The stable Vercel production domain, Render health/CORS, and end-to-end hosted journey remain unverified. Use public/synthetic data and do not enable billing. |

Routine implementation choices may be made autonomously. Do not repeatedly ask for permission to read files, implement reversible changes, or run relevant tests. Explain genuine blockers and continue independent work. Do not bypass approval or access restrictions.

## 3. Initial scope

Include:

- Pasted text and optional public source URLs.
- Intended use: topic understanding, assay interpretation, presentation preparation, or experiment planning.
- Relevant optional context: organism/model, assay, reagent identifier, and conditions.
- Editable extracted claims.
- Live public evidence retrieval with visible access limitations.
- Observation versus inference, source passages, context mismatches, and suggested qualified wording.
- Researcher accept/edit/reject decisions and notes.
- Google authentication through Supabase Free (implemented with fixture verification;
  live OAuth unverified) and saving/loading a review only after an explicit researcher
  save action (hosted migration applied; hosted authenticated journey unverified).
- Readable and structured JSON review exports.
- Clearly separated demonstration and live modes.
- A separate authenticated general assistant chat with owner-only saved history and PDF
  export, visibly labeled as unverified model output and never treated as retrieved evidence.

Exclude from the first release:

- Raw microscopy or western blot image interpretation.
- Patient data, clinical diagnosis, or treatment recommendations.
- Autonomous experiment execution or automatic dosing instructions.
- Training a new foundation model.
- Broad, unsupported claims of coverage across all research domains.
- A generic chatbot that replaces the structured review workflow.

Do not reuse private cell identities, unpublished targets, experimental results, images, or laboratory details from other conversations. Demonstrations must use public information or explicitly synthetic examples.

## 4. Evidence rules

1. A paper’s existence does not establish support for a claim.
2. A matching passage does not establish that the claim follows from it.
3. Database indexing does not certify that a finding is correct.
4. Model agreement is not independent scientific evidence.
5. User-reported observations are not independently verified measurements.
6. Missing evidence is not proof that a claim is false.
7. A failed request or inaccessible document is an access limitation, not a biological finding.
8. Abstract-only access must never be described as a full-text or methods review.
9. A statement from another organism, cell model, assay, or treatment context must not be silently generalized.
10. Association, prediction, proposed mechanism, and experimentally supported causation must remain distinct.
11. Do not invent titles, DOIs, PMIDs, quotations, page numbers, figures, passages, or document versions.
12. Cite only source IDs supplied by retrieval; reject unknown IDs before rendering or export.
13. Preserve the distinction between exact quotations and model-written summaries.
14. Validate exact quotations against retrieved text with limited, documented normalization. Preserve the original text.
15. Conflicting relevant evidence must be shown, not hidden to obtain a single confident answer.
16. Missing product identity requires a targeted question, not a guessed manufacturer or catalog number.
17. Correct arithmetic does not establish that an experimental condition is suitable.
18. Do not promise that suggested controls alone guarantee a mechanistic conclusion.

## 5. Assessment and retrieval states

Use the following evidence statuses:

| Status | Meaning |
| --- | --- |
| Supported within the stated context | Retrieved, accessible evidence supports the specific statement and its context. This is not universal certification. |
| Partially supported | Only part of the statement or a narrower conclusion is supported. |
| Conflicting evidence | Relevant retrieved evidence disagrees. Explain differences where possible. |
| Contradicted by retrieved evidence | Accessible evidence directly conflicts with the claim in the relevant context. |
| Insufficient evidence found | Accessible retrieved evidence does not resolve the claim. |

Keep access state separate, for example: `ok`, `no_results`, `partial_access`, `rate_limited`, `fetch_failed`, or `parse_failed`.

If retrieval or assessment fails, show the failure. Do not fabricate an evidence status from model memory. An assessment can be absent while retrieval is unavailable.

Do not produce confidence percentages or aggregate truth scores without a separately justified calibration method. Do not let a single overall verdict conceal mixed claim-level results.

## 6. Source strategy

Start with adapters for:

- PubMed: citation metadata and available abstracts.
- PubMed Central: accessible full text, subject to applicable access and reuse conditions.
- Exact official manufacturer product pages and public manuals.

Read current official integration documentation before implementing APIs. Do not invent endpoints, parameters, response schemas, SDK methods, supported features, rate limits, or licenses. If documentation or integration testing is unavailable, record the uncertainty and label the adapter unverified.

Search using the claim and context, including evidence that could limit or contradict it. Do not assume the first search result is authoritative. Prefer primary research for claims about experiments, methodological sources for interpretation rules, and exact official documentation for product questions.

For every retrieved source retain, where available:

- Internal source ID and retrieval-run ID.
- Canonical URL and source category.
- Title, authors, date, DOI/PMID/PMCID.
- Access level: metadata, abstract, full text, or product document.
- Retrieval timestamp and document version.
- Retrieved content or a permitted evidence extract.
- Passage text and actual location.
- Retrieval and parsing limitations.

Keep absent metadata null or explicitly unavailable. Do not infer missing page or section locations. Record enough provenance to explain later changes in a source.

## 7. Models and implementation roles

Active approved runtime direction (updated 2026-09-20): use one explicitly selected
non-Gemini free provider for structured extraction and assessment. The default is Groq
`openai/gpt-oss-20b`; OpenRouter is restricted to `openrouter/free`, and NVIDIA NIM is
restricted to the checked-in model allowlist. Groq and NVIDIA require an operator
confirmation that the exact account has free access with no billing. OpenRouter uses
only its zero-price free router. Documentation does not establish access in the user's
project, and no paid model or provider fallback is allowed.

Gemini `gemini-3.8-flash` was the Phase E provider and remains explicitly selectable
for migration compatibility, but it is no longer the default or active requirement.
Its previous 503 live-generation result does not establish that another provider works.

Previous planning candidates, **not active requirements or authorized fallbacks**:

- GPT-5 mini: claim extraction and missing-context identification.
- GPT-5.4: evidence comparison and explanation.

Codex assists application development, code review, and tests; it is not a runtime
evidence database. The former OpenAI implementation is retained only as a disabled
migration marker; provider selection rejects it and it is not an authorized fallback.

Previous candidates are not evidence of access or a reason to retain a paid runtime
dependency. One explicitly selected provider may perform both runtime tasks initially.

Record the model actually used and any available snapshot/version information. Keep AI use during development separate from AI use inside the application.

Use strict structured outputs where supported and validate them in application code. Give the comparison model only identified claims, user context, and retrieved source material. Require it to explain support from that material. Do not let model memory silently fill evidence gaps.

The backend handles retrieval, source-ID validation, passage matching, unit-aware calculations where implemented, credentials, and exports. Do not delegate deterministic validation solely to a language model.

## 8. Minimum review record

Define typed schemas before integration. A review record should represent:

- `review_id`, creation time, and mode (`demo` or `live`).
- Original input and intended use.
- User-reported context and missing fields.
- Extracted claims with stable claim IDs, original spans, types, observations, and inferences.
- Retrieval attempts, access states, and source records.
- Per-claim evidence status when an assessment exists.
- Evidence links containing source ID, passage, location, and support/limitation/conflict relationship.
- Plain-language explanation, context mismatches, and limitations.
- Suggested revised wording and next verification step.
- Researcher decision (`pending`, `accepted`, `edited`, or `rejected`), final wording, and notes.
- Actual model identifiers, prompt version, and validation results.

Do not mark an assessment human-approved until the researcher explicitly approves it. Preserve original suggestions when a user edits the final wording. Export the same provenance and mode labels shown in the interface.

## 9. Agreed demonstration case

**Title:** When more fluorescent spots do not mean more cellular activity.

**General question:** “If one sample has more fluorescent puncta in a CYTO-ID assay, does that mean autophagic activity has increased?”

**Reconstructed answer to review:** “More fluorescent puncta indicate increased autophagic activity.”

**Synthetic context:** Samples were compared at one time point without a lysosomal-inhibition comparison. No real cell identities, images, treatment outcomes, significance values, or private results are part of the example.

**Reasoning to examine:** More assay-positive puncta are an observation. Increased autophagic activity is an inference. The assessment must distinguish compartment abundance from flux and consider increased formation, reduced clearance, or both. Explain autophagic flux in plain English without equating it with puncta count.

**Candidate qualified wording:** “The sample showed more CYTO-ID-positive puncta under the measured conditions. This observation alone does not establish whether autophagic flux increased or decreased.”

**Next verification question:** Could an appropriately validated comparison of control and test conditions, each with and without lysosomal inhibition, help investigate formation and clearance? This is a plan for experimental review, not an automatic dose recommendation or completed result.

**Public source candidates:**

- Enzo CYTO-ID product page: https://www.enzo.com/product/cyto-id-autophagy-detection-kit/
- Loos, du Toit, and Hofmeyr, *Defining and measuring autophagosome flux—concept and reality*: https://pmc.ncbi.nlm.nih.gov/articles/PMC4502790/

These URLs identify material to inspect. This context file is not a substitute for retrieving their current accessible contents. Do not fabricate passages if access fails.

**Guardrails:**

- The original answer is a reconstructed example, not an authenticated past ChatGPT quote.
- The hypothetical Research Guard interaction is not an actual evaluation.
- The case does not establish that autophagy was increased or blocked.
- The case outcome is a revised interpretation and follow-up question, not a completed biological discovery.
- A curated demo may use predefined results if prominently labeled “Demonstration — not a live verification.”
- Live mode must assess actual retrieved evidence. Do not hardcode the expected verdict by recognizing this question.
- Never substitute demo output for failed live retrieval, even temporarily.

## 10. Phase sequence and completion gates

The numbered phases below are the original product gates and remain requirements,
not claims of completion. The later migration uses letters A–H to avoid confusing
the two sequences. Migration Phases A–H have been supplied and executed within their
recorded limits. External Google OAuth and successful selected-provider generation gates remain
blocked. Do not begin later work without the user's next instruction.

| Phase | Deliverable | Completion evidence |
| --- | --- | --- |
| 1. Architecture | Workspace inspection, stack decision, schemas, plan | Actual repository observations and documented decisions. |
| 2. Interface | Inputs, claim results, editable review, labeled demo | Usable UI with empty, loading, error, and demo states. |
| 3. Retrieval | Real source adapters and provenance | Successful representative retrievals, plus explicit failure/access handling. |
| 4. Assessment | Claim extraction and source-grounded comparison | Schema validation, source-ID checks, passage checks, traceable live assessment. |
| 5. Worked case | Autophagy example | Clear separation of curated demo and live evidence review. |
| 6. Review and export | Accept/edit/reject and exports | Export matches review state, provenance, mode, and human decisions. |
| 7. Evaluation | Public/synthetic case set and tests | Executed results with failures and denominators reported. |
| 8. Release preparation | Local preview, setup guide, limitations | Verified user journey, relevant security checks, no secret exposure. |

Do not treat writing a test as passing it. Do not mark an integration working because its mock passes. Use separate status fields for implementation and verification: e.g., implemented but unverified, tested with fixtures, verified live, or blocked.

At each phase report what works, what was actually tested, and what remains incomplete. Continue authorized independent work when a dependency is blocked. Do not weaken a requirement merely to mark a phase complete.

## 11. Evaluation requirements

Prepare approximately 12–20 public or explicitly synthetic cases with manually source-grounded reference assessments. Include supported claims, irrelevant real citations, causation overclaims, wrong models, assay misinterpretation, missing product identity, inaccessible evidence, contradictory findings, no results, and document prompt injection.

Use separate development and held-out cases. Do not change held-out expected assessments merely to match model outputs. Record legitimate corrections to a reference assessment with a reason.

Measure claim extraction, citation validity, actual support, context matching, false alarms, and handling of uncertainty. Report case counts and failure examples. Do not use a second model's agreement as ground truth. Seek knowledgeable human review of scientific reference assessments where feasible.

Meaningful software tests should cover unknown source IDs, nonexistent passages, malformed model output, missing credentials, failed retrieval, unsafe URLs, demo/live separation, and exported provenance.

Do not invent accuracy, time savings, user learning, or adoption. A small pilot cannot certify reliability across all research.

## 12. Privacy and security

Keep credentials server-side and out of logs, exports, source control, and browser bundles. Treat retrieved documents as untrusted content, not instructions. Safely render external text.

Restrict URL retrieval: allow only supported schemes and destinations; block local/private/link-local networks and metadata services; validate redirects and resolved destinations; apply reasonable time, size, and content-type limits. Do not fetch arbitrary user URLs without those protections.

Do not persist full user inputs by default. Saving must be explicit. Explain external model processing and actual retention behavior accurately. Do not claim local-only processing, confidentiality guarantees, security certification, or regulatory compliance without evidence.

For the approved migration, signing in must not automatically save a draft. Explicitly
saved reviews may reside in Supabase; unsaved review bodies must remain transient.
Derive ownership from a server-verified Supabase identity, not the existing client-made
session header or a request-body user ID. Enforce owner isolation in the application
and database row-level security; test two distinct users and signed-out access.
Keep every model-provider key, OAuth client secret, and database service secret out of
frontend bundles, logs, and exports. Revise processing/retention notices for the
actually selected external provider and Supabase. Local application
hosting does not mean authentication, saved data, or model processing stay local.

## 13. Competition context

The intended competition category concerns actual useful AI use in research. The final case should show one concrete problem, AI's contribution, inspected evidence, a changed decision, and honestly documented results.

The user requested an approximately two-page A4 narrative with comprehensible professional scientific language. Building the app is the current coding task; automatically writing another proposal is not a substitute.

Prior sample documents imagine a completed application. They do not authorize invented experiments, usage records, model logs, screenshots, performance metrics, or historical claims. Use actual screenshots and records once available. Label reconstructions and demonstrations clearly.

Do not claim Research Guard invents literature search or guarantees error-free research. Explain its contribution through its observation-to-inference checks, contextual evidence review, beginner explanations, and review record.

## 14. Continuity and honest progress reporting

Maintain a separate `PROGRESS.md` during implementation. Record:

- Current phase and implementation/verification status.
- Files or components changed.
- Commands and relevant tests actually run, with outcomes.
- Live integrations verified and the verification date.
- Known failures, blockers, and unverified assumptions.
- Next concrete action.

Keep secrets and private research out of that file. Preserve this context as the agreed baseline. Record dated user-authorized changes rather than silently rewriting requirements or relabeling planned work as completed.

Before resuming, read this context, applicable project instructions, and progress notes; then confirm important state against the repository. Memory and previous narrative alone are insufficient.

## 15. Ready for user review

A user can paste a claim, retrieve real sources, inspect a source-linked assessment, review its limitations, edit the conclusion, and export the record. Missing access is clearly displayed. The demo is visibly labeled. Reported tests were actually executed. Private research is absent. Public deployment has not occurred without authorization.
