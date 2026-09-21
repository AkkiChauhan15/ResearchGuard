-- Owner-scoped AI chat history, schema version 1.
-- Chats are separate from evidence reviews and remain explicitly labeled unverified.

create table if not exists public.saved_chats (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  schema_version integer not null default 1,
  revision bigint not null default 1,
  title text not null,
  message_count integer not null,
  last_provider text not null,
  last_model text not null,
  record jsonb not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint saved_chats_schema_version check (schema_version = 1),
  constraint saved_chats_revision_positive check (revision >= 1),
  constraint saved_chats_title_length check (char_length(title) between 1 and 160),
  constraint saved_chats_message_count check (message_count between 2 and 24 and message_count % 2 = 0),
  constraint saved_chats_provider_length check (char_length(last_provider) between 1 and 40),
  constraint saved_chats_model_length check (char_length(last_model) between 1 and 120),
  constraint saved_chats_record_object check (jsonb_typeof(record) = 'object'),
  constraint saved_chats_record_messages check (jsonb_typeof(record -> 'messages') = 'array'),
  constraint saved_chats_record_count check (jsonb_array_length(record -> 'messages') = message_count),
  constraint saved_chats_record_size check (octet_length(record::text) <= 250000)
);

create index if not exists saved_chats_owner_updated_idx
  on public.saved_chats (owner_id, updated_at desc);

create or replace function public.protect_saved_chat_identity()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.id is distinct from old.id
     or new.owner_id is distinct from old.owner_id
     or new.schema_version is distinct from old.schema_version
     or new.created_at is distinct from old.created_at then
    raise exception 'saved chat identity and ownership are immutable' using errcode = '42501';
  end if;
  new.revision := old.revision + 1;
  new.updated_at := timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists protect_saved_chat_identity on public.saved_chats;
create trigger protect_saved_chat_identity
before update on public.saved_chats
for each row execute function public.protect_saved_chat_identity();

alter table public.saved_chats enable row level security;
alter table public.saved_chats force row level security;

revoke all on table public.saved_chats from anon, authenticated;
grant select on table public.saved_chats to authenticated;
grant insert (schema_version, title, message_count, last_provider, last_model, record)
  on table public.saved_chats to authenticated;
grant update (title, message_count, last_provider, last_model, record)
  on table public.saved_chats to authenticated;
grant delete on table public.saved_chats to authenticated;

drop policy if exists "saved_chats_select_owner" on public.saved_chats;
create policy "saved_chats_select_owner"
on public.saved_chats for select
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

drop policy if exists "saved_chats_insert_owner" on public.saved_chats;
create policy "saved_chats_insert_owner"
on public.saved_chats for insert
to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

drop policy if exists "saved_chats_update_owner" on public.saved_chats;
create policy "saved_chats_update_owner"
on public.saved_chats for update
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

drop policy if exists "saved_chats_delete_owner" on public.saved_chats;
create policy "saved_chats_delete_owner"
on public.saved_chats for delete
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

comment on table public.saved_chats is
  'Authenticated user-owned AI chat history. Unverified model output; no Google profile data.';
