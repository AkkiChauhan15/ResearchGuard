-- Standalone local RLS verification. Run with: supabase test db
-- The transaction rolls back both test identities and records.
begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(16);

insert into auth.users (
  id, instance_id, aud, role, email, encrypted_password,
  email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
  created_at, updated_at
) values
  (
    '11111111-1111-4111-8111-111111111111',
    '00000000-0000-0000-0000-000000000000',
    'authenticated', 'authenticated', 'phase-g-user-1@example.test', '', now(),
    '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb, now(), now()
  ),
  (
    '22222222-2222-4222-8222-222222222222',
    '00000000-0000-0000-0000-000000000000',
    'authenticated', 'authenticated', 'phase-g-user-2@example.test', '', now(),
    '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb, now(), now()
  );

select ok(
  (select relrowsecurity and relforcerowsecurity
   from pg_class where oid = 'public.saved_reviews'::regclass),
  'saved_reviews has RLS enabled and forced'
);

select ok(
  not has_table_privilege('anon', 'public.saved_reviews', 'SELECT'),
  'anonymous clients have no saved-review read privilege'
);

select ok(
  not has_column_privilege('authenticated', 'public.saved_reviews', 'owner_id', 'INSERT'),
  'authenticated clients cannot assign owner_id'
);

select ok(
  not has_column_privilege('authenticated', 'public.saved_reviews', 'owner_id', 'UPDATE'),
  'authenticated clients cannot update owner_id'
);

set local role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);

insert into public.saved_reviews (review_id, schema_version, mode, title, record)
values (
  'review_11111111111111111111111111111111', 1, 'demo', 'User one record',
  '{"review_id":"review_11111111111111111111111111111111","mode":"demo"}'::jsonb
);

select results_eq(
  $$select owner_id from public.saved_reviews$$,
  array['11111111-1111-4111-8111-111111111111'::uuid],
  'owner is derived from the authenticated user'
);

select results_eq(
  $$select count(*) from public.saved_reviews$$,
  array[1::bigint],
  'user one sees their own record'
);

select throws_ok(
  $$
    insert into public.saved_reviews (owner_id, review_id, schema_version, mode, title, record)
    values (
      '22222222-2222-4222-8222-222222222222',
      'review_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 1, 'demo', 'Forged owner',
      '{"review_id":"review_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","mode":"demo"}'::jsonb
    )
  $$,
  '42501', null,
  'user one cannot forge owner_id'
);

reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub', '22222222-2222-4222-8222-222222222222', true);

select results_eq(
  $$select count(*) from public.saved_reviews$$,
  array[0::bigint],
  'user two cannot read user one records'
);

select results_eq(
  $$
    update public.saved_reviews
    set title = 'Cross-user change'
    where review_id = 'review_11111111111111111111111111111111'
    returning id
  $$,
  array[]::uuid[],
  'user two cannot update user one records'
);

select results_eq(
  $$
    delete from public.saved_reviews
    where review_id = 'review_11111111111111111111111111111111'
    returning id
  $$,
  array[]::uuid[],
  'user two cannot delete user one records'
);

select lives_ok(
  $$
    insert into public.saved_reviews (review_id, schema_version, mode, title, record)
    values (
      'review_22222222222222222222222222222222', 1, 'live', 'User two record',
      '{"review_id":"review_22222222222222222222222222222222","mode":"live"}'::jsonb
    )
  $$,
  'user two can create their own record'
);

select results_eq(
  $$select owner_id from public.saved_reviews$$,
  array['22222222-2222-4222-8222-222222222222'::uuid],
  'user two sees only their own record'
);

reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);

select results_eq(
  $$select review_id from public.saved_reviews order by review_id$$,
  array['review_11111111111111111111111111111111'::text],
  'user one still sees only their own record'
);

update public.saved_reviews
set title = 'User one revised title'
where review_id = 'review_11111111111111111111111111111111';

select results_eq(
  $$select revision from public.saved_reviews where review_id = 'review_11111111111111111111111111111111'$$,
  array[2::bigint],
  'an owner update increments the stored revision'
);

select lives_ok(
  $$delete from public.saved_reviews where review_id = 'review_11111111111111111111111111111111'$$,
  'an owner can delete their record'
);

reset role;
set local role anon;
select throws_ok(
  $$select count(*) from public.saved_reviews$$,
  '42501', null,
  'signed-out clients cannot read saved reviews'
);

reset role;
select * from finish();
rollback;
