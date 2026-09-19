import json
import os
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

import httpx

from researchguard.api import create_app
from researchguard.auth import AuthenticatedUser
from researchguard.demo import demo_review
from researchguard.schemas import Attempt
from researchguard.settings import Settings
from researchguard.store import ReviewStore


def test_settings(**changes):
    values = dict(
        frontend_origins=("http://127.0.0.1:5173", "http://localhost:5173"),
        session_ttl_seconds=3600,
        max_reviews=100,
        max_review_bytes=5_000_000,
        max_request_bytes=100_000,
        external_concurrency=2,
        retrieval_timeout_seconds=2,
        assessment_timeout_seconds=2,
        auth_timeout_seconds=2,
        supabase_url="https://fixture.supabase.co",
    )
    values.update(changes)
    return Settings(**values)


def seed_accessible_sources(review):
    curated = demo_review()
    claim_id = review.claims[0].claim_id
    review.sources = [source.model_copy(deep=True) for source in curated.sources]
    review.attempts = [
        Attempt(
            retrieval_run_id=source.retrieval_run_id,
            claim_id=claim_id,
            query_or_url=source.url,
            adapter=source.category,
            access_state="partial_access",
            detail="HTTP fixture: archived accessible source.",
            source_ids=[source.source_id],
        )
        for source in review.sources
    ]


def seed_assessment(review):
    claim = review.claims[0]
    claim.assessment = demo_review().claims[0].assessment.model_copy(deep=True)
    claim.assessment_error = None


class AsyncAppClient:
    def __init__(self, settings):
        self.app = create_app(settings)
        self.lifespan = self.app.router.lifespan_context(self.app)
        self.client = None

    async def __aenter__(self):
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app, raise_app_exceptions=False),
            base_url="http://testserver",
        )
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        await self.client.aclose()
        await self.lifespan.__aexit__(exc_type, exc, traceback)


class HTTPTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app_client = AsyncAppClient(test_settings())
        await self.app_client.__aenter__()
        self.client = self.app_client.client
        self.session = str(uuid4())
        self.user_id = str(uuid4())
        self.app_client.app.state.auth_verifier.verify = lambda _token: AuthenticatedUser(
            user_id=self.user_id,
            email="researcher@example.test",
        )

    async def asyncTearDown(self):
        await self.app_client.__aexit__(None, None, None)

    def headers(self, session=None, *, authenticated=True):
        headers = {"X-Review-Session": session or self.session}
        if authenticated:
            headers["Authorization"] = "Bearer fixture-token"
        return headers

    async def create_live(self, **payload_changes):
        payload = {"text": "A synthetic observation implies a mechanism.", "intended_use": "topic understanding"}
        payload.update(payload_changes)
        response = await self.client.post("/api/reviews", headers=self.headers(), json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    async def test_health_config_static_and_cors_contracts(self):
        health = await self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["storage"], "temporary-process-memory")
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": ""}, clear=True):
            config = await self.client.get("/api/config")
        self.assertEqual(config.json()["model_state"], "unavailable_missing_credentials")
        self.assertFalse(config.json()["model_configured"])
        self.assertEqual(config.json()["model_provider"], "gemini")
        self.assertEqual(config.json()["extraction_model"], "gemini-3.8-flash")
        self.assertTrue(config.json()["auth_configured"])
        self.assertTrue(config.json()["live_auth_required"])
        self.assertNotIn("test-secret", json.dumps(config.json()))
        root = await self.client.get("/")
        self.assertEqual(root.status_code, 200)
        self.assertIn("script-src 'self'", root.headers["content-security-policy"])
        self.assertEqual((await self.client.get("/context.md")).status_code, 404)

        preflight = await self.client.options(
            "/api/reviews",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type,x-review-session",
            },
        )
        self.assertEqual(preflight.status_code, 200)
        self.assertEqual(preflight.headers["access-control-allow-origin"], "http://127.0.0.1:5173")
        self.assertNotEqual(preflight.headers.get("access-control-allow-credentials"), "true")
        same_origin = await self.client.post(
            "/api/reviews/demo", headers={**self.headers(), "Origin": "http://testserver"}, json={}
        )
        self.assertEqual(same_origin.status_code, 200, same_origin.text)
        blocked = await self.client.post(
            "/api/reviews/demo", headers={**self.headers(), "Origin": "https://evil.example"}, json={}
        )
        self.assertEqual(blocked.status_code, 400)

        me = await self.client.get("/api/auth/me", headers=self.headers())
        self.assertEqual(me.status_code, 200, me.text)
        self.assertEqual(me.json()["user_id"], self.user_id)

    async def test_public_demo_and_live_authentication_boundary(self):
        public_demo = await self.client.post(
            "/api/reviews/demo",
            headers=self.headers(authenticated=False),
            json={},
        )
        self.assertEqual(public_demo.status_code, 200, public_demo.text)
        demo_id = public_demo.json()["review_id"]
        self.assertEqual((await self.client.get(
            f"/api/reviews/{demo_id}", headers=self.headers(authenticated=False)
        )).status_code, 200)

        unauthenticated = await self.client.post(
            "/api/reviews",
            headers=self.headers(authenticated=False),
            json={"text": "Synthetic claim.", "intended_use": "topic understanding"},
        )
        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(unauthenticated.headers["www-authenticate"], "Bearer")

        live = await self.create_live()
        review_id = live["review_id"]
        self.assertEqual((await self.client.get(
            f"/api/reviews/{review_id}", headers=self.headers(authenticated=False)
        )).status_code, 401)

        other_user = str(uuid4())
        self.app_client.app.state.auth_verifier.verify = lambda _token: AuthenticatedUser(
            user_id=other_user,
            email="other@example.test",
        )
        self.assertEqual((await self.client.get(
            f"/api/reviews/{review_id}", headers=self.headers()
        )).status_code, 404)

    async def test_demo_retrieval_decision_and_canonical_exports(self):
        created = await self.client.post("/api/reviews/demo", headers=self.headers(), json={})
        self.assertEqual(created.status_code, 200, created.text)
        review = created.json()
        review_id = review["review_id"]
        claim_id = review["claims"][0]["claim_id"]
        fetched = await self.client.get(f"/api/reviews/{review_id}", headers=self.headers())
        self.assertEqual(fetched.json(), review)
        decided = await self.client.put(
            f"/api/reviews/{review_id}/claims/{claim_id}/decision",
            headers=self.headers(), json={"decision": {"status": "accepted"}},
        )
        self.assertEqual(decided.status_code, 200, decided.text)
        canonical = (await self.client.get(f"/api/reviews/{review_id}", headers=self.headers())).json()
        self.assertEqual(canonical["claims"][0]["decision"]["status"], "accepted")
        json_export = await self.client.get(f"/api/reviews/{review_id}/export?format=json", headers=self.headers())
        self.assertEqual(json_export.json(), canonical)
        self.assertIn("attachment", json_export.headers["content-disposition"])
        txt_export = await self.client.get(f"/api/reviews/{review_id}/export?format=txt", headers=self.headers())
        self.assertIn(json.dumps(canonical, ensure_ascii=False, indent=2), txt_export.text)

    async def test_main_live_routes_and_material_edits_invalidate_state(self):
        review = await self.create_live(
            intended_use="assay interpretation",
            context={"assay": "Synthetic assay", "conditions": "One time point"},
        )
        review_id = review["review_id"]
        claim_id = review["claims"][0]["claim_id"]
        with patch("researchguard.api.retrieve", side_effect=lambda current, _claim, _query: seed_accessible_sources(current)):
            retrieved = await self.client.post(
                f"/api/reviews/{review_id}/claims/{claim_id}/retrievals",
                headers=self.headers(), json={"query": "synthetic mechanism limitation"},
            )
        self.assertEqual(retrieved.status_code, 200, retrieved.text)
        self.assertEqual(len(retrieved.json()["sources"]), 2)
        with patch("researchguard.api.assess", side_effect=lambda current, _claim: seed_assessment(current)):
            assessed = await self.client.post(
                f"/api/reviews/{review_id}/claims/{claim_id}/assessment", headers=self.headers()
            )
        self.assertEqual(assessed.status_code, 200, assessed.text)
        decided = await self.client.put(
            f"/api/reviews/{review_id}/claims/{claim_id}/decision", headers=self.headers(),
            json={"decision": {"status": "accepted", "notes": "fixture review"}},
        )
        self.assertEqual(decided.status_code, 200, decided.text)
        edited = await self.client.patch(
            f"/api/reviews/{review_id}/claims/{claim_id}", headers=self.headers(),
            json={"text": "A revised synthetic claim."},
        )
        self.assertEqual(edited.status_code, 200, edited.text)
        self.assertIsNone(edited.json()["claims"][0]["assessment"])
        self.assertEqual(edited.json()["claims"][0]["decision"]["status"], "pending")
        self.assertFalse(any(item["claim_id"] == claim_id for item in edited.json()["attempts"]))

        with patch("researchguard.api.retrieve", side_effect=lambda current, _claim, _query: seed_accessible_sources(current)):
            self.assertEqual((await self.client.post(
                f"/api/reviews/{review_id}/claims/{claim_id}/retrievals", headers=self.headers(),
                json={"query": "revised query"},
            )).status_code, 200)
        with patch("researchguard.api.assess", side_effect=lambda current, _claim: seed_assessment(current)):
            self.assertEqual((await self.client.post(
                f"/api/reviews/{review_id}/claims/{claim_id}/assessment", headers=self.headers()
            )).status_code, 200)
        self.assertEqual((await self.client.put(
            f"/api/reviews/{review_id}/claims/{claim_id}/decision", headers=self.headers(),
            json={"decision": {"status": "rejected"}},
        )).status_code, 200)
        context_edit = await self.client.patch(
            f"/api/reviews/{review_id}/context", headers=self.headers(),
            json={"organism_model": "Synthetic model", "assay": "Changed assay", "reagent": "R-1", "conditions": "Two time points"},
        )
        self.assertEqual(context_edit.status_code, 200, context_edit.text)
        self.assertIsNone(context_edit.json()["claims"][0]["assessment"])
        self.assertEqual(context_edit.json()["claims"][0]["decision"]["status"], "pending")
        self.assertFalse(any(item["claim_id"] == claim_id for item in context_edit.json()["attempts"]))

    async def test_session_isolation_blocks_reads_and_mutations(self):
        review = await self.create_live()
        other = str(uuid4())
        review_id = review["review_id"]
        claim_id = review["claims"][0]["claim_id"]
        self.assertEqual((await self.client.get(f"/api/reviews/{review_id}", headers=self.headers(other))).status_code, 404)
        self.assertEqual((await self.client.patch(
            f"/api/reviews/{review_id}/claims/{claim_id}", headers=self.headers(other),
            json={"text": "Cross-session edit."},
        )).status_code, 404)
        unchanged = (await self.client.get(f"/api/reviews/{review_id}", headers=self.headers())).json()
        self.assertEqual(unchanged["claims"][0]["text"], review["claims"][0]["text"])

    async def test_invalid_unsafe_and_oversized_requests_are_rejected(self):
        self.assertEqual((await self.client.post("/api/reviews", headers=self.headers(), json={})).status_code, 400)
        self.assertEqual((await self.client.post(
            "/api/reviews", headers=self.headers(),
            json={"text": "Synthetic.", "intended_use": "topic understanding", "mode": "demo"},
        )).status_code, 400)
        self.assertEqual((await self.client.post(
            "/api/reviews", headers=self.headers(),
            json={"text": "Synthetic.", "intended_use": "topic understanding", "source_urls": ["http://127.0.0.1/"]},
        )).status_code, 400)
        self.assertEqual((await self.client.post(
            "/api/reviews/demo", headers={"X-Review-Session": "invalid"}, json={}
        )).status_code, 400)
        wrong_type = await self.client.post(
            "/api/reviews", headers={**self.headers(), "Content-Type": "text/plain"},
            content=b'{"text":"Synthetic.","intended_use":"topic understanding"}',
        )
        self.assertEqual(wrong_type.status_code, 400)
        oversized = await self.client.post(
            "/api/reviews", headers={**self.headers(), "Content-Type": "application/json"},
            content=b'{' + b'x' * 100_000 + b'}',
        )
        self.assertEqual(oversized.status_code, 413)
        self.assertIn("100000 bytes", oversized.json()["error"])

    async def test_demo_live_separation_and_missing_model_credentials(self):
        demo = (await self.client.post("/api/reviews/demo", headers=self.headers(), json={})).json()
        demo_id = demo["review_id"]
        demo_claim = demo["claims"][0]["claim_id"]
        self.assertEqual((await self.client.patch(
            f"/api/reviews/{demo_id}/claims/{demo_claim}", headers=self.headers(),
            json={"text": "Changed curated claim."},
        )).status_code, 400)
        self.assertEqual((await self.client.post(
            f"/api/reviews/{demo_id}/claims/{demo_claim}/assessment", headers=self.headers()
        )).status_code, 400)

        live = await self.create_live()
        review_id = live["review_id"]
        claim_id = live["claims"][0]["claim_id"]
        with patch("researchguard.api.retrieve", side_effect=lambda current, _claim, _query: seed_accessible_sources(current)):
            await self.client.post(
                f"/api/reviews/{review_id}/claims/{claim_id}/retrievals",
                headers=self.headers(), json={"query": "fixture evidence"},
            )
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": ""}, clear=True):
            unavailable = await self.client.post(
                f"/api/reviews/{review_id}/claims/{claim_id}/assessment", headers=self.headers()
            )
            extraction = await self.client.post(
                f"/api/reviews/{review_id}/extraction", headers=self.headers()
            )
        self.assertEqual(unavailable.status_code, 200, unavailable.text)
        result = unavailable.json()["claims"][0]
        self.assertIsNone(result["assessment"])
        self.assertIn("GEMINI_API_KEY", result["assessment_error"])
        self.assertEqual(extraction.status_code, 400, extraction.text)
        self.assertIn("GEMINI_API_KEY", extraction.json()["error"])

    async def test_external_timeout_does_not_commit_partial_mutation(self):
        def slow_retrieval(review, _claim, _query):
            review.validation_results.append("must not commit")
            time.sleep(0.05)

        async with AsyncAppClient(test_settings(retrieval_timeout_seconds=0.01, external_concurrency=1)) as app_client:
            session = str(uuid4())
            user_id = str(uuid4())
            app_client.app.state.auth_verifier.verify = lambda _token: AuthenticatedUser(
                user_id=user_id,
                email="timeout@example.test",
            )
            headers = {"X-Review-Session": session, "Authorization": "Bearer fixture-token"}
            created = (await app_client.client.post(
                "/api/reviews", headers=headers,
                json={"text": "Synthetic.", "intended_use": "topic understanding"},
            )).json()
            review_id = created["review_id"]
            claim_id = created["claims"][0]["claim_id"]
            with patch("researchguard.api.retrieve", side_effect=slow_retrieval):
                response = await app_client.client.post(
                    f"/api/reviews/{review_id}/claims/{claim_id}/retrievals",
                    headers=headers, json={"query": "slow fixture"},
                )
            self.assertEqual(response.status_code, 504, response.text)
            canonical = (await app_client.client.get(f"/api/reviews/{review_id}", headers=headers)).json()
            self.assertNotIn("must not commit", canonical["validation_results"])
            self.assertEqual(app_client.app.state.external_executor._max_workers, 1)


class StoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_expired_records_are_removed(self):
        current = [100.0]
        store = ReviewStore(ttl_seconds=10, max_reviews=1, clock=lambda: current[0])
        review = demo_review()
        await store.add("session", review)
        current[0] = 111.0
        await store.prune()
        with self.assertRaises(LookupError):
            await store.get_entry("session", review.review_id)

    async def test_wildcard_frontend_origin_is_rejected(self):
        with patch.dict(os.environ, {"RESEARCHGUARD_FRONTEND_ORIGINS": "*"}):
            with self.assertRaises(ValueError):
                Settings.from_env()


if __name__ == "__main__":
    unittest.main()
