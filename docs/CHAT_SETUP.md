# AI chat setup

The optional `/chat` page is a general assistant beside the evidence-review workflow.
Its replies are labeled **not evidence-checked** and are never inserted into a review,
saved to Supabase, or exported as evidence. A verified Supabase session is required so
anonymous visitors cannot spend server provider quotas.

The same server keys can now be used by the structured evidence workflow. That workflow
has a separate explicit `LLM_PROVIDER` selection and never uses chat fallback. Set
`LLM_PROVIDER=groq` with `GROQ_EXTRACTION_MODEL=openai/gpt-oss-20b` and the matching
assessment model for the recommended configuration. `openrouter` and `nvidia` are also
supported with the allowlisted model variables in `.env.example`; `gemini` is retained
but no longer the default. Chat provider/model choices do not change the evidence
provider for an in-progress review.

## Server configuration

Add only the providers you intend to use to the ignored root `.env` for local work and
to the Render service environment for deployment:

```dotenv
GROQ_API_KEY=
GROQ_FREE_TIER_CONFIRMED=false
OPENROUTER_API_KEY=
GEMINI_API_KEY=
GEMINI_FREE_TIER_CONFIRMED=false
NVIDIA_NIM_API_KEY=
NVIDIA_NIM_FREE_TIER_CONFIRMED=false

RESEARCHGUARD_CHAT_FALLBACK_ENABLED=false
RESEARCHGUARD_CHAT_REQUESTS_PER_MINUTE=6
RESEARCHGUARD_CHAT_TIMEOUT_SECONDS=45
RESEARCHGUARD_CHAT_PROVIDER_TIMEOUT_SECONDS=20
RESEARCHGUARD_CHAT_MAX_OUTPUT_TOKENS=1024
```

Never create a `VITE_GROQ_*`, `VITE_OPENROUTER_*`, `VITE_GEMINI_*`, or
`VITE_NVIDIA_*` variable. Provider keys belong only on FastAPI/Render. The browser gets
provider names, model names, configuration booleans, and normalized answers; it never
gets a key.

For Groq, Gemini, and NVIDIA, set the corresponding confirmation to `true` only after
checking that the exact account/project uses free access with no billing. OpenRouter is
restricted in `researchguard/chat/models.json` to its documented `openrouter/free`
router. Do not purchase credits or enable billing for this project.

Fallback remains disabled unless `RESEARCHGUARD_CHAT_FALLBACK_ENABLED=true`. A user must
also select the fallback checkbox for a request. Only configured providers that pass
the free-tier gates are considered. A successful response names the provider and model
that actually answered; the backend never silently switches or uses a paid model.

## HTTP contract

The signed-in SPA first calls `GET /api/chat/providers`, then sends its own backend:

```json
{
  "provider": "openrouter",
  "model": "openrouter/free",
  "messages": [
    {"role": "user", "content": "What is MELAS?"},
    {"role": "assistant", "content": "Earlier assistant reply"},
    {"role": "user", "content": "What mutation commonly causes it?"}
  ],
  "allow_fallback": false
}
```

The normalized success response is:

```json
{
  "success": true,
  "provider": "openrouter",
  "requested_provider": "openrouter",
  "model": "actual-returned-model",
  "requested_model": "openrouter/free",
  "answer": "Provider answer",
  "fallback_used": false,
  "attempts": [
    {"provider": "openrouter", "model": "openrouter/free", "status": "success"}
  ]
}
```

The backend accepts no URL field. React renders answer text without HTML interpretation.
Messages are bounded and treated as untrusted model input.

## Model list

Edit `researchguard/chat/models.json` to change visible model IDs and labels. This file
is the server allowlist, so the browser cannot submit an arbitrary model or API URL.
Before adding an ID, verify it in the provider's current official model and pricing
documentation and confirm that it is available without billing in the actual account.
The backend destinations remain fixed in provider adapters and are not configured by
the browser or this JSON file.

## Run and verify

Start FastAPI and Vite from the repository root:

```sh
.venv/bin/python -m researchguard.server
npm run dev --prefix frontend
```

Open `http://127.0.0.1:5173/chat`, sign in, choose an available provider and model, and
send public or synthetic text. Conversation history stays in React memory and is sent
again with each follow-up. Clear chat or reload to remove it; it is not persisted.

Run one bounded live connectivity check without printing the answer or key:

```sh
.venv/bin/python -m scripts.verify_chat_live --provider groq
```

Replace `groq` with `openrouter`, `nvidia`, or `gemini` after configuring that provider.
This confirms connectivity and response parsing only, not scientific accuracy.

## Add another provider

1. Add its server key name and free-access gate to `researchguard/chat/config.py`.
2. Add allowed current model IDs and labels to `researchguard/chat/models.json`.
3. Implement the `ChatProvider.complete()` interface in `researchguard/chat/`; keep its
   fixed official endpoint and response differences inside that adapter.
4. Register the adapter in `ChatService` and add the provider ID to the FastAPI request
   literal and frontend `ChatProviderId` type.
5. Add fixture tests for its endpoint, authentication header, request mapping, malformed
   output, timeout, quota error, returned model, and absence of secrets.
6. Recheck official free-tier terms, run the full test/build suite, then perform one
   bounded public/synthetic live check without fallback.

Current official contracts checked on 2026-09-20:

- [Groq Chat Completions API](https://console.groq.com/docs/api-reference)
- [Groq models and model-list endpoint](https://console.groq.com/docs/models)
- [OpenRouter Chat Completions API](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request)
- [OpenRouter free model router](https://openrouter.ai/collections/free-models)
- [Gemini text generation and multi-turn chat](https://ai.google.dev/gemini-api/docs/generate-content/text-generation)
- [Gemini models](https://ai.google.dev/gemini-api/docs/models)
- [NVIDIA NIM LLM API](https://docs.api.nvidia.com/nim/re/reference/llm-apis)
- [NVIDIA API Catalog quickstart](https://docs.api.nvidia.com/nim/docs/api-quickstart)
