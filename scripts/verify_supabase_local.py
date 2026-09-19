"""Exercise real local Supabase Auth, PostgREST, RLS, and FastAPI boundaries.

Requires an already-running local stack (`supabase start`). It creates two disposable
email/password identities in that local stack, deletes its saved review, and prints no
tokens, keys, passwords, record bodies, or account identifiers.
"""
from __future__ import annotations

import json
import subprocess
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from researchguard.api import create_app
from researchguard.settings import Settings


def require(response: httpx.Response, status: int, label: str) -> dict:
    if response.status_code != status:
        raise RuntimeError(f"{label}: expected HTTP {status}, received {response.status_code}")
    if not response.content:
        return {}
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label}: expected a JSON object")
    return payload


def local_configuration() -> tuple[str, str]:
    completed = subprocess.run(
        ["supabase", "status", "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    values = json.loads(completed.stdout)
    url = values.get("API_URL")
    key = values.get("PUBLISHABLE_KEY")
    if not isinstance(url, str) or not url.startswith("http://127.0.0.1:"):
        raise RuntimeError("Local Supabase API URL is unavailable.")
    if not isinstance(key, str) or not key.startswith("sb_publishable_"):
        raise RuntimeError("Local Supabase publishable key is unavailable.")
    return url, key


def sign_up(client: httpx.Client, url: str, key: str, label: str) -> str:
    response = client.post(
        f"{url}/auth/v1/signup",
        headers={"apikey": key},
        json={
            "email": f"researchguard-phase-h-{label}-{uuid4().hex}@example.test",
            "password": f"Local-test-only-{uuid4().hex}!",
        },
    )
    payload = require(response, 200, f"create local identity {label}")
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError(f"create local identity {label}: no access token returned")
    return token


def main() -> None:
    url, key = local_configuration()
    with httpx.Client(timeout=10) as auth_client:
        token_one = sign_up(auth_client, url, key, "one")
        token_two = sign_up(auth_client, url, key, "two")

    settings = Settings(
        supabase_url=url,
        supabase_publishable_key=key,
        auth_timeout_seconds=10,
        persistence_timeout_seconds=10,
    )
    session_one = str(uuid4())
    session_opened = str(uuid4())
    auth_one = {"Authorization": f"Bearer {token_one}"}
    auth_two = {"Authorization": f"Bearer {token_two}"}
    session_headers = {**auth_one, "X-Review-Session": session_one}

    with TestClient(create_app(settings)) as app:
        require(app.post("/api/reviews/demo", headers={"X-Review-Session": str(uuid4())}), 200, "public demo")
        require(
            app.post(
                "/api/reviews",
                headers={"X-Review-Session": str(uuid4())},
                json={"text": "A synthetic observation proves a universal mechanism.", "intended_use": "topic understanding"},
            ),
            401,
            "signed-out live review",
        )
        require(app.get("/api/auth/me", headers=auth_one), 200, "verified token one")
        require(app.get("/api/auth/me", headers=auth_two), 200, "verified token two")

        parts = token_one.split(".")
        parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
        require(
            app.get("/api/auth/me", headers={"Authorization": "Bearer " + ".".join(parts)}),
            401,
            "tampered token",
        )

        created = require(
            app.post(
                "/api/reviews",
                headers=session_headers,
                json={
                    "text": "A synthetic observation proves a universal mechanism.",
                    "intended_use": "topic understanding",
                    "context": {"organism_model": "synthetic model"},
                    "source_urls": [],
                },
            ),
            200,
            "authenticated live review",
        )
        review_id = created["review_id"]

        require(
            app.post(
                "/api/saved-reviews",
                headers=session_headers,
                json={"review_id": review_id, "owner_id": "22222222-2222-4222-8222-222222222222"},
            ),
            400,
            "forged owner field",
        )
        saved = require(
            app.post(
                "/api/saved-reviews",
                headers=session_headers,
                json={"review_id": review_id},
            ),
            201,
            "explicit save",
        )
        saved_id = saved["saved_id"]
        if saved["review"] != created or saved["revision"] != 1:
            raise RuntimeError("explicit save did not preserve the canonical review")

        own_list = require(app.get("/api/saved-reviews", headers=auth_one), 200, "owner list")
        other_list = require(app.get("/api/saved-reviews", headers=auth_two), 200, "other-user list")
        if len(own_list.get("items", [])) != 1 or other_list.get("items") != []:
            raise RuntimeError("owner-only saved-review listing failed")

        for path, method in (
            (f"/api/saved-reviews/{saved_id}/export?format=json", "get"),
            (f"/api/saved-reviews/{saved_id}?expected_revision=1", "delete"),
        ):
            response = getattr(app, method)(path, headers=auth_two)
            require(response, 404, f"other-user {method}")

        opened = require(
            app.post(
                f"/api/saved-reviews/{saved_id}/open",
                headers={**auth_one, "X-Review-Session": session_opened},
            ),
            200,
            "open saved review",
        )
        if opened["review"] != created:
            raise RuntimeError("opened saved review differs from canonical record")

        claim_id = created["claims"][0]["claim_id"]
        edited = require(
            app.patch(
                f"/api/reviews/{review_id}/claims/{claim_id}",
                headers={**auth_one, "X-Review-Session": session_opened},
                json={"text": "A synthetic observation may suggest a model-specific mechanism."},
            ),
            200,
            "edit opened claim",
        )
        if edited["claims"][0]["assessment"] is not None or edited["claims"][0]["decision"]["status"] != "pending":
            raise RuntimeError("claim edit did not leave invalidated assessment and decision state")

        updated = require(
            app.put(
                f"/api/saved-reviews/{saved_id}",
                headers={**auth_one, "X-Review-Session": session_opened},
                json={"review_id": review_id, "expected_revision": 1},
            ),
            200,
            "update saved review",
        )
        if updated["revision"] != 2 or updated["review"] != edited:
            raise RuntimeError("saved update did not preserve the edited canonical review")

        require(
            app.put(
                f"/api/saved-reviews/{saved_id}",
                headers={**auth_one, "X-Review-Session": session_opened},
                json={"review_id": review_id, "expected_revision": 1},
            ),
            409,
            "stale saved update",
        )

        exported_response = app.get(
            f"/api/saved-reviews/{saved_id}/export?format=json",
            headers=auth_one,
        )
        exported = require(exported_response, 200, "saved export")
        if exported != edited:
            raise RuntimeError("saved export differs from the canonical review")

        require(
            app.delete(
                f"/api/saved-reviews/{saved_id}?expected_revision=2",
                headers=auth_one,
            ),
            200,
            "owner delete",
        )
        after_delete = require(app.get("/api/saved-reviews", headers=auth_one), 200, "list after delete")
        if after_delete.get("items") != []:
            raise RuntimeError("deleted saved review remains visible")

    print(json.dumps({
        "status": "passed",
        "identity_provider": "local Supabase Auth email fixture; not Google OAuth",
        "real_access_tokens_verified": 2,
        "public_demo_without_auth": "passed",
        "signed_out_live_rejection": "passed",
        "tampered_token_rejection": "passed",
        "owner_only_list_open_update_export_delete": "passed",
        "cross_owner_read_export_delete": "rejected",
        "forged_owner_field": "rejected",
        "stale_update": "rejected with local review retained",
        "canonical_saved_export": "matched",
    }, indent=2))


if __name__ == "__main__":
    main()
