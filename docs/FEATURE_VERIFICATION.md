# Feature verification status

Status as of 2026-09-21. “Fixture” means controlled local inputs or mocked provider
responses. It is not a live external integration result.

| Feature | Status | Evidence |
| --- | --- | --- |
| Public curated demonstration | Live-verified locally | Actual React/FastAPI browser run, screenshots and canonical export |
| Claim editing, invalidation and decisions | Verified locally | Unit/HTTP tests and public browser decision flow |
| JSON/TXT canonical exports | Verified locally | Unit/HTTP tests plus actual JSON browser download |
| PubMed individual retrieval | Live-verified | Three current individual EFetch records |
| PMC full text when body exists | Live-verified | PMC8270360 body passages |
| Demo paper PMC access | Live-verified abstract-only | PMC4502790 returned no readable body |
| Exact Enzo page and manual | Live-verified | Current product page and 22 bounded manual page extracts |
| Unsafe URL and response limits | Fixture-verified | DNS, redirect, host/path/port, MIME, timeout and size tests |
| Non-Gemini evidence-provider boundary | Fixture-verified | Groq, OpenRouter-free and NVIDIA request shapes, bounds, structured parsing, safe errors and provenance pass controlled tests |
| Non-Gemini extraction/assessment | **Live-unverified locally** | No non-Gemini provider key is available in the local environment; hosted key/configuration was not accessible to this run |
| Retained Gemini compatibility | Fixture-verified; live generation blocked historically | Earlier requests reached Google but repeated HTTP 503 high demand produced no output; Gemini is no longer the default |
| General chat API and React UI | Fixture/browser-verified | Auth, allowlists, provider formats, context, explicit fallback metadata, errors, clear action and 390 px layout |
| Private saved chat and PDF | Fixture-verified; hosted migration pending | Owner-bound list/open/continue/delete, stale-history rejection and server PDF pass local HTTP tests; `202609210001` is prepared, not applied or browser-verified |
| Live general chat providers | **Blocked/partly configured locally** | Gemini is configured locally but its bounded request returned temporarily unavailable; deployed non-Gemini configuration was not accessible to this run |
| Supabase JWT verification | Live-verified locally | Two real local asymmetric access tokens plus tamper rejection |
| Supabase saved-review RLS | Live-verified locally | 16 pgTAP checks and two-user local PostgREST/FastAPI journey |
| Hosted Supabase migration | Applied, partially verified | CLI histories match; JWKS responds; anonymous REST is denied |
| Google sign-in and restoration | **Blocked** | No completed interactive Google OAuth round trip |
| Hosted two-user save isolation | **Blocked** | Requires two authenticated hosted users |
| Meaningful scientific support | Demonstration-only/unmeasured | Curated autophagy reasoning; 0/16 human-reviewed references and 0/16 model cases |
| Prompt-injection resistance | Fixture-only | Untrusted-data prompt boundary and two evaluation cases; no live model run |
| Keyboard/mobile layout | Browser-verified locally | Focus checks, 390 px overflow/font checks; no full WCAG audit |
| Public deployment | Partially verified | Vercel deployment metadata succeeds, but its generated URL redirects to Vercel SSO; public reachability and Render health remain unverified |
