# Feature verification status

Status as of 2026-09-26. “Fixture” means controlled local inputs or mocked provider
responses. It is not a live external integration result.

| Feature | Status | Evidence |
| --- | --- | --- |
| Dedicated application routes (Phase I) | Verified locally | FastAPI direct-route HTTP tests plus Vite/FastAPI headless Chrome journey across Home, About, Dashboard, Chat, New Review and Demo; typecheck/lint/build pass |
| Accessible interface motion (Phase IV) | Browser-verified locally; hosted unverified | Headless Chrome confirms sticky scroll state, one shared nav underline, one-time Home/About reveals, Verify-to-Record workflow state, non-sticky workflow strip, reduced-motion instant layout, and no page errors |
| Public curated demonstration | Live-verified locally | Actual React/FastAPI browser run, screenshots and canonical export |
| Claim editing, invalidation and decisions | Verified locally | Unit/HTTP tests and public browser decision flow |
| JSON/TXT canonical exports | Verified locally | Unit/HTTP tests plus actual JSON browser download |
| PubMed individual retrieval | Live-verified | Three current individual EFetch records |
| PMC full text when body exists | Live-verified | PMC8270360 body passages |
| Demo paper PMC access | Live-verified abstract-only | PMC4502790 returned no readable body |
| Exact Enzo page and manual | Live-verified | Current product page and 22 bounded manual page extracts |
| Unsafe URL and response limits | Fixture-verified | DNS, redirect, host/path/port, MIME, timeout and size tests |
| Retraction/correction/integrity notices | PubMed and Crossref live-verified; UI fixture-verified | Live PMID 38510612 returned `RetractionIn` PMID 38868598; Crossref DOI 10.1177/1758835920922055 returned `updated-by` retraction metadata; six explicit states and exports pass fixtures |
| Non-Gemini evidence-provider boundary | Fixture-verified | Groq, OpenRouter-free and NVIDIA request shapes, bounds, structured parsing, safe errors and provenance pass controlled tests |
| Non-Gemini extraction/assessment | **Live-unverified locally** | No non-Gemini provider key is available in the local environment; hosted key/configuration was not accessible to this run |
| Opt-in provider second opinion (Phase III) | Fixture/HTTP/browser/RLS verified locally; live model unverified | Mocked matching, structural mismatch, wording-only difference, invalid quote and unavailable-provider cases pass; UI shows the extra call and exact changed fields; migration `202609250001` passed local pgTAP but is not hosted |
| Retained Gemini compatibility | Fixture-verified; live generation blocked historically | Earlier requests reached Google but repeated HTTP 503 high demand produced no output; Gemini is no longer the default |
| General chat API and React UI | Fixture/browser-verified | Auth, allowlists, provider formats, context, explicit fallback metadata, errors, clear action and 390 px layout |
| Private saved chat and PDF | Fixture-verified; hosted browser path unverified | Owner-bound list/open/continue/delete, stale-history rejection and server PDF pass local HTTP tests; hosted migration history now contains `202609210001` |
| Live general chat providers | **Blocked/partly configured locally** | Gemini is configured locally but its bounded request returned temporarily unavailable; deployed non-Gemini configuration was not accessible to this run |
| Supabase JWT verification | Live-verified locally | Two real local asymmetric access tokens plus tamper rejection |
| Supabase saved-review RLS | Live-verified locally | 16 pgTAP checks and two-user local PostgREST/FastAPI journey |
| Hosted Supabase migrations | Core review/profile/chat applied; Phase III pending | CLI histories contain `202609190001`, `202609190002`, and `202609210001`; `202609250001` remains local-only; JWKS responds and anonymous saved-review REST is denied |
| Google sign-in and restoration | **Blocked** | No completed interactive Google OAuth round trip |
| Hosted two-user save isolation | **Blocked** | Requires two authenticated hosted users |
| Meaningful scientific support | Demonstration-only/unmeasured | Curated autophagy reasoning; 0/16 human-reviewed references and 0/16 model cases |
| Prompt-injection resistance | Fixture-only | Untrusted-data prompt boundary and two evaluation cases; no live model run |
| Keyboard/mobile layout | Browser-verified locally | Focus checks, 390 px overflow/font checks; no full WCAG audit |
| Public deployment | Partially verified | Vercel deployment metadata succeeds, but its generated URL redirects to Vercel SSO; public reachability and Render health remain unverified |
