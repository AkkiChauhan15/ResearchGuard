-- Optional Research Guard account profile. Authentication remains in auth.users.
-- Email addresses and Google provider data are not duplicated in this table.

create table if not exists public.researcher_profiles (
  user_id uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  full_name text,
  research_role text,
  research_field text,
  institution text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint researcher_profiles_full_name_length
    check (full_name is null or char_length(full_name) between 1 and 120),
  constraint researcher_profiles_role
    check (research_role is null or research_role in (
      'Undergraduate',
      'Master’s student',
      'PhD researcher',
      'Postdoctoral researcher',
      'Faculty',
      'Research staff',
      'Other'
    )),
  constraint researcher_profiles_field_length
    check (research_field is null or char_length(research_field) between 1 and 160),
  constraint researcher_profiles_institution_length
    check (institution is null or char_length(institution) between 1 and 200)
);

create or replace function public.protect_researcher_profile_identity()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.user_id is distinct from old.user_id
     or new.created_at is distinct from old.created_at then
    raise exception 'profile identity and ownership are immutable' using errcode = '42501';
  end if;
  new.updated_at := timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists protect_researcher_profile_identity on public.researcher_profiles;
create trigger protect_researcher_profile_identity
before update on public.researcher_profiles
for each row execute function public.protect_researcher_profile_identity();

alter table public.researcher_profiles enable row level security;
alter table public.researcher_profiles force row level security;

revoke all on table public.researcher_profiles from anon, authenticated;
grant select on table public.researcher_profiles to authenticated;
grant insert (full_name, research_role, research_field, institution)
  on table public.researcher_profiles to authenticated;
grant update (full_name, research_role, research_field, institution)
  on table public.researcher_profiles to authenticated;

drop policy if exists "researcher_profiles_select_owner" on public.researcher_profiles;
create policy "researcher_profiles_select_owner"
on public.researcher_profiles for select
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = user_id);

drop policy if exists "researcher_profiles_insert_owner" on public.researcher_profiles;
create policy "researcher_profiles_insert_owner"
on public.researcher_profiles for insert
to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = user_id);

drop policy if exists "researcher_profiles_update_owner" on public.researcher_profiles;
create policy "researcher_profiles_update_owner"
on public.researcher_profiles for update
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = user_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = user_id);

comment on table public.researcher_profiles is
  'Optional researcher details owned by one authenticated user. No review content or duplicated email.';
