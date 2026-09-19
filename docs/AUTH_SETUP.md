# Supabase Free Google sign-in setup

Phase F uses the Supabase JavaScript client directly in the React SPA. It uses the
browser implicit OAuth flow supported by Supabase for client-only applications; there
is no application callback route. FastAPI accepts the resulting access token and
verifies its asymmetric signature against the project's JWKS, exact issuer, expiry,
`authenticated` audience, role, and UUID subject.

## Values used by the local application

Replace `<PROJECT_REF>` with the reference shown in the intended Supabase Free project.
The primary development application address is exactly `http://127.0.0.1:5173/`.

Backend environment:

```sh
export SUPABASE_URL='https://<PROJECT_REF>.supabase.co'
export SUPABASE_PUBLISHABLE_KEY='sb_publishable_replace_with_project_value'
```

Frontend `frontend/.env.local`:

```dotenv
VITE_SUPABASE_URL=https://<PROJECT_REF>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_replace_with_project_value
```

Use the project's current `sb_publishable_...` key. It is a public browser credential
and does not authorize privileged database access. Never put the Google
client secret, Supabase secret/service-role key, JWT signing private key, or Gemini key
in a `VITE_` variable, this file, source control, exports, or chat.

## Configure Google and Supabase

1. In Supabase Dashboard, confirm the project is on the Free plan. In Authentication
   signing-key settings, use a supported asymmetric signing key (ES256 or RS256). The
   backend deliberately does not accept the legacy shared HS256 JWT secret.
2. In Google Cloud Console, create a Web application OAuth client. Add this Authorized
   JavaScript origin: `http://127.0.0.1:5173`.
3. Add this **Google Authorized redirect URI** exactly:
   `https://<PROJECT_REF>.supabase.co/auth/v1/callback`.
   This is Google's redirect to **Supabase Auth**, not a Research Guard route.
4. In Supabase Authentication → Providers → Google, enable Google and store the Google
   client ID and client secret in the dashboard. They never enter frontend code.
5. In Supabase Authentication → URL Configuration, set Site URL to
   `http://127.0.0.1:5173/` and add exactly
   `http://127.0.0.1:5173/` to Redirect URLs. This is **Supabase's redirect back to
   Research Guard** after it processes Google's response.
6. If the Google consent screen is still in test mode, add the intended test account.
   Do not publish or change billing merely to test this local application.

The client refuses redirect destinations outside the explicit local origins. To test
the FastAPI-served production build at `http://127.0.0.1:8000/`, add that exact origin
to Google's JavaScript origins and that exact URL to Supabase's Redirect URLs. The code
already permits ports 5173 and 8000 on `127.0.0.1` and `localhost`; configure only the
one actually used. Do not add wildcards or a public URL.

## Placeholders for a later authorized deployment

No public deployment is currently authorized, and the application intentionally
rejects public OAuth return origins. When a later phase supplies and authorizes a real
application origin, replace these placeholders in the provider dashboards:

| Dashboard field | Placeholder |
| --- | --- |
| Supabase project reference | `<PROJECT_REF>` |
| Application origin | `<APP_ORIGIN>` such as `https://app.example.org` |
| Google Authorized JavaScript origin | `<APP_ORIGIN>` without a trailing path |
| Google Authorized redirect URI | `https://<PROJECT_REF>.supabase.co/auth/v1/callback` |
| Supabase Site URL | `<APP_ORIGIN>/` |
| Supabase allowed Redirect URL | `<APP_ORIGIN>/` exactly; no wildcard |

The Google client ID and client secret are dashboard-only values. Do not create
environment-variable placeholders for the client secret in the frontend or repository.
Before using `<APP_ORIGIN>`, a later authorized phase must add it to the application's
validated origin/CORS/CSP configuration and test the deployed round trip. Merely filling
these dashboard fields does not make the current local-only build deployment-ready.

## Start and verify locally

```sh
.venv/bin/python -m researchguard.server --port 8000
npm run dev --prefix frontend -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173/`. Verify Google sign-in returns to that page, the header
shows the account, a live review can be created, page reload restores the session, and
Sign out returns to the logged-out state. Also cancel once at Google and verify the app
shows cancellation without creating a live review. An OAuth callback error must remain
an error and must never open demo content as a substitute.

The public demo works with no token. Live review creation, live review reads/mutations,
model requests, and private saved-review routes require a verified user. The
temporary store binds each live review to both its browser draft session and the
verified JWT subject. Follow `PERSISTENCE_SETUP.md` before expecting saved-review
operations to work; authentication alone does not create the database table.

Official references checked on 2026-09-18:

- [Supabase Google social login](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [JavaScript `signInWithOAuth`](https://supabase.com/docs/reference/javascript/auth-signinwithoauth)
- [Supabase redirect URL allow list](https://supabase.com/docs/guides/auth/redirect-urls)
- [Supabase JWT claims and JWKS](https://supabase.com/docs/guides/auth/jwts)
- [Supabase JWT signing keys](https://supabase.com/docs/guides/auth/signing-keys)
