# Free deployment: Vercel frontend + Render backend

This is the supported first hosted layout for the current application:

- **Vercel Hobby:** the static Vite/React frontend in `frontend/`.
- **Render Free:** one long-running FastAPI process from the repository root.
- **Supabase Free:** the existing Auth and Postgres project.
- **Gemini Developer API:** the server-side key from the confirmed Free Tier project.

Use this only for the personal, non-commercial competition demonstration allowed by
Vercel Hobby terms. Do not add a payment method, enable billing, select a paid Render
instance, or configure a paid model. The instructions prepare a public deployment;
they do not prove Google OAuth, Gemini generation, or hosted owner isolation works.

## 1. Push a reviewed revision to GitHub

Both hosts deploy the Git commit in `AkkiChauhan15/ResearchGuard`, not uncommitted local
files. Review `git status`, commit the intended source, and push `main`. Do not commit
the root `.env`, `frontend/.env.local`, tokens, keys, or any new export/screenshot that
contains private input. The checked-in competition artifacts contain only the labeled
public/synthetic demonstration.

## 2. Create the Render backend first

1. Sign in to Render and choose **New → Web Service**.
2. Connect GitHub and select `AkkiChauhan15/ResearchGuard`.
3. Enter these values:

| Render field | Exact value |
| --- | --- |
| Name | `research-guard-api` (or another available name) |
| Branch | `main` |
| Root Directory | leave blank |
| Language | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn researchguard.api:app --host 0.0.0.0 --port $PORT --workers 1 --no-access-log` |
| Instance Type | `Free` |
| Health Check Path | `/api/health` |

The checked-in `.python-version` pins Python 3.14.3. Keep exactly one worker because
temporary drafts, locks, and source throttling are process-local.

4. Add these Render environment variables. Paste real values in the Render dashboard;
   never place them in source control.

```dotenv
SUPABASE_URL=https://<PROJECT_REF>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_<PROJECT_VALUE>
NCBI_EMAIL=<YOUR_CONTACT_EMAIL>
LLM_PROVIDER=gemini
GEMINI_API_KEY=<YOUR_EXISTING_SERVER_SIDE_KEY>
GEMINI_FREE_TIER_CONFIRMED=true
GEMINI_EXTRACTION_MODEL=gemini-3.8-flash
GEMINI_ASSESSMENT_MODEL=gemini-3.8-flash
```

To enable one or more optional `/chat` providers, add their keys to **Render only**:

```dotenv
GROQ_API_KEY=<OPTIONAL_SERVER_KEY>
GROQ_FREE_TIER_CONFIRMED=false
OPENROUTER_API_KEY=<OPTIONAL_SERVER_KEY>
NVIDIA_NIM_API_KEY=<OPTIONAL_SERVER_KEY>
NVIDIA_NIM_FREE_TIER_CONFIRMED=false
RESEARCHGUARD_CHAT_FALLBACK_ENABLED=false
```

Leave unused values absent. Change a confirmation to `true` only after verifying the
actual account has free access and no billing. Keep fallback false for the first live
check. Never put these keys in Vercel or a `VITE_` variable. See `docs/CHAT_SETUP.md`.

Do not create `VITE_` variables on Render. Do not add a Supabase service-role/secret
key or a Google client secret. `RENDER_EXTERNAL_HOSTNAME` is provided automatically
and the backend uses it as its exact trusted host.

5. Leave `RESEARCHGUARD_FRONTEND_ORIGINS` unset for this first deploy. Click
   **Create Web Service**, wait for a successful health check, and copy the exact URL,
   for example `https://research-guard-api.onrender.com`.
6. Open `<RENDER_URL>/api/health`. It must return JSON with `"status":"ok"`.

## 3. Create the Vercel frontend

1. Sign in to Vercel with GitHub and choose **Add New → Project**.
2. Import `AkkiChauhan15/ResearchGuard`.
3. Use the **Hobby** plan and enter:

| Vercel field | Exact value |
| --- | --- |
| Framework Preset | `Vite` |
| Root Directory | `frontend` |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

4. Under **Environment Variables**, add these for **Production**:

```dotenv
VITE_SUPABASE_URL=https://<PROJECT_REF>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_<PROJECT_VALUE>
VITE_API_BASE_URL=https://<RENDER_SERVICE>.onrender.com
VITE_APPLICATION_ORIGIN=https://<VERCEL_PRODUCTION_DOMAIN>
VITE_SUPABASE_PASSWORD_MIN_LENGTH=6
```

`VITE_APPLICATION_ORIGIN` must exactly match the production origin: HTTPS, no path,
and no trailing slash. Match the password minimum to the actual Supabase Auth setting.
These values are compiled into the browser bundle. The two
Supabase values and service URLs are public configuration; the Gemini key, Google client
secret, Supabase secret/service-role keys, and JWT private keys must never be added.

5. Click **Deploy**. If the assigned production domain differs from the value entered,
   copy the exact domain from **Project → Settings → Domains**, correct
   `VITE_APPLICATION_ORIGIN`, and redeploy. Environment-variable edits do not change an
   already-built deployment.
