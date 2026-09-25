import json
import unittest
from pathlib import Path
from uuid import uuid4

import httpx

from researchguard.demo import demo_review
from researchguard.chat_persistence import (
    SavedChatMessage,
    SupabaseChatRepository,
)
from researchguard.persistence import (
    PersistenceConflict,
    PersistenceNotFound,
    PersistenceUnavailable,
    SupabaseReviewRepository,
)


ROOT = Path(__file__).resolve().parent.parent


def row(review, *, saved_id=None, revision=1):
    return {
        "id": saved_id or str(uuid4()),
        "review_id": review.review_id,
        "schema_version": 1,
        "revision": revision,
        "mode": review.mode,
        "title": review.claims[0].text,
        "created_at": "2026-09-19T00:00:00+00:00",
        "updated_at": "2026-09-19T00:00:00+00:00",
        "record": review.model_dump(mode="json"),
    }


class RepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_uses_user_jwt_publishable_key_and_never_sends_owner(self):
        review = demo_review()
        expected = row(review)
        captured = {}

        def handler(request: httpx.Request):
            captured["authorization"] = request.headers.get("authorization")
            captured["apikey"] = request.headers.get("apikey")
            captured["body"] = json.loads(request.content)
            return httpx.Response(201, json=[expected])

        client = httpx.AsyncClient(
            base_url="https://fixture.supabase.co",
            transport=httpx.MockTransport(handler),
        )
        repository = SupabaseReviewRepository(
            "https://fixture.supabase.co",
            "sb_publishable_fixture_value",
            client=client,
        )
        saved = await repository.create("signed-user-jwt", review)
        self.assertEqual(saved.review, review)
        self.assertEqual(captured["authorization"], "Bearer signed-user-jwt")
        self.assertEqual(captured["apikey"], "sb_publishable_fixture_value")
        self.assertNotIn("owner_id", captured["body"])
        self.assertNotIn("email", captured["body"])
        await client.aclose()

    async def test_saved_chat_uses_user_jwt_and_never_sends_owner(self):
        messages = [
            SavedChatMessage(role="user", content="Synthetic question"),
            SavedChatMessage(role="assistant", content="Synthetic answer", provider="groq", model="fixture-model"),
        ]
        saved_id = str(uuid4())
        captured = {}
        expected = {
            "id": saved_id,
            "schema_version": 1,
            "revision": 1,
            "title": "Synthetic question",
            "message_count": 2,
            "last_provider": "groq",
            "last_model": "fixture-model",
            "created_at": "2026-09-21T00:00:00+00:00",
            "updated_at": "2026-09-21T00:00:00+00:00",
            "record": {"messages": [message.model_dump(mode="json") for message in messages]},
        }

        def handler(request: httpx.Request):
            captured["authorization"] = request.headers.get("authorization")
            captured["body"] = json.loads(request.content)
            return httpx.Response(201, json=[expected])

        client = httpx.AsyncClient(base_url="https://fixture.supabase.co", transport=httpx.MockTransport(handler))
        repository = SupabaseChatRepository(
            "https://fixture.supabase.co",
            "sb_publishable_fixture_value",
            client=client,
        )
        saved = await repository.create("signed-user-jwt", messages)
        self.assertEqual(saved.summary.chat_id, saved_id)
        self.assertEqual(captured["authorization"], "Bearer signed-user-jwt")
        self.assertNotIn("owner_id", captured["body"])
        self.assertNotIn("email", captured["body"])
        await client.aclose()

    async def test_saved_chat_update_sends_only_mutable_columns(self):
        messages = [
            SavedChatMessage(role="user", content="Synthetic question"),
            SavedChatMessage(role="assistant", content="Synthetic answer", provider="groq", model="fixture-model"),
            SavedChatMessage(role="user", content="Follow-up question"),
            SavedChatMessage(role="assistant", content="Follow-up answer", provider="groq", model="fixture-model"),
        ]
        saved_id = str(uuid4())
        captured = {}
        expected = {
            "id": saved_id,
            "schema_version": 1,
            "revision": 2,
            "title": "Synthetic question",
            "message_count": 4,
            "last_provider": "groq",
            "last_model": "fixture-model",
            "created_at": "2026-09-21T00:00:00+00:00",
            "updated_at": "2026-09-21T00:01:00+00:00",
            "record": {"messages": [message.model_dump(mode="json") for message in messages]},
        }

        def handler(request: httpx.Request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=[expected])

        client = httpx.AsyncClient(base_url="https://fixture.supabase.co", transport=httpx.MockTransport(handler))
        repository = SupabaseChatRepository(
            "https://fixture.supabase.co",
            "sb_publishable_fixture_value",
            client=client,
        )
        saved = await repository.update("signed-user-jwt", saved_id, 1, messages)
        self.assertEqual(saved.summary.revision, 2)
        self.assertEqual(
            set(captured["body"]),
            {"title", "message_count", "last_provider", "last_model", "record"},
        )
        self.assertNotIn("schema_version", captured["body"])
        self.assertNotIn("owner_id", captured["body"])
        self.assertNotIn("revision", captured["body"])
        await client.aclose()

    async def test_stale_update_and_cross_owner_empty_results_are_distinct(self):
        review = demo_review()
        saved_id = str(uuid4())
        calls = []

        def handler(request: httpx.Request):
            calls.append((request.method, str(request.url)))
            if request.method == "PATCH":
                return httpx.Response(200, json=[])
            if "id=eq." in str(request.url) and "cross-owner" not in request.headers.get("authorization", ""):
                return httpx.Response(200, json=[row(review, saved_id=saved_id, revision=2)])
            return httpx.Response(200, json=[])

        client = httpx.AsyncClient(
            base_url="https://fixture.supabase.co",
            transport=httpx.MockTransport(handler),
        )
        repository = SupabaseReviewRepository(
            "https://fixture.supabase.co",
            "sb_publishable_fixture_value",
            client=client,
        )
        with self.assertRaises(PersistenceConflict):
            await repository.update("owner-token", saved_id, 1, review)
        with self.assertRaises(PersistenceNotFound):
            await repository.get("cross-owner-token", saved_id)
        self.assertEqual(calls[0][0], "PATCH")
        await client.aclose()

    async def test_unconfigured_and_unavailable_service_are_clear(self):
        unconfigured = SupabaseReviewRepository(None, None)
        with self.assertRaisesRegex(PersistenceUnavailable, "SUPABASE_URL"):
            await unconfigured.list("unused-token")
        await unconfigured.close()

        client = httpx.AsyncClient(
            base_url="https://fixture.supabase.co",
            transport=httpx.MockTransport(lambda _request: httpx.Response(503)),
        )
        repository = SupabaseReviewRepository(
            "https://fixture.supabase.co",
            "sb_publishable_fixture_value",
            client=client,
        )
        with self.assertRaisesRegex(PersistenceUnavailable, "temporarily unavailable"):
            await repository.list("signed-user-jwt")
        await client.aclose()


