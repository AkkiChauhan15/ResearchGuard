-- Owner-scoped structured provider comparisons derived from saved review records.

create table if not exists public.multi_provider_assessments (
  id uuid primary key default gen_random_uuid(),
  saved_review_id uuid not null references public.saved_reviews (id) on delete cascade,
  owner_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  review_id text not null,
  claim_id text not null,
  source_ids jsonb not null default '[]'::jsonb,
  provider text not null,
  model text not null,
  is_primary boolean not null,
  label text not null,
  confidence text not null,
  quote_check_passed boolean not null,
  created_at timestamptz not null default timezone('utc', now()),
  constraint multi_provider_review_id_format check (review_id ~ '^review_[0-9a-f]{32}$'),
  constraint multi_provider_claim_id_format check (claim_id ~ '^claim_[0-9a-f]{32}$'),
  constraint multi_provider_source_ids_array check (jsonb_typeof(source_ids) = 'array'),
  constraint multi_provider_provider check (provider in ('groq', 'openrouter', 'nvidia', 'gemini')),
  constraint multi_provider_model_length check (char_length(model) between 1 and 200),
  constraint multi_provider_label check (label in ('supports', 'contradicts', 'uncertain', 'insufficient')),
  constraint multi_provider_confidence check (confidence in ('low', 'medium', 'high')),
  constraint multi_provider_saved_claim_provider_unique unique (saved_review_id, claim_id, provider)
);

create unique index if not exists multi_provider_one_primary_per_claim
  on public.multi_provider_assessments (saved_review_id, claim_id)
  where is_primary;

create index if not exists multi_provider_owner_review_idx
  on public.multi_provider_assessments (owner_id, review_id, claim_id, created_at);

create or replace function public.protect_multi_provider_assessment_identity()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.id is distinct from old.id
     or new.saved_review_id is distinct from old.saved_review_id
     or new.owner_id is distinct from old.owner_id
     or new.review_id is distinct from old.review_id
     or new.claim_id is distinct from old.claim_id
     or new.provider is distinct from old.provider
     or new.model is distinct from old.model
     or new.is_primary is distinct from old.is_primary
     or new.created_at is distinct from old.created_at then
    raise exception 'provider assessment identity and ownership are immutable' using errcode = '42501';
  end if;
  return new;
end;
$$;

drop trigger if exists protect_multi_provider_assessment_identity on public.multi_provider_assessments;
create trigger protect_multi_provider_assessment_identity
before update on public.multi_provider_assessments
for each row execute function public.protect_multi_provider_assessment_identity();

alter table public.multi_provider_assessments enable row level security;
alter table public.multi_provider_assessments force row level security;

revoke all on table public.multi_provider_assessments from anon, authenticated;
grant select on table public.multi_provider_assessments to authenticated;
grant insert (
  saved_review_id, review_id, claim_id, source_ids, provider, model,
  is_primary, label, confidence, quote_check_passed, created_at
) on table public.multi_provider_assessments to authenticated;
grant update (label, confidence, quote_check_passed)
  on table public.multi_provider_assessments to authenticated;
grant delete on table public.multi_provider_assessments to authenticated;

drop policy if exists "multi_provider_assessments_select_owner" on public.multi_provider_assessments;
create policy "multi_provider_assessments_select_owner"
on public.multi_provider_assessments for select
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

drop policy if exists "multi_provider_assessments_insert_owner" on public.multi_provider_assessments;
create policy "multi_provider_assessments_insert_owner"
on public.multi_provider_assessments for insert
to authenticated
with check (
  (select auth.uid()) is not null
  and (select auth.uid()) = owner_id
  and exists (
    select 1 from public.saved_reviews
    where saved_reviews.id = saved_review_id
      and saved_reviews.owner_id = (select auth.uid())
  )
);

drop policy if exists "multi_provider_assessments_update_owner" on public.multi_provider_assessments;
create policy "multi_provider_assessments_update_owner"
on public.multi_provider_assessments for update
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

drop policy if exists "multi_provider_assessments_delete_owner" on public.multi_provider_assessments;
create policy "multi_provider_assessments_delete_owner"
on public.multi_provider_assessments for delete
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

create or replace function public.sync_saved_review_provider_assessments()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  delete from public.multi_provider_assessments
  where saved_review_id = new.id;

  insert into public.multi_provider_assessments (
    saved_review_id, owner_id, review_id, claim_id, source_ids, provider, model,
    is_primary, label, confidence, quote_check_passed, created_at
  )
  select
    new.id,
    new.owner_id,
    new.review_id,
    claim ->> 'claim_id',
    assessment -> 'source_ids',
    assessment ->> 'provider',
    assessment ->> 'model',
    (assessment ->> 'is_primary')::boolean,
    assessment ->> 'label',
    assessment ->> 'confidence',
    (assessment ->> 'quote_check_passed')::boolean,
    (assessment ->> 'created_at')::timestamptz
  from jsonb_array_elements(coalesce(new.record -> 'claims', '[]'::jsonb)) as claim
  cross join lateral jsonb_array_elements(
    coalesce(claim -> 'provider_assessments', '[]'::jsonb)
  ) as assessment;

  return new;
end;
$$;

revoke all on function public.sync_saved_review_provider_assessments() from public, anon, authenticated;

drop trigger if exists sync_saved_review_provider_assessments on public.saved_reviews;
create trigger sync_saved_review_provider_assessments
after insert or update of record on public.saved_reviews
for each row execute function public.sync_saved_review_provider_assessments();

comment on table public.multi_provider_assessments is
  'Structured primary and opt-in second-opinion results derived from owner-scoped saved reviews.';
