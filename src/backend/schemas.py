import base64
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class Attachment(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=100)
    content_base64: str = Field(min_length=1)


class DownloadAttachment(BaseModel):
    """A file emitted by an agent tool for the browser to download."""

    name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=100)
    content_base64: str = Field(min_length=1)

    @field_validator("content_base64")
    @classmethod
    def require_valid_base64(cls, value: str) -> str:
        try:
            base64.b64decode(value, validate=True)
        except ValueError as exc:
            raise ValueError("content_base64 is not valid base64.") from exc
        return value


class ChatMessage(BaseModel):
    """A message the frontend can render from an agent invocation."""

    role: Literal["assistant", "tool"]
    content: str = ""
    tool_name: str | None = None
    attachments: list[DownloadAttachment] = Field(default_factory=list)


class ChatRequest(BaseModel):
    thread_id: UUID
    message: str = ""
    files: list[Attachment] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_message_or_file(self) -> "ChatRequest":
        if not self.message.strip() and not self.files:
            raise ValueError("Provide a message or at least one file.")
        return self


class ChatResponse(BaseModel):
    thread_id: UUID
    answer: str
    messages: list[ChatMessage]


class HealthResponse(BaseModel):
    status: str
