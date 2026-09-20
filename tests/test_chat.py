import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import httpx

from researchguard.api import create_app
from researchguard.auth import AuthenticatedUser
from researchguard.chat.base import ChatProviderError, ProviderMessage, ProviderReply
from researchguard.chat.gemini import GeminiChatProvider
from researchguard.chat.http_provider import groq_provider, nvidia_provider, openrouter_provider
from researchguard.settings import Settings


class FakeProvider:
    name = "Fixture provider"

    def __init__(self, reply=None, error=None):
        self.reply = reply or ProviderReply("A bounded fixture answer.", "fixture-returned-model")
        self.error = error
        self.calls = []

    def complete(self, model, messages, *, timeout_seconds, max_output_tokens):
        self.calls.append((model, messages, timeout_seconds, max_output_tokens))
        if self.error:
            raise self.error
        return self.reply


def settings(**changes):
    values = dict(
        frontend_origins=("http://127.0.0.1:5173",),
        allowed_hosts=("127.0.0.1", "localhost", "testserver"),
        external_concurrency=2,
        auth_timeout_seconds=2,
        chat_timeout_seconds=4,
        chat_provider_timeout_seconds=2,
        chat_requests_per_minute=6,
        supabase_url="https://fixture.supabase.co",
        supabase_publishable_key="sb_publishable_fixture_value",
    )
    values.update(changes)
    return Settings(**values)


class ChatHTTPTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.environment = patch.dict(os.environ, {
            "GROQ_API_KEY": "groq-fixture-secret",
            "GROQ_FREE_TIER_CONFIRMED": "true",
            "OPENROUTER_API_KEY": "openrouter-fixture-secret",
            "GEMINI_API_KEY": "gemini-fixture-secret",
            "GEMINI_FREE_TIER_CONFIRMED": "true",
            "NVIDIA_NIM_API_KEY": "nvidia-fixture-secret",
            "NVIDIA_NIM_FREE_TIER_CONFIRMED": "true",
        })
        self.environment.start()
        self.app = create_app(settings(chat_fallback_enabled=True))
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.user_id = str(uuid4())
        self.app.state.auth_verifier.verify = lambda _token: AuthenticatedUser(
            user_id=self.user_id,
            email="chat@example.test",
        )
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app, raise_app_exceptions=False),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)
        self.environment.stop()

    @property
    def headers(self):
        return {"Authorization": "Bearer fixture-token"}

    async def test_chat_requires_verified_authentication(self):
        status = await self.client.get("/api/chat/providers")
        response = await self.client.post("/api/chat", json={
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": "Synthetic question"}],
        })
        self.assertEqual(status.status_code, 401)
        self.assertEqual(response.status_code, 401)

    async def test_provider_status_exposes_no_secrets(self):
        response = await self.client.get("/api/chat/providers", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["fallback_enabled"])
        self.assertEqual({item["id"] for item in body["providers"]}, {"groq", "openrouter", "gemini", "nvidia"})
        self.assertTrue(all(item["configured"] for item in body["providers"]))
        serialized = json.dumps(body)
        self.assertNotIn("fixture-secret", serialized)
        self.assertNotIn("API_KEY", serialized)

    async def test_normalized_response_and_bounded_conversation(self):
        fake = FakeProvider()
        self.app.state.chat_service.adapters["groq"] = fake
        response = await self.client.post("/api/chat", headers=self.headers, json={
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": "What is MELAS?"},
                {"role": "assistant", "content": "A mitochondrial disorder."},
                {"role": "user", "content": "What mutation commonly causes it?"},
            ],
            "allow_fallback": False,
        })
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["provider"], "groq")
        self.assertEqual(body["model"], "fixture-returned-model")
        self.assertFalse(body["fallback_used"])
        self.assertEqual(body["attempts"][0]["status"], "success")
        self.assertEqual(len(fake.calls), 1)
        sent_messages = fake.calls[0][1]
        self.assertEqual(sent_messages[-1].content, "What mutation commonly causes it?")
        self.assertEqual(sent_messages[0].role, "system")

    async def test_invalid_model_history_and_extra_fields_are_rejected(self):
        base = {
            "provider": "groq",
            "model": "attacker/model",
            "messages": [{"role": "user", "content": "Question"}],
        }
        invalid_model = await self.client.post("/api/chat", headers=self.headers, json=base)
        self.assertEqual(invalid_model.status_code, 400)
        wrong_last_role = await self.client.post("/api/chat", headers=self.headers, json={
            **base,
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "assistant", "content": "Not a user turn"}],
        })
        self.assertEqual(wrong_last_role.status_code, 400)
        oversized_history = await self.client.post("/api/chat", headers=self.headers, json={
            **base,
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user" if index == 6 else "assistant", "content": "x" * 4000}
                for index in range(7)
            ],
        })
        self.assertEqual(oversized_history.status_code, 400)
        extra = await self.client.post("/api/chat", headers=self.headers, json={**base, "api_url": "https://evil.example"})
        self.assertEqual(extra.status_code, 400)

    async def test_explicit_fallback_reports_actual_provider(self):
        self.app.state.chat_service.adapters["groq"] = FakeProvider(
            error=ChatProviderError("Groq fixture rate limit.", "rate_limited")
        )
        openrouter = FakeProvider(ProviderReply("Fallback answer.", "free-router-model"))
        self.app.state.chat_service.adapters["openrouter"] = openrouter
        response = await self.client.post("/api/chat", headers=self.headers, json={
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": "Synthetic question"}],
            "allow_fallback": True,
        })
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["fallback_used"])
        self.assertEqual(body["requested_provider"], "groq")
        self.assertEqual(body["provider"], "openrouter")
        self.assertEqual([item["status"] for item in body["attempts"]], ["rate_limited", "success"])

    async def test_no_silent_fallback_when_not_requested(self):
        self.app.state.chat_service.adapters["groq"] = FakeProvider(
            error=ChatProviderError("Groq fixture rate limit.", "rate_limited")
        )
        openrouter = FakeProvider()
        self.app.state.chat_service.adapters["openrouter"] = openrouter
        response = await self.client.post("/api/chat", headers=self.headers, json={
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": "Synthetic question"}],
            "allow_fallback": False,
        })
        self.assertEqual(response.status_code, 429)
        self.assertIn("rate limit", response.json()["error"])
        self.assertEqual(openrouter.calls, [])


class ChatRateLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limit_is_per_verified_user(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "fixture-secret"}):
            app = create_app(settings(chat_requests_per_minute=1))
            lifespan = app.router.lifespan_context(app)
            await lifespan.__aenter__()
            try:
                app.state.auth_verifier.verify = lambda token: AuthenticatedUser(
                    user_id=str(uuid4()) if token == "second-user" else "00000000-0000-4000-8000-000000000001",
                    email=None,
                )
                app.state.chat_service.adapters["openrouter"] = FakeProvider()
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                    base_url="http://testserver",
                ) as client:
                    payload = {
                        "provider": "openrouter",
                        "model": "openrouter/free",
                        "messages": [{"role": "user", "content": "Question"}],
                    }
                    first = await client.post("/api/chat", headers={"Authorization": "Bearer first-user"}, json=payload)
                    limited = await client.post("/api/chat", headers={"Authorization": "Bearer first-user"}, json=payload)
                    other = await client.post("/api/chat", headers={"Authorization": "Bearer second-user"}, json=payload)
                    self.assertEqual(first.status_code, 200)
                    self.assertEqual(limited.status_code, 429)
                    self.assertIn("retry-after", limited.headers)
                    self.assertEqual(other.status_code, 200)
            finally:
                await lifespan.__aexit__(None, None, None)


