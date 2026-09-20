# Feature verification status

Status as of 2026-09-20. “Fixture” means controlled local inputs or mocked provider
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
| Gemini provider boundary | Fixture-verified and live configuration-verified | Key/model metadata accepted; JSON Schema adapter repaired; bounds and error tests pass |
| Gemini extraction/assessment | **Blocked by provider availability** | Repaired requests reached Google; repeated HTTP 503 high demand produced no output |
| General chat API and React UI | Fixture/browser-verified | Auth, allowlists, provider formats, context, explicit fallback metadata, errors, clear action and 390 px layout |
| Live general chat providers | **Blocked/partly configured** | Gemini is configured but the bounded request returned temporarily unavailable; other provider keys are absent |
| Supabase JWT verification | Live-verified locally | Two real local asymmetric access tokens plus tamper rejection |
| Supabase saved-review RLS | Live-verified locally | 16 pgTAP checks and two-user local PostgREST/FastAPI journey |
| Hosted Supabase migration | Applied, partially verified | CLI histories match; JWKS responds; anonymous REST is denied |
| Google sign-in and restoration | **Blocked** | No completed interactive Google OAuth round trip |
| Hosted two-user save isolation | **Blocked** | Requires two authenticated hosted users |
| Meaningful scientific support | Demonstration-only/unmeasured | Curated autophagy reasoning; 0/16 human-reviewed references and 0/16 model cases |
| Prompt-injection resistance | Fixture-only | Untrusted-data prompt boundary and two evaluation cases; no live model run |
| Keyboard/mobile layout | Browser-verified locally | Focus checks, 390 px overflow/font checks; no full WCAG audit |
| Public deployment | Partially verified | Vercel deployment metadata succeeds, but its generated URL redirects to Vercel SSO; public reachability and Render health remain unverified |