6. Do not enable OAuth on Vercel preview URLs. The application intentionally accepts
   only the one configured production origin plus its local development origins.

## 4. Allow that Vercel origin in Render

In **Render → research-guard-api → Environment**, add:

```dotenv
RESEARCHGUARD_FRONTEND_ORIGINS=https://<VERCEL_PRODUCTION_DOMAIN>
```

Use the exact origin without a trailing slash or wildcard. Save it and allow Render to
redeploy. If a custom backend domain is added later, also set
`RESEARCHGUARD_ALLOWED_HOSTS` to that exact hostname without `https://` or a path.

## 5. Configure Supabase and Google OAuth

1. In **Supabase → Authentication → URL Configuration** set:
   - **Site URL:** `https://<VERCEL_PRODUCTION_DOMAIN>/`
   - **Redirect URLs:** add these exact entries:
     - `https://<VERCEL_PRODUCTION_DOMAIN>/`
     - `https://<VERCEL_PRODUCTION_DOMAIN>/account`
     - `https://<VERCEL_PRODUCTION_DOMAIN>/update-password`
   - Keep the exact local URL only if local OAuth testing is still needed.
2. In **Google Cloud Console → APIs & Services → Credentials**, open the Web OAuth
   client and add:
   - **Authorized JavaScript origin:** `https://<VERCEL_PRODUCTION_DOMAIN>`
   - **Authorized redirect URI:**
     `https://<PROJECT_REF>.supabase.co/auth/v1/callback`
3. In **Supabase → Authentication → Sign In / Providers → Google**, enable Google and
   save the Google client ID and client secret there.
4. If Google's consent screen is in testing mode, add the intended Google test users.
5. Confirm email sign-in and signups are enabled, email confirmation has the intended
   setting, and the password minimum matches the frontend build variable. Do not add a
   paid SMTP service for this demonstration.

Google redirects to the Supabase callback. Supabase then redirects to the Vercel URL.
There is no Research Guard OAuth callback API route. The hosted project already exposes
JWKS, so no signing-key dashboard change is required for this deployment.

## 6. Verify the hosted journey

Perform these checks in order with public or synthetic text only:

1. Open the Vercel production URL while signed out. Create the public demonstration,
   inspect evidence, and export JSON.
2. Open browser developer tools → Network. Confirm API requests go to the exact Render
   HTTPS origin and return no CORS or trusted-host errors.
3. Open `/login` and `/signup`. Sign in with Google from each page, reload to confirm
   session restoration, then sign out.
   Also cancel one Google sign-in attempt and confirm the app remains signed out.
4. Open `/chat`, confirm only configured providers show Available, send one public or
   synthetic question, ask one follow-up, and verify the reply names the actual provider
   and model and says it is not evidence-checked. Check browser Network and confirm the
   provider key is absent. Do not enable fallback until each candidate account has been
   confirmed free/no-billing.
5. Create one disposable email/password account, follow its confirmation email to
   `/account`, request a password reset, and follow the recovery link to
   `/update-password`. If the Free project's default sender cannot deliver to that
   address, record this check as blocked rather than changing to a paid service.
6. Sign in again. Create a live review, edit a claim, retrieve sources, run assessment,
   make a decision, explicitly save, reload/open it, export it, and delete a disposable
   record.
7. Repeat saved-review and optional-profile access with a second test user. Each account must list
   only its own records; a copied record UUID from the other user must return not found.
8. Inspect Render logs for errors, but do not log or paste access tokens, review bodies,
   the Gemini key, or Google secrets.

Gemini is still a separate external gate. A `503 high demand` response is an unavailable
state, not an authentication failure, and must not trigger billing, a paid model, or a
demonstration substitution.

## Free-plan behavior to expect

Render Free spins down after 15 minutes without inbound traffic and may take about one
minute to wake. Its filesystem and this application's process memory are ephemeral.
Therefore every unsaved draft can disappear on sleep, restart, or redeploy; only an
explicitly saved Supabase record is durable. Render Free is suitable for this competition
preview, not a production availability claim.

Vercel Hobby is restricted to personal, non-commercial use. Keep the frontend static;
the FastAPI service belongs on Render under the current architecture. If either free
quota is exhausted, leave the feature unavailable until quota resets. Do not attach
billing or silently move to a paid service.

## Official documentation checked on 2026-09-19

- [Render FastAPI deployment](https://render.com/docs/deploy-fastapi)
- [Render web services and port binding](https://render.com/docs/web-services)
- [Render Free limitations](https://render.com/docs/free)
- [Render Python version selection](https://render.com/docs/python-version)
- [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite)
- [Vercel environment variables](https://vercel.com/docs/environment-variables)
- [Vercel Hobby terms and limits](https://vercel.com/docs/plans/hobby)
- [Supabase redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)
- [Supabase Google login](https://supabase.com/docs/guides/auth/social-login/auth-google)
