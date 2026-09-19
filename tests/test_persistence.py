import json
import unittest
from pathlib import Path
from uuid import uuid4

import httpx

from researchguard.demo import demo_review
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


if __name__ == "__main__":
    unittest.main()
