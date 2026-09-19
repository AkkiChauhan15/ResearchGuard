-- Research Guard AI saved-review envelope, schema version 1.
-- The canonical Review remains in record; database metadata is outside that schema.

create table if not exists public.saved_reviews (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  review_id text not null,
  schema_version integer not null default 1,
  revision bigint not null default 1,
  mode text not null,
  title text not null,
  record jsonb not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint saved_reviews_review_id_format check (review_id ~ '^review_[0-9a-f]{32}$'),
  constraint saved_reviews_schema_version check (schema_version = 1),
  constraint saved_reviews_revision_positive check (revision >= 1),
  constraint saved_reviews_mode check (mode in ('demo', 'live')),
  constraint saved_reviews_title_length check (char_length(title) between 1 and 300),
  constraint saved_reviews_record_object check (jsonb_typeof(record) = 'object'),
  constraint saved_reviews_record_size check (octet_length(record::text) <= 5000000),
  constraint saved_reviews_record_identity check (record ->> 'review_id' = review_id),
  constraint saved_reviews_record_mode check (record ->> 'mode' = mode),
  constraint saved_reviews_owner_review_unique unique (owner_id, review_id)
);

create index if not exists saved_reviews_owner_updated_idx
  on public.saved_reviews (owner_id, updated_at desc);

create or replace function public.protect_saved_review_identity()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.id is distinct from old.id
     or new.owner_id is distinct from old.owner_id
     or new.review_id is distinct from old.review_id
     or new.schema_version is distinct from old.schema_version
     or new.mode is distinct from old.mode
     or new.created_at is distinct from old.created_at then
    raise exception 'saved review identity and ownership are immutable' using errcode = '42501';
  end if;
  new.revision := old.revision + 1;
  new.updated_at := timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists protect_saved_review_identity on public.saved_reviews;
create trigger protect_saved_review_identity
before update on public.saved_reviews
for each row execute function public.protect_saved_review_identity();

alter table public.saved_reviews enable row level security;
alter table public.saved_reviews force row level security;

revoke all on table public.saved_reviews from anon, authenticated;
grant select on table public.saved_reviews to authenticated;
grant insert (review_id, schema_version, mode, title, record)
  on table public.saved_reviews to authenticated;
grant update (title, record)
  on table public.saved_reviews to authenticated;
grant delete on table public.saved_reviews to authenticated;

drop policy if exists "saved_reviews_select_owner" on public.saved_reviews;
create policy "saved_reviews_select_owner"
on public.saved_reviews for select
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

drop policy if exists "saved_reviews_insert_owner" on public.saved_reviews;
create policy "saved_reviews_insert_owner"
on public.saved_reviews for insert
to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

drop policy if exists "saved_reviews_update_owner" on public.saved_reviews;
create policy "saved_reviews_update_owner"
on public.saved_reviews for update
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

drop policy if exists "saved_reviews_delete_owner" on public.saved_reviews;
create policy "saved_reviews_delete_owner"
on public.saved_reviews for delete
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

comment on table public.saved_reviews is
  'Explicitly saved Research Guard canonical reviews. No Google profile data.';
