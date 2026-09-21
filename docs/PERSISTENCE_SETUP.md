# Supabase saved-review persistence setup

Phase G stores only reviews that a signed-in researcher explicitly saves. Unsaved
reviews remain in the one-hour process-local draft store. The table stores the canonical
review plus owner UUID, schema version, revision, title and timestamps. It does not add
Google profile data.

The account-page work adds a separate minimal table for optional researcher profile
fields. It stores full name, role, research field and institution only; it does not
duplicate email addresses or store review content. Every field may be left blank.

Authenticated AI chat uses a third, separate table, `saved_chats`. Successful complete
turns save automatically at the user's request; each assistant message keeps its actual
provider/model and fallback flag. Chat PDFs are generated from this canonical record and
remain labeled as unverified model output. No Google profile data is copied into it.

## 1. Copy the two public project values

In the intended Supabase **Free** project, open the Connect dialog or project API-key
settings and copy:

- Project URL: `https://<PROJECT_REF>.supabase.co`
- Publishable key: an `sb_publishable_...` value

Set both in the backend shell:

```sh
export SUPABASE_URL='https://<PROJECT_REF>.supabase.co'
export SUPABASE_PUBLISHABLE_KEY='sb_publishable_replace_with_project_value'
export RESEARCHGUARD_PERSISTENCE_TIMEOUT_SECONDS=10
```

Use the same URL and publishable key in `frontend/.env.local` as documented in
`AUTH_SETUP.md`. Do not use or share an `sb_secret_...`, legacy `service_role` key,
database password, JWT private key, or Google client secret. The backend deliberately
uses each user's access token so RLS remains active.

## 2. Apply the versioned migrations

The saved-review migration already present in the linked history is:

`supabase/migrations/202609190001_create_saved_reviews.sql`

Use the Supabase CLI migration workflow so the remote migration history stays aligned:

```sh
supabase init
supabase login
supabase link
supabase migration list
supabase db push
supabase migration list
```

The new optional-profile migration is:

`supabase/migrations/202609190002_create_researcher_profiles.sql`

The saved-chat migration prepared on 2026-09-21 is:

`supabase/migrations/202609210001_create_saved_chats.sql`

Choose the already-created Free project when `supabase link` prompts. On 2026-09-19, a
fresh linked query confirmed both `202609190001` and `202609190002` in remote migration
history. Do **not** push either migration again. Migration `202609210001` is prepared in
this repository but has not been confirmed in hosted migration history. Review the push
preview, apply it with `supabase db push`, and confirm that exact version in the final
`supabase migration list`. Do not
create the table manually in the Dashboard Table Editor or SQL Editor; current Supabase
guidance warns that remote manual schema changes bypass migration history.

The migration creates `public.saved_reviews`, enables and forces RLS, removes anonymous
privileges, grants only the required authenticated columns, and adds separate owner-only
SELECT, INSERT, UPDATE and DELETE policies. `owner_id` defaults to `auth.uid()` and is
not insertable or updateable by the authenticated role. The record identity, demo/live
mode and schema version are immutable, and saved canonical JSON is limited to 5 MB.

The profile migration creates `public.researcher_profiles`, derives `user_id` from
`auth.uid()`, grants authenticated clients only the four optional data columns, and
enforces owner-only SELECT/INSERT/UPDATE with RLS. The owner and creation timestamp are
immutable. There is no browser profile-delete operation and no anonymous access.

The chat migration enables and forces RLS, derives `owner_id` from `auth.uid()`, omits
owner columns from authenticated insert/update grants, and applies owner-only SELECT,
INSERT, UPDATE and DELETE policies. A trigger prevents ownership/identity changes and
increments the revision for stale-update protection. Records are capped at 24 messages
and 250,000 serialized bytes.

## 3. Optional local database policy test

The saved-review and profile pgTAP files are under `supabase/tests/`. Start the local
Supabase stack and run:

```sh
supabase test db
.venv/bin/python -m scripts.verify_supabase_local
```

On 2026-09-19 the policy suite passed 16/16 checks. The second command also passed with
two disposable local identities, real asymmetric access tokens, PostgREST and FastAPI.
Those results predate the new profile and chat migrations. Their source contracts pass
automated tests, but the new chat pgTAP file must be run after the local stack applies
`202609210001`.
This does not replace the Google OAuth/hosted two-user browser check below.

## 4. Verify with two accounts after Auth is configured

Use only public or synthetic review content.

1. Sign in as test user A, open the public demo, choose **Save this review**, and confirm
   it appears under **Your saved reviews**.
2. Open it, make a researcher decision or a material claim edit, and choose **Update
   saved copy**. Confirm a claim edit has no old assessment/current evidence link and
   resets the decision to pending.
3. Sign out. Confirm the saved list and private working copy disappear while the public
   demo remains available.
4. Sign in as test user B. Confirm user A's record cannot be listed, opened, updated,
   exported or deleted, even if its saved UUID is copied into a request.
5. Save a separate record as user B. Sign back in as user A and confirm only A's record
   appears.
6. Open the same saved record in two browser sessions. Update one, then try the older
   revision in the other. Confirm HTTP 409 is shown and the older local review remains
   open rather than being overwritten.
7. Export the saved JSON and TXT and compare the JSON with the opened canonical review,
   including mode, source IDs/passages/locations/access levels, model identifiers,
   original suggestions and researcher decisions.
8. Delete the saved record and confirm it no longer lists or opens.

Then verify chat history:

1. As user A, open `/chat`, send public/synthetic text, reload, and reopen the saved
   conversation. Continue it and confirm its revision/message count increase.
2. Export PDF and confirm it contains all messages, timestamps, actual provider/model,
   fallback status and the `not evidence-checked` warning.
3. As user B, confirm user A's UUID cannot be listed, opened, exported, continued or
   deleted. Confirm signed-out requests receive HTTP 401.
4. Continue the same chat from two browser sessions; the stale revision must receive
   HTTP 409 and must not lose or silently overwrite the local conversation.
5. Delete the chat as its owner and confirm it disappears after reload.

For the optional profile, sign in as each user and open `/account`. Confirm blank fields
can be saved, repeat saves update one row, and user B cannot select or update user A's
row through PostgREST. Confirm no email address is stored in `researcher_profiles`.

If Supabase is paused, unreachable or a migration is absent, the application shows a
clear persistence error. Evidence reviews retain their local working copy. Chat does not
present a model response as saved unless persistence confirms the canonical turn. The
application does not switch to a privileged key, paid service, model fallback or demo
substitution.

Official references checked through 2026-09-21:

- [Supabase database migrations](https://supabase.com/docs/guides/deployment/database-migrations)
- [Supabase row-level security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase advanced pgTAP testing](https://supabase.com/docs/guides/local-development/testing/pgtap-extended)
- [Supabase API keys](https://supabase.com/docs/guides/getting-started/api-keys)
- [ReportLab PDF generation](https://docs.reportlab.com/reportlab/userguide/ch2_graphics/)
