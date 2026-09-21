-- Standalone local owner-isolation checks for saved chat history.
begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(15);

insert into auth.users (
  id, instance_id, aud, role, email, encrypted_password,
  email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
  created_at, updated_at
) values
  ('33333333-3333-4333-8333-333333333333', '00000000-0000-0000-0000-000000000000',
   'authenticated', 'authenticated', 'chat-user-1@example.test', '', now(),
   '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb, now(), now()),
  ('44444444-4444-4444-8444-444444444444', '00000000-0000-0000-0000-000000000000',
   'authenticated', 'authenticated', 'chat-user-2@example.test', '', now(),
   '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb, now(), now());

select ok(
  (select relrowsecurity and relforcerowsecurity from pg_class where oid = 'public.saved_chats'::regclass),
  'saved_chats has RLS enabled and forced'
);
select ok(not has_table_privilege('anon', 'public.saved_chats', 'SELECT'), 'signed-out clients have no saved-chat read privilege');
select ok(not has_column_privilege('authenticated', 'public.saved_chats', 'owner_id', 'INSERT'), 'authenticated clients cannot assign chat owner_id');
select ok(not has_column_privilege('authenticated', 'public.saved_chats', 'owner_id', 'UPDATE'), 'authenticated clients cannot change chat owner_id');

set local role authenticated;
select set_config('request.jwt.claim.sub', '33333333-3333-4333-8333-333333333333', true);

insert into public.saved_chats (title, message_count, last_provider, last_model, record)
values ('User one chat', 2, 'groq', 'fixture-model',
  '{"messages":[{"role":"user"},{"role":"assistant"}]}'::jsonb);

select results_eq($$select owner_id from public.saved_chats$$,
  array['33333333-3333-4333-8333-333333333333'::uuid], 'chat owner is derived from auth.uid()');
select results_eq($$select count(*) from public.saved_chats$$, array[1::bigint], 'user one sees their chat');
select throws_ok(
  $$insert into public.saved_chats (owner_id, title, message_count, last_provider, last_model, record)
    values ('44444444-4444-4444-8444-444444444444', 'Forged', 2, 'groq', 'model',
    '{"messages":[{"role":"user"},{"role":"assistant"}]}'::jsonb)$$,
  '42501', null, 'user one cannot forge chat owner_id');

reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub', '44444444-4444-4444-8444-444444444444', true);
select results_eq($$select count(*) from public.saved_chats$$, array[0::bigint], 'user two cannot read user one chats');
select results_eq($$update public.saved_chats set title = 'Cross-user edit' returning id$$, array[]::uuid[], 'user two cannot update user one chats');
select results_eq($$delete from public.saved_chats returning id$$, array[]::uuid[], 'user two cannot delete user one chats');
select lives_ok(
  $$insert into public.saved_chats (title, message_count, last_provider, last_model, record)
    values ('User two chat', 2, 'openrouter', 'free-model',
    '{"messages":[{"role":"user"},{"role":"assistant"}]}'::jsonb)$$,
  'user two can create a chat');

reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub', '33333333-3333-4333-8333-333333333333', true);
select results_eq($$select title from public.saved_chats$$, array['User one chat'::text], 'user one still sees only their chat');
update public.saved_chats set title = 'User one updated' where title = 'User one chat';
select results_eq($$select revision from public.saved_chats$$, array[2::bigint], 'owner update increments chat revision');
select lives_ok($$delete from public.saved_chats$$, 'owner can delete their chat');

reset role;
set local role anon;
select throws_ok($$select count(*) from public.saved_chats$$, '42501', null, 'signed-out clients cannot read saved chats');

reset role;
select * from finish();
rollback;
