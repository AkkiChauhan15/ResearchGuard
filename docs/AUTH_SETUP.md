# Supabase Free sign-in and account setup

The React SPA uses the existing Supabase JavaScript client for Google OAuth and
email/password accounts. Google uses the browser implicit OAuth flow supported by
Supabase for client-only applications; there is no application callback route.
FastAPI accepts the resulting access token and
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
VITE_SUPABASE_PASSWORD_MIN_LENGTH=6
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
   `http://127.0.0.1:5173/` and add these exact Redirect URLs:
   - `http://127.0.0.1:5173/`
   - `http://127.0.0.1:5173/account`
   - `http://127.0.0.1:5173/update-password`
   The root is **Supabase's redirect back to Research Guard** after Google OAuth.
   `/account` is the email-confirmation destination and `/update-password` is the
   password-recovery destination.
6. If the Google consent screen is still in test mode, add the intended test account.
   Do not publish or change billing merely to test this local application.

The client refuses redirect destinations outside the explicit local origins. To test
the FastAPI-served production build at `http://127.0.0.1:8000/`, add that exact origin
to Google's JavaScript origins and that exact URL to Supabase's Redirect URLs. The code
already permits ports 5173 and 8000 on `127.0.0.1` and `localhost`; configure only the
one actually used. Add its `/account` and `/update-password` paths when testing email
confirmation and password recovery. Do not add wildcards or a public URL.

## Email/password settings verified and still to check

On 2026-09-19 the project's public Auth settings endpoint reported that email sign-in,
Google sign-in and new registrations are enabled, and that email confirmation is
required. The UI therefore exposes email/password fields and shows the confirmation
step after registration. This read-only check did not reveal the dashboard's exact
password policy or prove that an email can be delivered.

In Supabase Authentication settings:

1. Confirm **Allow new users to sign up** and the email provider remain enabled.
2. Keep **Confirm email** enabled unless the project owner intentionally changes the
   account policy. The page reads the current public capability flags.
3. Check the displayed minimum password length. If it is not 6, set
   `VITE_SUPABASE_PASSWORD_MIN_LENGTH` to the same value before building the frontend.
   Supabase remains authoritative and rejects any stronger unmet policy.
4. Confirm the three exact local redirect URLs above. The app rejects external `next`
   values and never forwards arbitrary browser-supplied origins.
5. Test registration and recovery with an address that the project's current mail
   service permits. Supabase's default mail sender is rate-limited and intended for
   trial use; if delivery is restricted, leave the live email check blocked. Do not add
   a paid mail service or disable confirmation merely to make the test pass.

The implemented routes are `/login`, `/signup`, `/forgot-password`,
`/update-password`, and `/account`. `/account` is the post-authentication profile page.
The public demonstration remains available from `/` and from both sign-in pages.

## Hosted deployment values

Free-tier competition deployment preparation is now authorized. The application accepts
one exact hosted OAuth return origin only when `VITE_APPLICATION_ORIGIN` is present in
that production build. Follow `DEPLOYMENT.md`, then replace these placeholders:

| Dashboard field | Placeholder |
| --- | --- |
| Supabase project reference | `<PROJECT_REF>` |
| Application origin | `<APP_ORIGIN>` such as `https://app.example.org` |
| Google Authorized JavaScript origin | `<APP_ORIGIN>` without a trailing path |
| Google Authorized redirect URI | `https://<PROJECT_REF>.supabase.co/auth/v1/callback` |
| Supabase Site URL | `<APP_ORIGIN>/` |
| Supabase allowed Redirect URLs | `<APP_ORIGIN>/`, `<APP_ORIGIN>/account`, and `<APP_ORIGIN>/update-password`; no wildcard |

The Google client ID and client secret are dashboard-only values. Do not create
environment-variable placeholders for the client secret in the frontend or repository.
Set the same exact origin in Render's `RESEARCHGUARD_FRONTEND_ORIGINS`. Merely filling
these fields does not prove the deployed OAuth round trip works; complete the hosted
checklist in `DEPLOYMENT.md`.

## Start and verify locally

```sh
.venv/bin/python -m researchguard.server --port 8000
npm run dev --prefix frontend -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173/login`. Verify Google sign-in returns to the requested
internal page, the header
shows the account, a live review can be created, page reload restores the session, and
Sign out returns to the logged-out state. Also cancel once at Google and verify the app
shows cancellation without creating a live review. An OAuth callback error must remain
an error and must never open demo content as a substitute.

Then create one disposable email/password account. Confirm the email link reaches
`/account`, request a reset from `/forgot-password`, and confirm the recovery link
reaches `/update-password` with a valid session. An expired or malformed link must show
the missing/expired recovery state. These are live manual checks; the automated browser
test does not send OAuth or account emails.

The public demo works with no token. Live review creation, live review reads/mutations,
model requests, and private saved-review routes require a verified user. The
temporary store binds each live review to both its browser draft session and the
verified JWT subject. Follow `PERSISTENCE_SETUP.md` before expecting saved-review
operations to work; authentication alone does not create the database table.

Official references checked on 2026-09-19:

- [Supabase Google social login](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [JavaScript `signInWithOAuth`](https://supabase.com/docs/reference/javascript/auth-signinwithoauth)
- [Supabase redirect URL allow list](https://supabase.com/docs/guides/auth/redirect-urls)
- [Supabase JWT claims and JWKS](https://supabase.com/docs/guides/auth/jwts)
- [Supabase JWT signing keys](https://supabase.com/docs/guides/auth/signing-keys)
- [Supabase password authentication](https://supabase.com/docs/guides/auth/passwords)
- [JavaScript password recovery](https://supabase.com/docs/reference/javascript/auth-resetpasswordforemail)
- [JavaScript auth-state events](https://supabase.com/docs/reference/javascript/auth-onauthstatechange)
