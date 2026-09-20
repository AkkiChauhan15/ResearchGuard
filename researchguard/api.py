"""FastAPI HTTP adapter for the existing Research Guard services."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import mimetypes
from pathlib import Path
import re
from dataclasses import asdict, dataclass
from typing import Annotated, Callable, Literal
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Path as ApiPath, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import Field, field_validator, model_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .assessment import assess, extract
from .chat import ChatProviderError, ChatRateLimiter, ChatService, ProviderMessage
from .auth import (
    AuthenticatedUser,
    AuthenticationError,
    AuthenticationUnavailable,
    SupabaseTokenVerifier,
    bearer_token,
)
from .providers import provider_status
from .persistence import (
    PersistenceConflict,
    PersistenceNotFound,
    PersistencePermissionDenied,
    PersistenceUnavailable,
    SupabaseReviewRepository,
)
from .demo import demo_review
from .export import export_review, validate_review
from .retrieval import classify_url, retrieve
from .reviews import create_review, decide, edit_claim, edit_context
from .schemas import Context, Decision, Review, ReviewInput, Strict
from .settings import Settings
from .store import ReviewEntry, ReviewStore


ROOT = Path(__file__).resolve().parent.parent
REVIEW_ID_PATTERN = r"review_[0-9a-f]{32}"
CLAIM_ID_PATTERN = r"claim_[0-9a-f]{32}"
SESSION_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
SESSION_HEADER = "X-Review-Session"
ReviewId = Annotated[str, ApiPath(pattern=REVIEW_ID_PATTERN)]
ClaimId = Annotated[str, ApiPath(pattern=CLAIM_ID_PATTERN)]
SessionId = Annotated[str, Header(alias=SESSION_HEADER)]
Authorization = Annotated[str | None, Header(alias="Authorization")]
SavedReviewId = Annotated[UUID, ApiPath()]


class ClaimEdit(Strict):
    text: str = Field(min_length=1, max_length=12000)


class RetrievalRequest(Strict):
    query: str = Field(min_length=1, max_length=500)


class DecisionRequest(Strict):
    decision: Decision


class SaveReviewRequest(Strict):
    review_id: str = Field(pattern=f"^{REVIEW_ID_PATTERN}$")


class UpdateSavedReviewRequest(Strict):
    review_id: str = Field(pattern=f"^{REVIEW_ID_PATTERN}$")
    expected_revision: int = Field(ge=1)


class ChatMessageRequest(Strict):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Chat messages cannot be blank.")
        return value


class ChatRequest(Strict):
    provider: Literal["groq", "openrouter", "gemini", "nvidia"]
    model: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9._:/-]+$")
    messages: list[ChatMessageRequest] = Field(min_length=1, max_length=24)
    allow_fallback: bool = False

    @model_validator(mode="after")
    def validate_conversation(self):
        if self.messages[-1].role != "user":
            raise ValueError("The last chat message must be from the user.")
        if sum(len(message.content) for message in self.messages) > 24_000:
            raise ValueError("Chat history exceeds the 24,000-character limit.")
        return self


@dataclass(frozen=True)
class AuthenticatedRequest:
    user: AuthenticatedUser
    access_token: str


def _error(status: int, detail: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": detail}, headers=headers)


class RequestSizeLimitMiddleware:
    """Bound request bodies before FastAPI attempts JSON parsing."""

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = self.max_bytes + 1
        if declared > self.max_bytes:
            await _error(413, f"Request body exceeds {self.max_bytes} bytes.")(scope, receive, send)
            return
        chunks: list[bytes] = []
        total = 0
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            total += len(chunk)
            if total > self.max_bytes:
                await _error(413, f"Request body exceeds {self.max_bytes} bytes.")(scope, receive, send)
                return
            chunks.append(chunk)
            more = message.get("more_body", False)
        body = b"".join(chunks)
        content_type = headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower()
        if body and content_type != b"application/json":
            await _error(400, "Send request bodies as application/json.")(scope, receive, send)
            return
        delivered = False

        async def replay():
            nonlocal delivered
            if delivered:
                return {"type": "http.request", "body": b"", "more_body": False}
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay, send)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    legacy_assets = {
        "/legacy": ((ROOT / "web" / "index.html").read_bytes(), "text/html"),
        "/app.js": ((ROOT / "web" / "app.js").read_bytes(), "text/javascript"),
        "/style.css": ((ROOT / "web" / "style.css").read_bytes(), "text/css"),
    }
    built_root = ROOT / "frontend" / "dist"
    built_assets: dict[str, tuple[bytes, str]] = {}
    if (built_root / "index.html").is_file():
        for file_path in built_root.rglob("*"):
            if file_path.is_file():
                url_path = "/" + file_path.relative_to(built_root).as_posix()
                media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
                built_assets[url_path] = (file_path.read_bytes(), media_type)
    primary_index = built_assets.get("/index.html", legacy_assets["/legacy"])

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.store = ReviewStore(settings.session_ttl_seconds, settings.max_reviews)
        application.state.auth_verifier = SupabaseTokenVerifier(
            settings.supabase_url,
            settings.supabase_audience,
        )
        application.state.saved_reviews = SupabaseReviewRepository(
            settings.supabase_url,
            settings.supabase_publishable_key,
            timeout_seconds=settings.persistence_timeout_seconds,
        )
        application.state.chat_service = ChatService(
            fallback_enabled=settings.chat_fallback_enabled,
            provider_timeout_seconds=settings.chat_provider_timeout_seconds,
            max_output_tokens=settings.chat_max_output_tokens,
        )
        application.state.chat_rate_limiter = ChatRateLimiter(settings.chat_requests_per_minute)
        application.state.external_executor = ThreadPoolExecutor(
            max_workers=settings.external_concurrency,
            thread_name_prefix="researchguard-external",
        )
        try:
            yield
        finally:
            await application.state.saved_reviews.close()
            application.state.external_executor.shutdown(wait=True, cancel_futures=True)

    application = FastAPI(
        title="Research Guard AI local API",
        version="0.5.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    application.state.settings = settings
    application.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.max_request_bytes)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.frontend_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", SESSION_HEADER],
        max_age=600,
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(settings.allowed_hosts),
    )

    @application.middleware("http")
    async def local_origin_and_security_headers(request: Request, call_next):
        origin = request.headers.get("origin")
        request_origin = f"{request.url.scheme}://{request.headers.get('host', '')}".rstrip("/")
        origin_allowed = bool(
            origin and origin.rstrip("/") in {*settings.frontend_origins, request_origin}
        )
        if origin and not origin_allowed:
            response = _error(400, "Cross-origin requests are not allowed.")
        elif request.headers.get("sec-fetch-site") == "cross-site" and not origin_allowed:
            response = _error(400, "Cross-site requests are not allowed.")
        else:
            response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self' "
            + " ".join(settings.frontend_origins + ((settings.supabase_url,) if settings.supabase_url else ()))
            + "; img-src 'self'; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        return response

    @application.exception_handler(RequestValidationError)
    async def request_validation_error(_request: Request, _exc: RequestValidationError):
        return _error(400, "Invalid input fields or values. Check required fields and size limits.")

    @application.exception_handler(LookupError)
    async def lookup_error(_request: Request, exc: LookupError):
        return _error(404, str(exc))

    @application.exception_handler(ValueError)
    async def value_error(_request: Request, exc: ValueError):
        return _error(400, str(exc))

    @application.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException):
        return _error(exc.status_code, str(exc.detail), exc.headers)

    @application.exception_handler(Exception)
    async def unexpected_error(_request: Request, _exc: Exception):
        return _error(500, "Local service failed. No assessment was fabricated. Retry or inspect the local setup.")

    @application.exception_handler(PersistenceNotFound)
    async def persistence_not_found(_request: Request, exc: PersistenceNotFound):
        return _error(404, str(exc))

    @application.exception_handler(PersistenceConflict)
    async def persistence_conflict(_request: Request, exc: PersistenceConflict):
        return _error(409, str(exc))

    @application.exception_handler(PersistencePermissionDenied)
    async def persistence_permission(_request: Request, exc: PersistencePermissionDenied):
        return _error(403, str(exc))

    @application.exception_handler(PersistenceUnavailable)
    async def persistence_unavailable(_request: Request, exc: PersistenceUnavailable):
        return _error(503, str(exc))

    def session(value: str) -> str:
        if not SESSION_PATTERN.fullmatch(value):
            raise ValueError("A valid browser review session is required.")
        return value

    async def add_review(session_id: str, review: Review, owner_id: str | None = None) -> Review:
        validate_review(review)
        if len(review.model_dump_json().encode("utf-8")) > settings.max_review_bytes:
            raise ValueError("Review size limit reached; export and start a new review.")
        await application.state.store.add(session_id, review, owner_id)
        return review

    async def run_in_external_pool(operation: Callable, *args, timeout: float, **kwargs):
        """Await a bounded worker without relying on Python's executor wakeup bridge."""
        future = application.state.external_executor.submit(operation, *args, **kwargs)
        deadline = asyncio.get_running_loop().time() + timeout
        while not future.done():
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                future.cancel()
                raise HTTPException(504, "External operation timed out; no partial review changes were saved.")
            await asyncio.sleep(min(0.01, remaining))
        return future.result()

    async def authenticated_request(authorization: str | None) -> AuthenticatedRequest:
        try:
            token = bearer_token(authorization)
            user = await run_in_external_pool(
                application.state.auth_verifier.verify,
                token,
                timeout=settings.auth_timeout_seconds,
            )
            return AuthenticatedRequest(user=user, access_token=token)
        except AuthenticationError as exc:
            raise HTTPException(
                401,
                str(exc),
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        except AuthenticationUnavailable as exc:
            raise HTTPException(503, str(exc)) from None

    async def authenticated_user(authorization: str | None) -> AuthenticatedUser:
        return (await authenticated_request(authorization)).user

    async def review_owner(
        session_id: str,
        review_id: str,
        authorization: str | None,
    ) -> str | None:
        entry = await application.state.store.get_session_entry(session_id, review_id)
        if entry.review.mode == "demo" and entry.owner_id is None:
            return None
        user = await authenticated_user(authorization)
        if entry.owner_id != user.user_id:
            raise LookupError("Review not found in this session, or expired. Start a new review.")
        return user.user_id

    async def mutate(
        session_id: str,
        review_id: str,
        operation: Callable[[Review], None],
        *,
        owner_id: str | None = None,
        offload: bool = False,
        timeout: float | None = None,
    ) -> Review:
        entry: ReviewEntry = await application.state.store.get_entry(session_id, review_id, owner_id)
        async with entry.lock:
            current = await application.state.store.get_entry(session_id, review_id, owner_id)
            if current is not entry:
                raise LookupError("Review expired while processing. Start a new review.")
            review = entry.review.model_copy(deep=True)
            if offload:
                await run_in_external_pool(operation, review, timeout=timeout)
            else:
                operation(review)
            validate_review(review)
            if len(review.model_dump_json().encode("utf-8")) > settings.max_review_bytes:
                raise ValueError("Review size limit reached; export and start a new review.")
            await application.state.store.commit(session_id, review_id, entry, review, owner_id)
            return review

    @application.get("/api/health")
    async def health():
        return {"status": "ok", "service": "researchguard-api", "storage": "temporary-process-memory"}

    @application.get("/", include_in_schema=False)
    @application.get("/login", include_in_schema=False)
    @application.get("/signup", include_in_schema=False)
    @application.get("/forgot-password", include_in_schema=False)
    @application.get("/update-password", include_in_schema=False)
    @application.get("/account", include_in_schema=False)
    @application.get("/chat", include_in_schema=False)
    async def primary_frontend():
        content, media_type = primary_index
        return Response(content=content, media_type=media_type)

    @application.get("/legacy", include_in_schema=False)
    @application.get("/app.js", include_in_schema=False)
    @application.get("/style.css", include_in_schema=False)
    async def legacy_frontend(request: Request):
        content, media_type = legacy_assets[request.url.path]
        return Response(content=content, media_type=media_type)

    @application.get("/favicon.svg", include_in_schema=False)
    async def frontend_favicon():
        asset = built_assets.get("/favicon.svg")
        if asset is None:
            raise HTTPException(404, "Frontend asset not found.")
        return Response(content=asset[0], media_type=asset[1])

    @application.get("/assets/{asset_path:path}", include_in_schema=False)
    async def frontend_asset(asset_path: str):
        asset = built_assets.get(f"/assets/{asset_path}")
        if asset is None:
            raise HTTPException(404, "Frontend asset not found.")
        return Response(content=asset[0], media_type=asset[1])

    @application.get("/api/config")
    async def config():
        status = provider_status()
        return {
            "model_configured": status.available,
            "model_state": status.state,
            "model_provider": status.provider,
            "extraction_model": status.extraction_model,
            "assessment_model": status.assessment_model,
            "model_detail": status.detail,
            "retention_seconds": settings.session_ttl_seconds,
            "mode": "local preview",
            "auth_configured": settings.supabase_url is not None,
            "auth_state": "configured" if settings.supabase_url else "unavailable_missing_configuration",
            "auth_provider": "supabase_google",
            "live_auth_required": True,
            "persistence_configured": application.state.saved_reviews.configured,
            "persistence_state": (
                "configured" if application.state.saved_reviews.configured
                else "unavailable_missing_configuration"
            ),
        }

    @application.get("/api/auth/me")
    async def auth_me(authorization: Authorization = None):
        user = await authenticated_user(authorization)
        return {"user_id": user.user_id, "email": user.email}

    @application.get("/api/chat/providers")
    async def chat_providers(authorization: Authorization = None):
        await authenticated_user(authorization)
        return application.state.chat_service.public_status()

    @application.post("/api/chat")
    async def chat(payload: ChatRequest, authorization: Authorization = None):
        user = await authenticated_user(authorization)
        retry_after = await application.state.chat_rate_limiter.check(user.user_id)
        if retry_after is not None:
            raise HTTPException(
                429,
                "Chat request limit reached. Wait before trying again.",
                headers={"Retry-After": str(retry_after)},
            )
        try:
            result = await run_in_external_pool(
                application.state.chat_service.complete,
                payload.provider,
                payload.model,
                tuple(ProviderMessage(item.role, item.content) for item in payload.messages),
                allow_fallback=payload.allow_fallback,
                total_timeout_seconds=settings.chat_timeout_seconds,
                timeout=settings.chat_timeout_seconds + 1,
            )
        except ChatProviderError as exc:
            status = 429 if exc.category == "rate_limited" else 504 if exc.category == "timeout" else 503
            raise HTTPException(status, exc.detail) from None
        return {"success": True, **asdict(result)}

    async def local_review_for_save(
        session_id: str,
        review_id: str,
        user: AuthenticatedUser,
    ) -> Review:
        session_id = session(session_id)
        entry = await application.state.store.get_session_entry(session_id, review_id)
        if entry.owner_id is not None and entry.owner_id != user.user_id:
            raise LookupError("Review not found in this session, or expired. Start a new review.")
        owner_id = entry.owner_id
        review = await application.state.store.snapshot(session_id, review_id, owner_id)
        validate_review(review)
        return review

    @application.get("/api/saved-reviews")
    async def list_saved_reviews(authorization: Authorization = None):
        identity = await authenticated_request(authorization)
        records = await application.state.saved_reviews.list(identity.access_token)
        return {"items": [record.as_dict() for record in records]}

    @application.post("/api/saved-reviews", status_code=201)
    async def save_review(payload: SaveReviewRequest, session_id: SessionId, authorization: Authorization = None):
        identity = await authenticated_request(authorization)
        review = await local_review_for_save(session_id, payload.review_id, identity.user)
        saved = await application.state.saved_reviews.create(identity.access_token, review)
        return saved.as_dict()

    @application.post("/api/saved-reviews/{saved_id}/open")
    async def open_saved_review(saved_id: SavedReviewId, session_id: SessionId, authorization: Authorization = None):
        identity = await authenticated_request(authorization)
        saved = await application.state.saved_reviews.get(identity.access_token, str(saved_id))
        await add_review(session(session_id), saved.review.model_copy(deep=True), identity.user.user_id)
        return saved.as_dict()

    @application.put("/api/saved-reviews/{saved_id}")
    async def update_saved_review(saved_id: SavedReviewId, payload: UpdateSavedReviewRequest, session_id: SessionId, authorization: Authorization = None):
        identity = await authenticated_request(authorization)
        review = await local_review_for_save(session_id, payload.review_id, identity.user)
        current = await application.state.saved_reviews.get(identity.access_token, str(saved_id))
        if current.summary.review_id != review.review_id:
            raise ValueError("The open review does not match this saved record.")
        if current.summary.revision != payload.expected_revision:
            raise PersistenceConflict(
                "The saved review changed elsewhere. Your local review was kept; reopen the saved copy before updating."
            )
        saved = await application.state.saved_reviews.update(
            identity.access_token,
            str(saved_id),
            payload.expected_revision,
            review,
        )
        return saved.as_dict()

    @application.get("/api/saved-reviews/{saved_id}/export")
    async def export_saved_review(saved_id: SavedReviewId, authorization: Authorization = None, format: Annotated[Literal["json", "txt"], Query()] = "json"):
        identity = await authenticated_request(authorization)
        saved = await application.state.saved_reviews.get(identity.access_token, str(saved_id))
        content = await run_in_external_pool(
            export_review,
            saved.review,
            format,
            timeout=settings.assessment_timeout_seconds,
        )
        media_type = "application/json" if format == "json" else "text/plain"
        headers = {"Content-Disposition": f'attachment; filename="research-guard-saved-{saved.review.mode}.{format}"'}
        return Response(content=content, media_type=media_type, headers=headers)

    @application.delete("/api/saved-reviews/{saved_id}")
    async def delete_saved_review(saved_id: SavedReviewId, expected_revision: Annotated[int, Query(ge=1)], authorization: Authorization = None):
        identity = await authenticated_request(authorization)
        deleted = await application.state.saved_reviews.delete(
            identity.access_token,
            str(saved_id),
            expected_revision,
        )
        return {"deleted": deleted.as_dict()}

    @application.post("/api/reviews", response_model=Review)
    async def create_live_review(payload: ReviewInput, session_id: SessionId, authorization: Authorization = None):
        user = await authenticated_user(authorization)
        for url in payload.source_urls:
            classify_url(url)
        return await add_review(session(session_id), create_review(payload), user.user_id)

    @application.post("/api/reviews/demo", response_model=Review)
    async def create_demo_review(session_id: SessionId):
        return await add_review(session(session_id), demo_review())

    @application.get("/api/reviews/{review_id}", response_model=Review)
    async def get_review(review_id: ReviewId, session_id: SessionId, authorization: Authorization = None):
        session_id = session(session_id)
        owner_id = await review_owner(session_id, review_id, authorization)
        return await application.state.store.snapshot(session_id, review_id, owner_id)

    @application.patch("/api/reviews/{review_id}/claims/{claim_id}", response_model=Review)
    async def update_claim(review_id: ReviewId, claim_id: ClaimId, payload: ClaimEdit, session_id: SessionId, authorization: Authorization = None):
        session_id = session(session_id)
        owner_id = await review_owner(session_id, review_id, authorization)
        return await mutate(session_id, review_id, lambda review: edit_claim(review, claim_id, payload.text), owner_id=owner_id)

    @application.patch("/api/reviews/{review_id}/context", response_model=Review)
    async def update_context(review_id: ReviewId, payload: Context, session_id: SessionId, authorization: Authorization = None):
        session_id = session(session_id)
        owner_id = await review_owner(session_id, review_id, authorization)
        return await mutate(session_id, review_id, lambda review: edit_context(review, payload), owner_id=owner_id)

    @application.post("/api/reviews/{review_id}/extraction", response_model=Review)
    async def extract_claims(review_id: ReviewId, session_id: SessionId, authorization: Authorization = None):
        def operation(review: Review) -> None:
            if len(review.model_runs) >= 30:
                raise ValueError("Model call limit reached for this review.")
            extract(review)
        session_id = session(session_id)
        owner_id = await review_owner(session_id, review_id, authorization)
        return await mutate(session_id, review_id, operation, owner_id=owner_id, offload=True, timeout=settings.assessment_timeout_seconds)

    @application.post("/api/reviews/{review_id}/claims/{claim_id}/retrievals", response_model=Review)
    async def retrieve_sources(review_id: ReviewId, claim_id: ClaimId, payload: RetrievalRequest, session_id: SessionId, authorization: Authorization = None):
        def operation(review: Review) -> None:
            if len(review.attempts) >= 60:
                raise ValueError("Retrieval history limit reached; export and start a new review.")
            retrieve(review, claim_id, payload.query)
        session_id = session(session_id)
        owner_id = await review_owner(session_id, review_id, authorization)
        return await mutate(session_id, review_id, operation, owner_id=owner_id, offload=True, timeout=settings.retrieval_timeout_seconds)

    @application.post("/api/reviews/{review_id}/claims/{claim_id}/assessment", response_model=Review)
    async def assess_claim(review_id: ReviewId, claim_id: ClaimId, session_id: SessionId, authorization: Authorization = None):
        def operation(review: Review) -> None:
            if len(review.model_runs) >= 30:
                raise ValueError("Model call limit reached for this review.")
            assess(review, claim_id)
        session_id = session(session_id)
        owner_id = await review_owner(session_id, review_id, authorization)
        return await mutate(session_id, review_id, operation, owner_id=owner_id, offload=True, timeout=settings.assessment_timeout_seconds)

    @application.put("/api/reviews/{review_id}/claims/{claim_id}/decision", response_model=Review)
    async def record_decision(review_id: ReviewId, claim_id: ClaimId, payload: DecisionRequest, session_id: SessionId, authorization: Authorization = None):
        session_id = session(session_id)
        owner_id = await review_owner(session_id, review_id, authorization)
        return await mutate(session_id, review_id, lambda review: decide(review, claim_id, payload.decision), owner_id=owner_id)

    @application.get("/api/reviews/{review_id}/export")
    async def export(review_id: ReviewId, session_id: SessionId, authorization: Authorization = None, format: Annotated[Literal["json", "txt"], Query()] = "json"):
        session_id = session(session_id)
        owner_id = await review_owner(session_id, review_id, authorization)
        review = await application.state.store.snapshot(session_id, review_id, owner_id)
        content = await run_in_external_pool(
            export_review, review, format, timeout=settings.assessment_timeout_seconds
        )
        media_type = "application/json" if format == "json" else "text/plain"
        headers = {"Content-Disposition": f'attachment; filename="research-guard-{review.mode}.{format}"'}
        return Response(content=content, media_type=media_type, headers=headers)

    return application


app = create_app()
