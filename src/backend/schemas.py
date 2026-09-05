from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class Attachment(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=100)
    content_base64: str = Field(min_length=1)


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


class HealthResponse(BaseModel):
    status: str
