"""Archived provider marker.

The former OpenAI transport implementation was retired in Phase E. This module
exists to make the migration decision explicit; provider selection rejects
``openai`` and ``legacy_openai`` and no runtime code imports or calls this file.
"""

DISABLED_REASON = (
    "The OpenAI adapter is a previous candidate and is disabled under the "
    "Gemini Free Tier direction."
)