class ProviderAdapterTests(unittest.TestCase):
    @patch("researchguard.chat.http_provider.httpx.Client")
    def test_compatible_adapters_use_fixed_official_destinations(self, client_class):
        response = MagicMock()
        response.status_code = 200
        response.iter_bytes.return_value = [json.dumps({
            "model": "returned-model",
            "choices": [{"message": {"content": " Provider answer "}}],
        }).encode()]
        client = client_class.return_value.__enter__.return_value
        client.stream.return_value.__enter__.return_value = response
        cases = [
            (groq_provider(), "GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions"),
            (openrouter_provider(), "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions"),
            (nvidia_provider(), "NVIDIA_NIM_API_KEY", "https://integrate.api.nvidia.com/v1/chat/completions"),
        ]
        for adapter, key_name, endpoint in cases:
            with self.subTest(provider=adapter.name), patch.dict(os.environ, {key_name: "adapter-secret"}):
                reply = adapter.complete(
                    "allowed-model",
                    [ProviderMessage("user", "Synthetic question")],
                    timeout_seconds=3,
                    max_output_tokens=256,
                )
                self.assertEqual(reply.answer, "Provider answer")
                call = client.stream.call_args
                self.assertEqual(call.args[:2], ("POST", endpoint))
                self.assertEqual(call.kwargs["json"]["model"], "allowed-model")
                self.assertEqual(call.kwargs["json"]["messages"][-1]["content"], "Synthetic question")
                self.assertNotIn("adapter-secret", repr(reply))

    @patch("researchguard.chat.http_provider.httpx.Client")
    def test_compatible_adapter_maps_quota_without_leaking_provider_body(self, client_class):
        response = MagicMock(status_code=429)
        client_class.return_value.__enter__.return_value.stream.return_value.__enter__.return_value = response
        with patch.dict(os.environ, {"GROQ_API_KEY": "adapter-secret"}):
            with self.assertRaises(ChatProviderError) as raised:
                groq_provider().complete(
                    "llama-3.1-8b-instant",
                    [ProviderMessage("user", "Question")],
                    timeout_seconds=2,
                    max_output_tokens=128,
                )
        self.assertEqual(raised.exception.category, "rate_limited")
        self.assertNotIn("contains-secret-detail", str(raised.exception))
        self.assertNotIn("adapter-secret", str(raised.exception))

    @patch("researchguard.chat.http_provider.httpx.Client")
    def test_compatible_adapter_rejects_oversized_stream_and_maps_timeout(self, client_class):
        response = MagicMock(status_code=200)
        response.iter_bytes.return_value = [b"x" * 64_001]
        stream = client_class.return_value.__enter__.return_value.stream.return_value
        stream.__enter__.return_value = response
        with patch.dict(os.environ, {"GROQ_API_KEY": "adapter-secret"}):
            with self.assertRaises(ChatProviderError) as oversized:
                groq_provider().complete(
                    "llama-3.1-8b-instant",
                    [ProviderMessage("user", "Question")],
                    timeout_seconds=2,
                    max_output_tokens=128,
                )
            self.assertEqual(oversized.exception.category, "malformed_response")
            stream.__enter__.side_effect = httpx.ReadTimeout("provider timeout detail")
            with self.assertRaises(ChatProviderError) as timeout:
                groq_provider().complete(
                    "llama-3.1-8b-instant",
                    [ProviderMessage("user", "Question")],
                    timeout_seconds=2,
                    max_output_tokens=128,
                )
        self.assertEqual(timeout.exception.category, "timeout")
        self.assertNotIn("provider timeout detail", str(timeout.exception))

    @patch("researchguard.chat.gemini.genai.Client")
    def test_gemini_adapter_sends_history_without_tools(self, client_class):
        client_class.return_value.models.generate_content.return_value = SimpleNamespace(
            text="Gemini fixture answer",
            model_version="gemini-fixture-version",
        )
        with patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-adapter-secret"}):
            reply = GeminiChatProvider().complete(
                "gemini-3.8-flash",
                [
                    ProviderMessage("user", "What is MELAS?"),
                    ProviderMessage("assistant", "A mitochondrial disorder."),
                    ProviderMessage("user", "What commonly causes it?"),
                ],
                timeout_seconds=3,
                max_output_tokens=256,
            )
        self.assertEqual(reply.returned_model, "gemini-fixture-version")
        call = client_class.return_value.models.generate_content.call_args
        self.assertEqual(call.kwargs["model"], "gemini-3.8-flash")
        self.assertEqual([item.role for item in call.kwargs["contents"]], ["user", "model", "user"])
        config = call.kwargs["config"]
        self.assertIsNone(config.tools)
        self.assertTrue(config.automatic_function_calling.disable)
        self.assertNotIn("gemini-adapter-secret", repr(reply))

    @patch("researchguard.chat.gemini.genai.Client")
    def test_gemini_transport_failure_is_safe(self, client_class):
        client_class.return_value.models.generate_content.side_effect = httpx.ConnectError("secret provider detail")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-adapter-secret"}):
            with self.assertRaises(ChatProviderError) as raised:
                GeminiChatProvider().complete(
                    "gemini-3.8-flash",
                    [ProviderMessage("user", "Question")],
                    timeout_seconds=2,
                    max_output_tokens=128,
                )
        self.assertEqual(raised.exception.category, "unavailable")
        self.assertNotIn("secret provider detail", str(raised.exception))
        self.assertNotIn("gemini-adapter-secret", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
