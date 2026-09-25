begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(14);

insert into auth.users (
  id, instance_id, aud, role, email, encrypted_password,
  email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
  created_at, updated_at
) values
  ('11111111-1111-4111-8111-111111111111', '00000000-0000-0000-0000-000000000000',
   'authenticated', 'authenticated', 'phase-three-user-1@example.test', '', now(),
   '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb, now(), now()),
  ('22222222-2222-4222-8222-222222222222', '00000000-0000-0000-0000-000000000000',
   'authenticated', 'authenticated', 'phase-three-user-2@example.test', '', now(),
   '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb, now(), now());

select ok(
  (select relrowsecurity and relforcerowsecurity from pg_class
   where oid = 'public.multi_provider_assessments'::regclass),
  'multi_provider_assessments has RLS enabled and forced'
);
select ok(not has_table_privilege('anon', 'public.multi_provider_assessments', 'SELECT'),
  'signed-out clients have no provider-assessment read privilege');
select ok(not has_column_privilege('authenticated', 'public.multi_provider_assessments', 'owner_id', 'INSERT'),
  'authenticated clients cannot assign provider-assessment owner_id');
select ok(not has_column_privilege('authenticated', 'public.multi_provider_assessments', 'owner_id', 'UPDATE'),
  'authenticated clients cannot change provider-assessment owner_id');

set local role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);
insert into public.saved_reviews (review_id, schema_version, mode, title, record)
values (
  'review_11111111111111111111111111111111', 1, 'live', 'Provider comparison',
  '{"review_id":"review_11111111111111111111111111111111","mode":"live","claims":[{"claim_id":"claim_11111111111111111111111111111111","provider_assessments":[{"provider":"groq","model":"fixture-primary","is_primary":true,"label":"supports","confidence":"medium","quote_check_passed":true,"source_ids":["src_fixture"],"created_at":"2026-09-25T00:00:00+00:00"},{"provider":"openrouter","model":"fixture-second","is_primary":false,"label":"uncertain","confidence":"low","quote_check_passed":true,"source_ids":["src_fixture"],"created_at":"2026-09-25T00:01:00+00:00"}]}]}'::jsonb
);

select results_eq($$select count(*) from public.multi_provider_assessments$$,
  array[2::bigint], 'saved canonical list synchronizes two provider assessments');
select results_eq($$select count(*) from public.multi_provider_assessments where is_primary$$,
  array[1::bigint], 'exactly one primary result is synchronized');
select results_eq($$select distinct owner_id from public.multi_provider_assessments$$,
  array['11111111-1111-4111-8111-111111111111'::uuid], 'owner is derived from the saved review');

reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub', '22222222-2222-4222-8222-222222222222', true);
select results_eq($$select count(*) from public.multi_provider_assessments$$,
  array[0::bigint], 'user two cannot read user one provider assessments');
select results_eq($$update public.multi_provider_assessments set label = 'insufficient' returning id$$,
  array[]::uuid[], 'user two cannot update user one provider assessments');
select results_eq($$delete from public.multi_provider_assessments returning id$$,
  array[]::uuid[], 'user two cannot delete user one provider assessments');
select throws_ok(
  $$insert into public.multi_provider_assessments (owner_id, saved_review_id, review_id, claim_id, provider, model, is_primary, label, confidence, quote_check_passed)
    values ('11111111-1111-4111-8111-111111111111', gen_random_uuid(), 'review_22222222222222222222222222222222', 'claim_22222222222222222222222222222222', 'gemini', 'forged', true, 'supports', 'high', true)$$,
  '42501', null, 'user two cannot forge provider-assessment owner_id');

reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);
select lives_ok($$update public.multi_provider_assessments set confidence = 'high' where provider = 'openrouter'$$,
  'owner can update an allowed comparison field');
select lives_ok($$delete from public.saved_reviews$$,
  'owner can delete the saved review and cascade its provider assessments');

reset role;
set local role anon;
select throws_ok($$select count(*) from public.multi_provider_assessments$$,
  '42501', null, 'signed-out clients cannot read provider assessments');

reset role;
select * from finish();
rollback;
