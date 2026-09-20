"""Validated local runtime settings for the FastAPI HTTP adapter."""
from dataclasses import dataclass
import os
from urllib.parse import urlsplit
import re


DEFAULT_FRONTEND_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)

DEFAULT_ALLOWED_HOSTS = (
    "127.0.0.1",
    "localhost",
    "testserver",
)


def _supabase_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    candidate = value.strip().rstrip("/")
    parsed = urlsplit(candidate)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".supabase.co")
        or parsed.hostname == "supabase.co"
        or parsed.port is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError("SUPABASE_URL must be an exact https://<project-ref>.supabase.co origin.")
    return candidate


def _supabase_publishable_key(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    candidate = value.strip()
    if not re.fullmatch(r"sb_publishable_[A-Za-z0-9_-]{10,}", candidate):
        raise ValueError("SUPABASE_PUBLISHABLE_KEY must be a publishable key, never a secret key.")
    return candidate


def _positive_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer.") from None
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return value


def _boolean(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes"}:
        return True
    if value in {"0", "false", "no"}:
        return False
    raise ValueError(f"{name} must be true or false.")


def _origins(value: str | None) -> tuple[str, ...]:
    values = DEFAULT_FRONTEND_ORIGINS if value is None else tuple(
        item.strip().rstrip("/") for item in value.split(",") if item.strip()
    )
    if not values:
        raise ValueError("RESEARCHGUARD_FRONTEND_ORIGINS must contain an origin.")
    for origin in values:
        parsed = urlsplit(origin)
        local_http = (
            parsed.scheme == "http"
            and parsed.hostname in {"127.0.0.1", "localhost"}
            and parsed.port is not None
        )
        hosted_https = parsed.scheme == "https" and parsed.hostname is not None
        if not (local_http or hosted_https) or any(
            (parsed.path, parsed.query, parsed.fragment, parsed.username, parsed.password)
        ):
            raise ValueError(
                "RESEARCHGUARD_FRONTEND_ORIGINS accepts exact local HTTP origins with ports "
                "or exact HTTPS origins only."
            )
    return values


def _allowed_hosts(value: str | None, render_hostname: str | None) -> tuple[str, ...]:
    values = list(DEFAULT_ALLOWED_HOSTS)
    for raw in (value, render_hostname):
        if not raw:
            continue
        values.extend(item.strip().lower() for item in raw.split(",") if item.strip())
    unique = tuple(dict.fromkeys(values))
    for host in unique:
        parsed = urlsplit(f"//{host}")
        if (
            host == "*"
            or parsed.hostname != host
            or parsed.port is not None
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or not re.fullmatch(r"[a-z0-9.-]+", host)
            or ".." in host
            or host.startswith(".")
            or host.endswith(".")
        ):
            raise ValueError(
                "RESEARCHGUARD_ALLOWED_HOSTS accepts exact hostnames only, without schemes, ports, or wildcards."
            )
    return unique


@dataclass(frozen=True)
class Settings:
    frontend_origins: tuple[str, ...] = DEFAULT_FRONTEND_ORIGINS
    allowed_hosts: tuple[str, ...] = DEFAULT_ALLOWED_HOSTS
    session_ttl_seconds: int = 3600
    max_reviews: int = 24
    max_review_bytes: int = 5_000_000
    max_request_bytes: int = 100_000
    external_concurrency: int = 4
    retrieval_timeout_seconds: float = 90
    assessment_timeout_seconds: float = 130
    auth_timeout_seconds: float = 10
    persistence_timeout_seconds: float = 10
    chat_timeout_seconds: float = 45
    chat_provider_timeout_seconds: float = 20
    chat_requests_per_minute: int = 6
    chat_max_output_tokens: int = 1024
    chat_fallback_enabled: bool = False
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_audience: str = "authenticated"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            frontend_origins=_origins(os.environ.get("RESEARCHGUARD_FRONTEND_ORIGINS")),
            allowed_hosts=_allowed_hosts(
                os.environ.get("RESEARCHGUARD_ALLOWED_HOSTS"),
                os.environ.get("RENDER_EXTERNAL_HOSTNAME"),
            ),
            session_ttl_seconds=_positive_int("RESEARCHGUARD_SESSION_TTL_SECONDS", 3600, 60, 86400),
            max_reviews=_positive_int("RESEARCHGUARD_MAX_REVIEWS", 24, 1, 1000),
            max_review_bytes=_positive_int("RESEARCHGUARD_MAX_REVIEW_BYTES", 5_000_000, 100_000, 20_000_000),
            max_request_bytes=_positive_int("RESEARCHGUARD_MAX_REQUEST_BYTES", 100_000, 1_000, 2_000_000),
            external_concurrency=_positive_int("RESEARCHGUARD_EXTERNAL_CONCURRENCY", 4, 1, 16),
            retrieval_timeout_seconds=_positive_int("RESEARCHGUARD_RETRIEVAL_TIMEOUT_SECONDS", 90, 1, 300),
            assessment_timeout_seconds=_positive_int("RESEARCHGUARD_ASSESSMENT_TIMEOUT_SECONDS", 130, 1, 300),
            auth_timeout_seconds=_positive_int("RESEARCHGUARD_AUTH_TIMEOUT_SECONDS", 10, 1, 30),
            persistence_timeout_seconds=_positive_int("RESEARCHGUARD_PERSISTENCE_TIMEOUT_SECONDS", 10, 1, 30),
            chat_timeout_seconds=_positive_int("RESEARCHGUARD_CHAT_TIMEOUT_SECONDS", 45, 5, 120),
            chat_provider_timeout_seconds=_positive_int("RESEARCHGUARD_CHAT_PROVIDER_TIMEOUT_SECONDS", 20, 2, 60),
            chat_requests_per_minute=_positive_int("RESEARCHGUARD_CHAT_REQUESTS_PER_MINUTE", 6, 1, 60),
            chat_max_output_tokens=_positive_int("RESEARCHGUARD_CHAT_MAX_OUTPUT_TOKENS", 1024, 128, 4096),
            chat_fallback_enabled=_boolean("RESEARCHGUARD_CHAT_FALLBACK_ENABLED", False),
            supabase_url=_supabase_url(os.environ.get("SUPABASE_URL")),
            supabase_publishable_key=_supabase_publishable_key(os.environ.get("SUPABASE_PUBLISHABLE_KEY")),
            supabase_audience="authenticated",
        )
