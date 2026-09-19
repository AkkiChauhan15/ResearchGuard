"""Validated local runtime settings for the FastAPI HTTP adapter."""
from dataclasses import dataclass
import os
from urllib.parse import urlsplit


DEFAULT_FRONTEND_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
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


def _positive_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer.") from None
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return value


def _origins(value: str | None) -> tuple[str, ...]:
    values = DEFAULT_FRONTEND_ORIGINS if value is None else tuple(
        item.strip().rstrip("/") for item in value.split(",") if item.strip()
    )
    if not values:
        raise ValueError("RESEARCHGUARD_FRONTEND_ORIGINS must contain an origin.")
    for origin in values:
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"127.0.0.1", "localhost"}
            or parsed.port is None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.username
        ):
            raise ValueError(
                "RESEARCHGUARD_FRONTEND_ORIGINS accepts explicit local HTTP origins with ports only."
            )
    return values


@dataclass(frozen=True)
class Settings:
    frontend_origins: tuple[str, ...] = DEFAULT_FRONTEND_ORIGINS
    session_ttl_seconds: int = 3600
    max_reviews: int = 24
    max_review_bytes: int = 5_000_000
    max_request_bytes: int = 100_000
    external_concurrency: int = 4
    retrieval_timeout_seconds: float = 90
    assessment_timeout_seconds: float = 130
    auth_timeout_seconds: float = 10
    supabase_url: str | None = None
    supabase_audience: str = "authenticated"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            frontend_origins=_origins(os.environ.get("RESEARCHGUARD_FRONTEND_ORIGINS")),
            session_ttl_seconds=_positive_int("RESEARCHGUARD_SESSION_TTL_SECONDS", 3600, 60, 86400),
            max_reviews=_positive_int("RESEARCHGUARD_MAX_REVIEWS", 24, 1, 1000),
            max_review_bytes=_positive_int("RESEARCHGUARD_MAX_REVIEW_BYTES", 5_000_000, 100_000, 20_000_000),
            max_request_bytes=_positive_int("RESEARCHGUARD_MAX_REQUEST_BYTES", 100_000, 1_000, 2_000_000),
            external_concurrency=_positive_int("RESEARCHGUARD_EXTERNAL_CONCURRENCY", 4, 1, 16),
            retrieval_timeout_seconds=_positive_int("RESEARCHGUARD_RETRIEVAL_TIMEOUT_SECONDS", 90, 1, 300),
            assessment_timeout_seconds=_positive_int("RESEARCHGUARD_ASSESSMENT_TIMEOUT_SECONDS", 130, 1, 300),
            auth_timeout_seconds=_positive_int("RESEARCHGUARD_AUTH_TIMEOUT_SECONDS", 10, 1, 30),
            supabase_url=_supabase_url(os.environ.get("SUPABASE_URL")),
            supabase_audience="authenticated",
        )
