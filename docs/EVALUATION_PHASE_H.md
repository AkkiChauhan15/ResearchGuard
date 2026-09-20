# Phase H evaluation report

Date: 2026-09-19  
Scope: local verification only; no deployment, billing, paid fallback, or private data.

> Historical Phase H record: Gemini was the selected evidence provider during this
> evaluation. On 2026-09-20 the configured default changed to Groq; no non-Gemini live
> result has been added to the denominators below.

## Result

Phase H is **BLOCKED for the complete live browser journey**. The public demonstration,
local application checks, live public-source retrieval, and real local Supabase database
boundaries passed. Google OAuth and Gemini could not be exercised because the Google
provider round trip is not configured/available to this run and no Gemini API key or
operator Free Tier confirmation is present.

No scientific accuracy or time-saving result is claimed.

## Evaluation denominators

The case file SHA-256 is
`1d19ba7693fac1c8647e9dbab4af68e19eb5089b5e188818267e09c8adcdf5f1`.
The references remain agent-authored drafts awaiting knowledgeable human review.

| Split | Cases checked for fixture consistency | Gemini cases attempted | Gemini cases completed | Human-reviewed references |
| --- | ---: | ---: | ---: | ---: |
| Development | 10/10 | 0/10 | 0/10 | 0/10 |
| Held-out | 6/6 | 0/6 | 0/6 | 0/6 |
| Total | 16/16 | 0/16 | 0/16 | 0/16 |

Development IDs: `supported_observation`, `causation_overclaim`, `wrong_model`,
`assay_puncta`, `missing_product`, `inaccessible`, `conflicting`, `no_results`,
`prompt_injection`, and `irrelevant_real_citation`.

Held-out IDs: `supported_scope`, `universal_scope`, `abstract_methods`,
`prediction_vs_measurement`, `arithmetic_suitability`, and `injection_wrong_model`.

The held-out split was inspected only by the consistency runner. No output was used to
tune code or references. `scripts/evaluate.py` now defaults live model evaluation to a
maximum batch of two cases; a larger batch must be requested explicitly. Because the
provider check was blocked, no free-quota calls were attempted and no paid remedy was
used.

## Executed checks

| Requirement | Evidence and result | Limit |
| --- | --- | --- |
| Citation identity and exact passage/location validation | Python suite passed unknown-ID, nonexistent-quotation, wrong-location, metadata-only and whitespace-normalization tests. Fresh records retained PMID 25484088, PMCID PMC4502790, hashes, locations and timestamps. | Structural validity does not prove entailment. |
| Meaningful support | The curated autophagy explanation distinguishes puncta abundance from flux and cites exact accessible passages. The case artifact keeps those passages and provenance. | No live Gemini assessment and no knowledgeable human grading occurred; semantic performance is unmeasured. |
| Abstract-only and partial-result labels | Fresh PubMed and PMC retrieval for the demo paper both returned `abstract`; PMC4502790 had one abstract passage and no readable body. The browser showed `Partial result or access limitation` and the separate access labels. | Current endpoint access can change. |
| No paid quota fallback | Missing credentials produced `unavailable_missing_credentials`, zero calls, and the explicit message that no demonstration result was substituted. Fixture 429/quota tests passed. | Live quota exhaustion was not induced without credentials. |
| Prompt injection | The system prompt treats every source field as untrusted data, disables provider tools/search/caching, and fixture cases remain in both dev and held-out sets. Structured output and deterministic citation checks passed. | Live model resistance is blocked and therefore unverified. |
| Ownership and tokens | Local Supabase pgTAP passed 16/16 owner/RLS checks. A real local Auth/PostgREST/FastAPI check verified two signed access tokens, rejected a tampered token and forged owner field, and enforced owner-only list/open/update/export/delete. | The local identities used email fixtures. Google OAuth and two-user checks against the hosted project remain unverified. |
| Unsafe URLs | Unit tests passed private/mixed DNS, private redirect, unsupported host/path/port, MIME, byte limit, rate-limit and timeout cases. | This is targeted coverage, not a security audit. |
| Claim-edit invalidation | Unit and HTTP checks passed for removal of stale assessment, current source links and decisions; the saved revision path preserves the invalidated canonical review. | The local live integration began without a model assessment; its edit check corroborated the empty/pending state. |
| Accessibility and responsive layout | Headless Chrome passed skip-link/focus navigation, form tab order, readable base font and no horizontal overflow at 390 x 844. | No comprehensive assistive-technology or WCAG audit occurred. |

## Live source results

The bounded read-only source run completed successfully:

- PubMed search: 3/3 individual EFetch records preserved, all abstract access.
- Demo paper: PMID 25484088 resolved to PMCID PMC4502790 and abstract access.
- PMC full-text control: PMC8270360 returned 39 passages, including 35 body passages,
  and was correctly labeled full text.
- Demo PMC record: PMC4502790 returned one abstract passage; OAI front matter was
  available, while the full-text OAI request returned HTTP 400.
- Exact Enzo product page: 160 bounded text blocks, visible version
  `Last modified: May 29, 2024`.
- Exact official manual: 22 complete physical-page extracts from the 28-page PDF,
  version `HTTP Last-Modified: Tue, 27 Jun 2023 11:15:20 GMT`.

The detailed autophagy record is
[`artifacts/competition-demo/autophagy-case-record.json`](../artifacts/competition-demo/autophagy-case-record.json).
It separates fresh retrieval from the curated browser demonstration. It preserves the
reconstructed input, real source metadata/access/hashes/passages/timestamps, researcher
edit, and an explicit null model output with zero attempted calls.

## Browser results

The actual React/FastAPI public journey passed:

1. Open signed-out application.
2. Open the clearly labeled demonstration.
3. Inspect observation versus inference, exact passages, access limitations, wording,
   and next verification question.
4. Record edited wording and researcher notes.
5. Export canonical JSON.
6. Confirm mobile layout and a visible failed-API state without losing the open review.

Artifacts:

- [`react-empty-desktop.png`](../artifacts/competition-demo/react-empty-desktop.png)
- [`react-demo-desktop.png`](../artifacts/competition-demo/react-demo-desktop.png)
- [`react-signed-out-mobile.png`](../artifacts/competition-demo/react-signed-out-mobile.png)
- [`autophagy-demo-export.json`](../artifacts/competition-demo/autophagy-demo-export.json)
- [`browser-run.json`](../artifacts/competition-demo/browser-run.json)

The requested Google sign-in → Gemini → save → reload browser journey was not run to
completion. Substituting fixture login or curated content would not verify that journey.

## Known limitations and blockers

- Follow-up on 2026-09-19 verified that the configured key can access
  `gemini-3.8-flash` metadata. The strict Pydantic schema initially failed through the
  SDK's older `response_schema` conversion; the adapter now uses the official
  `response_json_schema` path and disables automatic function calling. Google accepted
  the repaired request but repeatedly returned HTTP 503 high demand after bounded
  retries. Live extraction/assessment output and prompt-injection behavior remain blocked.
- Google OAuth dashboard setup and an interactive browser round trip remain incomplete.
  Hosted access-token refresh, account switching and hosted two-user database behavior
  remain unverified.
- The linked Supabase project reports migration `202609190001` applied, and anonymous
  REST access is denied, but no hosted authenticated user journey was performed.
- The 16 references are not human-reviewed ground truth. Scientific support, context
  matching, false alarms and uncertainty performance all remain unmeasured.
- Screenshots show reconstructed synthetic input and a curated demonstration. They are
  not represented as a historical live model run.
