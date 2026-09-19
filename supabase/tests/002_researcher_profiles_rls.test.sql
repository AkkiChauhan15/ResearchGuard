begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(12);

insert into auth.users (
  id, instance_id, aud, role, email, encrypted_password,
  email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
  created_at, updated_at
) values
  (
    '11111111-1111-4111-8111-111111111111',
    '00000000-0000-0000-0000-000000000000',
    'authenticated', 'authenticated', 'profile-user-1@example.test', '', now(),
    '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb, now(), now()
  ),
  (
    '22222222-2222-4222-8222-222222222222',
    '00000000-0000-0000-0000-000000000000',
    'authenticated', 'authenticated', 'profile-user-2@example.test', '', now(),
    '{"provider":"google","providers":["google"]}'::jsonb, '{}'::jsonb, now(), now()
  );

select ok(
  (select relrowsecurity and relforcerowsecurity
   from pg_class where oid = 'public.researcher_profiles'::regclass),
  'researcher_profiles has RLS enabled and forced'
);

select ok(
  not has_table_privilege('anon', 'public.researcher_profiles', 'SELECT'),
  'anonymous clients cannot read profiles'
);

select ok(
  not has_column_privilege('authenticated', 'public.researcher_profiles', 'user_id', 'INSERT'),
  'authenticated clients cannot assign profile ownership'
);

select ok(
  not has_column_privilege('authenticated', 'public.researcher_profiles', 'user_id', 'UPDATE'),
  'authenticated clients cannot update profile ownership'
);

set local role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);

insert into public.researcher_profiles (full_name, research_role)
values ('Researcher One', 'PhD researcher');

select results_eq(
  $$select user_id from public.researcher_profiles$$,
  array['11111111-1111-4111-8111-111111111111'::uuid],
  'profile owner is derived from auth.uid()'
);

select lives_ok(
  $$
    insert into public.researcher_profiles (full_name, research_field)
    values ('Researcher One Revised', 'Cell biology')
    on conflict (user_id) do update
    set full_name = excluded.full_name, research_field = excluded.research_field
  $$,
  'profile creation is safe to repeat for one user'
);

select results_eq(
  $$select full_name from public.researcher_profiles$$,
  array['Researcher One Revised'::text],
  'repeated save updates the owner profile'
);

select throws_ok(
  $$update public.researcher_profiles set user_id = '22222222-2222-4222-8222-222222222222'$$,
  '42501', null,
  'profile owner cannot be changed'
);

reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub', '22222222-2222-4222-8222-222222222222', true);

select results_eq(
  $$select count(*) from public.researcher_profiles$$,
  array[0::bigint],
  'another user cannot read the first profile'
);

select results_eq(
  $$update public.researcher_profiles set research_field = 'Forged change' returning user_id$$,
  array[]::uuid[],
  'another user cannot update the first profile'
);

insert into public.researcher_profiles (
  full_name, research_role, research_field, institution
) values (null, null, null, null);
select results_eq(
  $$select user_id from public.researcher_profiles$$,
  array['22222222-2222-4222-8222-222222222222'::uuid],
  'optional profile details can all be skipped'
);

reset role;
set local role anon;
select throws_ok(
  $$select count(*) from public.researcher_profiles$$,
  '42501', null,
  'signed-out clients cannot read profiles'
);

reset role;
select * from finish();
rollback;
