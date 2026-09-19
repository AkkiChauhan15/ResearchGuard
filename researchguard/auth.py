"""Supabase access-token verification for FastAPI authorization."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import jwt


ALLOWED_ALGORITHMS = ("ES256", "RS256")
MAX_TOKEN_BYTES = 8_192


class AuthenticationError(ValueError):
    """The supplied credential is absent or did not verify."""


class AuthenticationUnavailable(RuntimeError):
    """The configured identity service cannot currently verify credentials."""


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str | None


class SupabaseTokenVerifier:
    """Verify asymmetric Supabase JWTs without trusting browser identity fields."""

    def __init__(
        self,
        project_url: str | None,
        audience: str = "authenticated",
        *,
        jwks_client: Any | None = None,
    ):
        self.project_url = project_url.rstrip("/") if project_url else None
        self.audience = audience
        self.issuer = f"{self.project_url}/auth/v1" if self.project_url else None
        self.jwks_url = f"{self.issuer}/.well-known/jwks.json" if self.issuer else None
        self.jwks_client = jwks_client
        if self.jwks_client is None and self.jwks_url:
            self.jwks_client = jwt.PyJWKClient(
                self.jwks_url,
                cache_keys=True,
                lifespan=600,
                timeout=5,
                headers={"User-Agent": "ResearchGuardAI/0.3 local-auth-verifier"},
            )

    def verify(self, token: str) -> AuthenticatedUser:
        if not self.project_url or not self.jwks_client:
            raise AuthenticationUnavailable(
                "Authentication is unavailable: configure SUPABASE_URL on the backend."
            )
        if not isinstance(token, str) or not token or len(token.encode("utf-8")) > MAX_TOKEN_BYTES:
            raise AuthenticationError("Authentication required: access token is invalid or expired.")
        try:
            header = jwt.get_unverified_header(token)
            algorithm = header.get("alg")
            key_id = header.get("kid")
            if algorithm not in ALLOWED_ALGORITHMS or not isinstance(key_id, str) or not key_id:
                raise AuthenticationError("Authentication required: access token is invalid or expired.")
            signing_key = self.jwks_client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=[algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iss", "aud", "sub", "role"]},
            )
            subject = claims.get("sub")
            role = claims.get("role")
            if role != "authenticated" or not isinstance(subject, str):
                raise AuthenticationError("Authentication required: access token is invalid or expired.")
            user_id = str(UUID(subject))
            email = claims.get("email")
            if email is not None and not isinstance(email, str):
                email = None
            return AuthenticatedUser(user_id=user_id, email=email)
        except AuthenticationError:
            raise
        except jwt.exceptions.PyJWKClientConnectionError:
            raise AuthenticationUnavailable(
                "Authentication verification is temporarily unavailable; retry later."
            ) from None
        except (jwt.PyJWTError, ValueError, TypeError):
            raise AuthenticationError(
                "Authentication required: access token is invalid or expired."
            ) from None


def bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise AuthenticationError("Authentication required: sign in with Google first.")
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token or " " in token:
        raise AuthenticationError("Authentication required: access token is malformed.")
    return token