class MigrationContractTests(unittest.TestCase):
    def test_versioned_migration_has_rls_owner_policies_and_column_grants(self):
        migration = (ROOT / "supabase/migrations/202609190001_create_saved_reviews.sql").read_text()
        normalized = " ".join(migration.lower().split())
        self.assertIn("alter table public.saved_reviews enable row level security", normalized)
        self.assertIn("alter table public.saved_reviews force row level security", normalized)
        for operation in ("select", "insert", "update", "delete"):
            self.assertIn(f"on public.saved_reviews for {operation} to authenticated", normalized)
        self.assertGreaterEqual(normalized.count("(select auth.uid()) = owner_id"), 5)
        self.assertIn("revoke all on table public.saved_reviews from anon, authenticated", normalized)
        self.assertIn("grant update (title, record)", normalized)
        self.assertNotIn("grant update on table public.saved_reviews to authenticated", normalized)
        self.assertIn("new.owner_id is distinct from old.owner_id", normalized)
        self.assertIn("new.mode is distinct from old.mode", normalized)
        self.assertIn("owner_id uuid not null default auth.uid()", normalized)
        self.assertIn("schema_version integer not null default 1", normalized)
        self.assertIn("revision bigint not null default 1", normalized)
        self.assertIn("octet_length(record::text) <= 5000000", normalized)

        rls_test = (ROOT / "supabase/tests/001_saved_reviews_rls.test.sql").read_text().lower()
        self.assertIn("set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111'", rls_test)
        self.assertIn("set_config('request.jwt.claim.sub', '22222222-2222-4222-8222-222222222222'", rls_test)
        self.assertIn("user one cannot forge owner_id", rls_test)
        self.assertIn("user two cannot update user one records", rls_test)
        self.assertIn("user two cannot delete user one records", rls_test)
        self.assertIn("authenticated clients cannot assign owner_id", rls_test)
        self.assertIn("signed-out clients cannot read saved reviews", rls_test)

    def test_profile_migration_has_optional_owner_only_rls_contract(self):
        migration = (ROOT / "supabase/migrations/202609190002_create_researcher_profiles.sql").read_text()
        normalized = " ".join(migration.lower().split())
        self.assertIn("user_id uuid primary key default auth.uid()", normalized)
        self.assertIn("alter table public.researcher_profiles enable row level security", normalized)
        self.assertIn("alter table public.researcher_profiles force row level security", normalized)
        for operation in ("select", "insert", "update"):
            self.assertIn(f"on public.researcher_profiles for {operation} to authenticated", normalized)
        self.assertNotIn("on public.researcher_profiles for delete", normalized)
        self.assertGreaterEqual(normalized.count("(select auth.uid()) = user_id"), 4)
        self.assertIn("revoke all on table public.researcher_profiles from anon, authenticated", normalized)
        self.assertIn("grant insert (full_name, research_role, research_field, institution)", normalized)
        self.assertIn("grant update (full_name, research_role, research_field, institution)", normalized)
        self.assertNotIn("grant update on table public.researcher_profiles", normalized)
        self.assertIn("new.user_id is distinct from old.user_id", normalized)
        self.assertNotIn("email text", normalized)

        rls_test = (ROOT / "supabase/tests/002_researcher_profiles_rls.test.sql").read_text().lower()
        self.assertIn("profile owner is derived from auth.uid()", rls_test)
        self.assertIn("profile creation is safe to repeat", rls_test)
        self.assertIn("another user cannot read the first profile", rls_test)
        self.assertIn("another user cannot update the first profile", rls_test)
        self.assertIn("profile owner cannot be changed", rls_test)
        self.assertIn("optional profile details can all be skipped", rls_test)
        self.assertIn("signed-out clients cannot read profiles", rls_test)

    def test_saved_chat_migration_has_owner_only_rls_contract(self):
        migration = (ROOT / "supabase/migrations/202609210001_create_saved_chats.sql").read_text()
        normalized = " ".join(migration.lower().split())
        self.assertIn("alter table public.saved_chats enable row level security", normalized)
        self.assertIn("alter table public.saved_chats force row level security", normalized)
        for operation in ("select", "insert", "update", "delete"):
            self.assertIn(f"on public.saved_chats for {operation} to authenticated", normalized)
        self.assertGreaterEqual(normalized.count("(select auth.uid()) = owner_id"), 5)
        self.assertIn("revoke all on table public.saved_chats from anon, authenticated", normalized)
        self.assertIn("owner_id uuid not null default auth.uid()", normalized)
        self.assertIn("new.owner_id is distinct from old.owner_id", normalized)
        self.assertIn("grant update (title, message_count, last_provider, last_model, record)", normalized)
        self.assertNotIn("grant update on table public.saved_chats", normalized)
        self.assertIn("octet_length(record::text) <= 250000", normalized)

        rls_test = (ROOT / "supabase/tests/003_saved_chats_rls.test.sql").read_text().lower()
        self.assertIn("chat owner is derived from auth.uid()", rls_test)
        self.assertIn("user two cannot read user one chats", rls_test)
        self.assertIn("user two cannot update user one chats", rls_test)
        self.assertIn("user two cannot delete user one chats", rls_test)
        self.assertIn("user one cannot forge chat owner_id", rls_test)
        self.assertIn("signed-out clients cannot read saved chats", rls_test)

    def test_multi_provider_migration_has_owner_only_list_contract(self):
        migration = (ROOT / "supabase/migrations/202609250001_multi_provider_assessments.sql").read_text()
        normalized = " ".join(migration.lower().split())
        self.assertIn("create table if not exists public.multi_provider_assessments", normalized)
        for column in (
            "provider text not null",
            "model text not null",
            "is_primary boolean not null",
            "label text not null",
            "confidence text not null",
            "quote_check_passed boolean not null",
            "created_at timestamptz not null",
        ):
            self.assertIn(column, normalized)
        self.assertIn("alter table public.multi_provider_assessments enable row level security", normalized)
        self.assertIn("alter table public.multi_provider_assessments force row level security", normalized)
        for operation in ("select", "insert", "update", "delete"):
            self.assertIn(f"on public.multi_provider_assessments for {operation} to authenticated", normalized)
        self.assertGreaterEqual(normalized.count("(select auth.uid()) = owner_id"), 5)
        self.assertIn("new.owner_id is distinct from old.owner_id", normalized)
        self.assertIn("sync_saved_review_provider_assessments", normalized)
        self.assertIn("jsonb_array_elements", normalized)

        rls_test = (ROOT / "supabase/tests/004_multi_provider_assessments_rls.test.sql").read_text().lower()
        self.assertIn("saved canonical list synchronizes two provider assessments", rls_test)
        self.assertIn("user two cannot read user one provider assessments", rls_test)
        self.assertIn("user two cannot update user one provider assessments", rls_test)
        self.assertIn("user two cannot delete user one provider assessments", rls_test)
        self.assertIn("user two cannot forge provider-assessment owner_id", rls_test)
        self.assertIn("signed-out clients cannot read provider assessments", rls_test)


if __name__ == "__main__":
    unittest.main()
