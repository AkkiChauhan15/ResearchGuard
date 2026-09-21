"""Owner-scoped Supabase persistence and PDF export for AI chat conversations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Literal
from uuid import UUID
from xml.sax.saxutils import escape

import httpx
from pydantic import Field, ValidationError, field_validator, model_validator

from .persistence import (
    PersistenceConflict,
    PersistenceNotFound,
    PersistencePermissionDenied,
    PersistenceUnavailable,
)
from .schemas import Strict


SAVED_CHAT_SCHEMA_VERSION = 1
ROW_COLUMNS = "id,schema_version,revision,title,message_count,last_provider,last_model,created_at,updated_at,record"
SUMMARY_COLUMNS = "id,schema_version,revision,title,message_count,last_provider,last_model,created_at,updated_at"
MAX_CHAT_RECORD_BYTES = 250_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SavedChatMessage(Strict):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8_000)
    timestamp: str = Field(default_factory=_now, max_length=64)
    provider: str | None = Field(default=None, max_length=40)
    model: str | None = Field(default=None, max_length=120)
    fallback_used: bool = False

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            raise ValueError("Chat message timestamps must use ISO 8601.") from None
        if parsed.tzinfo is None:
            raise ValueError("Chat message timestamps must include a timezone.")
        return value

    @model_validator(mode="after")
    def validate_provenance(self):
        if self.role == "user" and (self.provider is not None or self.model is not None or self.fallback_used):
            raise ValueError("User chat messages cannot contain model provenance.")
        if self.role == "assistant" and (not self.provider or not self.model):
            raise ValueError("Assistant chat messages require provider and model provenance.")
        return self


class SavedChatPayload(Strict):
    messages: list[SavedChatMessage] = Field(min_length=2, max_length=24)

    @model_validator(mode="after")
    def validate_turns(self):
        if len(self.messages) % 2:
            raise ValueError("Saved chats must contain complete user and assistant turns.")
        for index, message in enumerate(self.messages):
            expected = "user" if index % 2 == 0 else "assistant"
            if message.role != expected:
                raise ValueError("Saved chat roles must alternate from user to assistant.")
        return self


@dataclass(frozen=True)
class SavedChatSummary:
    chat_id: str
    schema_version: int
    revision: int
    title: str
    message_count: int
    last_provider: str
    last_model: str
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "chat_id": self.chat_id,
            "schema_version": self.schema_version,
            "revision": self.revision,
            "title": self.title,
            "message_count": self.message_count,
            "last_provider": self.last_provider,
            "last_model": self.last_model,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class SavedChatRecord:
    summary: SavedChatSummary
    messages: tuple[SavedChatMessage, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.summary.as_dict(),
            "messages": [message.model_dump(mode="json") for message in self.messages],
        }


def _title(messages: list[SavedChatMessage] | tuple[SavedChatMessage, ...]) -> str:
    first_user = next(message.content for message in messages if message.role == "user")
    return " ".join(first_user.split())[:160] or "Untitled chat"


def _summary(row: dict[str, Any]) -> SavedChatSummary:
    try:
        summary = SavedChatSummary(
            chat_id=str(UUID(str(row["id"]))),
            schema_version=int(row["schema_version"]),
            revision=int(row["revision"]),
            title=str(row["title"]),
            message_count=int(row["message_count"]),
            last_provider=str(row["last_provider"]),
            last_model=str(row["last_model"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
    except (KeyError, TypeError, ValueError):
        raise PersistenceUnavailable("Saved-chat service returned malformed metadata.") from None
    if (
        summary.schema_version != SAVED_CHAT_SCHEMA_VERSION
        or summary.revision < 1
        or not 1 <= len(summary.title) <= 160
        or summary.message_count < 2
        or summary.message_count > 24
        or summary.message_count % 2
        or not summary.last_provider
        or not summary.last_model
    ):
        raise PersistenceUnavailable("Saved-chat service returned unsupported metadata.")
    return summary


def _record(row: dict[str, Any]) -> SavedChatRecord:
    summary = _summary(row)
    try:
        payload = SavedChatPayload.model_validate(row["record"])
    except (KeyError, ValidationError, ValueError):
        raise PersistenceUnavailable("Saved chat failed its canonical message schema.") from None
    if (
        len(payload.messages) != summary.message_count
        or _title(payload.messages) != summary.title
        or payload.messages[-1].provider != summary.last_provider
        or payload.messages[-1].model != summary.last_model
    ):
        raise PersistenceUnavailable("Saved-chat metadata does not match its canonical messages.")
    return SavedChatRecord(summary=summary, messages=tuple(payload.messages))


class SupabaseChatRepository:
    """Use the signed-in user's access token so Supabase RLS remains authoritative."""

    def __init__(
        self,
        project_url: str | None,
        publishable_key: str | None,
        *,
        timeout_seconds: float = 10,
        client: httpx.AsyncClient | None = None,
    ):
        self.project_url = project_url.rstrip("/") if project_url else None
        self.publishable_key = publishable_key.strip() if publishable_key else None
        self.configured = bool(self.project_url and self.publishable_key)
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url=self.project_url or "https://unconfigured.invalid",
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
            headers={"User-Agent": "ResearchGuardAI/0.6 saved-chat"},
        )

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    def _headers(self, access_token: str, *, write: bool = False) -> dict[str, str]:
        if not self.configured:
            raise PersistenceUnavailable(
                "Saved chats are unavailable: configure SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY."
            )
        headers = {
            "apikey": self.publishable_key or "",
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        if write:
            headers.update({"Content-Type": "application/json", "Prefer": "return=representation"})
        return headers

    @staticmethod
    async def _payload(response: httpx.Response) -> list[dict[str, Any]]:
        if response.status_code in {401, 403}:
            raise PersistencePermissionDenied("Saved-chat access was denied by authentication or row-level security.")
        if response.status_code == 409:
            raise PersistenceConflict("The saved chat changed elsewhere. Reload it before continuing.")
        if response.status_code >= 500:
            raise PersistenceUnavailable("Saved-chat service is temporarily unavailable. The message was not saved.")
        if response.status_code >= 400:
            raise PersistenceUnavailable("Saved-chat request failed. The message was not saved.")
        try:
            payload = response.json()
        except ValueError:
            raise PersistenceUnavailable("Saved-chat service returned malformed JSON.") from None
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            raise PersistenceUnavailable("Saved-chat service returned an unexpected response.")
        return payload

    @staticmethod
    def _body(messages: list[SavedChatMessage] | tuple[SavedChatMessage, ...]) -> dict[str, Any]:
        payload = SavedChatPayload(messages=list(messages))
        encoded = payload.model_dump_json().encode("utf-8")
        if len(encoded) > MAX_CHAT_RECORD_BYTES:
            raise ValueError("Saved chat exceeds the 250,000-byte limit. Start a new chat.")
        last = payload.messages[-1]
        return {
            "schema_version": SAVED_CHAT_SCHEMA_VERSION,
            "title": _title(payload.messages),
            "message_count": len(payload.messages),
            "last_provider": last.provider,
            "last_model": last.model,
            "record": payload.model_dump(mode="json"),
        }

    async def list(self, access_token: str) -> list[SavedChatSummary]:
        try:
            response = await self.client.get(
                "/rest/v1/saved_chats",
                params={"select": SUMMARY_COLUMNS, "order": "updated_at.desc", "limit": "100"},
                headers=self._headers(access_token),
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-chat service is unreachable.") from None
        return [_summary(row) for row in await self._payload(response)]

    async def get(self, access_token: str, chat_id: str) -> SavedChatRecord:
        try:
            response = await self.client.get(
                "/rest/v1/saved_chats",
                params={"id": f"eq.{chat_id}", "select": ROW_COLUMNS, "limit": "1"},
                headers=self._headers(access_token),
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-chat service is unreachable.") from None
        rows = await self._payload(response)
        if not rows:
            raise PersistenceNotFound("Saved chat not found, or it belongs to another user.")
        return _record(rows[0])

    async def create(self, access_token: str, messages: list[SavedChatMessage]) -> SavedChatRecord:
        body = self._body(messages)
        try:
            response = await self.client.post(
                "/rest/v1/saved_chats",
                params={"select": ROW_COLUMNS},
                headers=self._headers(access_token, write=True),
                json=body,
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-chat service is unreachable. The message was not saved.") from None
        rows = await self._payload(response)
        if len(rows) != 1:
            raise PersistenceUnavailable("Saved-chat service did not confirm the conversation.")
        return _record(rows[0])

    async def update(
        self,
        access_token: str,
        chat_id: str,
        expected_revision: int,
        messages: list[SavedChatMessage],
    ) -> SavedChatRecord:
        body = self._body(messages)
        # schema_version is immutable and intentionally absent from the authenticated
        # role's UPDATE column grant. Sending it unchanged still requires UPDATE
        # privilege in Postgres, so PATCH only the mutable columns.
        del body["schema_version"]
        try:
            response = await self.client.patch(
                "/rest/v1/saved_chats",
                params={
                    "id": f"eq.{chat_id}",
                    "revision": f"eq.{expected_revision}",
                    "select": ROW_COLUMNS,
                },
                headers=self._headers(access_token, write=True),
                json=body,
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-chat service is unreachable. The new turn was not saved.") from None
        rows = await self._payload(response)
        if not rows:
            try:
                await self.get(access_token, chat_id)
            except PersistenceNotFound:
                raise
            raise PersistenceConflict("The saved chat changed elsewhere. Reload it before continuing.")
        if len(rows) != 1:
            raise PersistenceUnavailable("Saved-chat service returned an unexpected update result.")
        return _record(rows[0])

    async def delete(self, access_token: str, chat_id: str, expected_revision: int) -> SavedChatSummary:
        try:
            response = await self.client.delete(
                "/rest/v1/saved_chats",
                params={"id": f"eq.{chat_id}", "revision": f"eq.{expected_revision}", "select": SUMMARY_COLUMNS},
                headers=self._headers(access_token, write=True),
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-chat service is unreachable. The chat was not deleted.") from None
        rows = await self._payload(response)
        if not rows:
            try:
                await self.get(access_token, chat_id)
            except PersistenceNotFound:
                raise
            raise PersistenceConflict("The saved chat changed elsewhere. Reload it before deleting.")
        if len(rows) != 1:
            raise PersistenceUnavailable("Saved-chat service returned an unexpected delete result.")
        return _summary(rows[0])


def export_chat_pdf(chat: SavedChatRecord) -> bytes:
    """Create a readable PDF containing the complete saved conversation provenance."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    import reportlab

    font_name = "Helvetica"
    bold_name = "Helvetica-Bold"
    font_root = Path(reportlab.__file__).resolve().parent / "fonts"
    try:
        pdfmetrics.registerFont(TTFont("ResearchGuardSans", str(font_root / "Vera.ttf")))
        pdfmetrics.registerFont(TTFont("ResearchGuardSansBold", str(font_root / "VeraBd.ttf")))
        font_name, bold_name = "ResearchGuardSans", "ResearchGuardSansBold"
    except (OSError, ValueError):
        pass

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title=chat.summary.title,
        author="Research Guard AI",
        subject="Saved AI chat export",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ChatTitle", parent=styles["Title"], fontName=bold_name, fontSize=19,
        leading=23, textColor=colors.HexColor("#123B39"), alignment=TA_CENTER,
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "ChatMeta", parent=styles["BodyText"], fontName=font_name, fontSize=8.5,
        leading=11, textColor=colors.HexColor("#526966"), spaceAfter=4,
    )
    user_style = ParagraphStyle(
        "UserMessage", parent=styles["BodyText"], fontName=font_name, fontSize=10,
        leading=14, leftIndent=24, rightIndent=2, borderColor=colors.HexColor("#42D8A2"),
        borderWidth=0.8, borderPadding=8, backColor=colors.HexColor("#EAF8F2"), spaceAfter=10,
    )
    assistant_style = ParagraphStyle(
        "AssistantMessage", parent=user_style, leftIndent=2, rightIndent=24,
        borderColor=colors.HexColor("#B6C7C4"), backColor=colors.HexColor("#F4F7F6"),
    )

    def safe(value: str) -> str:
        return escape(value).replace("\n", "<br/>")

    story = [
        Paragraph("Research Guard AI — saved chat", title_style),
        Paragraph(f"<b>{safe(chat.summary.title)}</b>", meta_style),
        Paragraph(
            f"Created: {safe(chat.summary.created_at)} &nbsp;&nbsp; Updated: {safe(chat.summary.updated_at)}<br/>"
            f"Chat ID: {safe(chat.summary.chat_id)} &nbsp;&nbsp; Revision: {chat.summary.revision}",
            meta_style,
        ),
        Paragraph(
            "This conversation is unverified model output. It is not an evidence review and should not be treated as scientific evidence.",
            ParagraphStyle("Warning", parent=meta_style, fontName=bold_name, textColor=colors.HexColor("#8A5A18"), spaceAfter=12),
        ),
    ]
    for message in chat.messages:
        if message.role == "user":
            heading = f"<b>User</b> &nbsp; {safe(message.timestamp)}"
            style = user_style
        else:
            fallback = " · fallback used" if message.fallback_used else ""
            heading = (
                f"<b>Assistant</b> &nbsp; {safe(message.timestamp)}<br/>"
                f"Provider: {safe(message.provider or '')} · Model: {safe(message.model or '')}{fallback} · not evidence-checked"
            )
            style = assistant_style
        story.extend([Paragraph(heading, meta_style), Paragraph(safe(message.content), style), Spacer(1, 2 * mm)])

    def page_number(canvas, _document):
        canvas.saveState()
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor("#526966"))
        canvas.drawCentredString(A4[0] / 2, 9 * mm, f"Research Guard AI · page {canvas.getPageNumber()}")
        canvas.restoreState()

    document.build(story, onFirstPage=page_number, onLaterPages=page_number)
    return output.getvalue()
