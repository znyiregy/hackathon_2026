"""Application service coordinating attachments and the chat graph."""

from typing import Any

from langchain.messages import HumanMessage, ToolMessage

from src.backend.attachments import prepare_attachments
from src.backend.schemas import ChatMessage, ChatRequest, DownloadAttachment


class AgentInvocationError(RuntimeError):
    """Raised when the model or graph cannot complete a chat request."""


class ChatResult:
    """The final answer plus messages generated while producing it."""

    def __init__(self, answer: str, messages: list[ChatMessage]) -> None:
        self.answer = answer
        self.messages = messages


def _answer_text(message: Any) -> str:
    text = getattr(message, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    content = getattr(message, "content", message)
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") in {"text", "output_text"}:
                value = block.get("text")
                if isinstance(value, str):
                    parts.append(value)
        if parts:
            return "\n".join(parts).strip()
    raise AgentInvocationError("The agent returned no text response.")


def _download_attachments(message: ToolMessage) -> list[DownloadAttachment]:
    """Read browser-downloadable files from a tool message artifact.

    Tools may return an artifact shaped as
    ``{"attachments": [{"name", "mime_type", "content_base64"}]}``.
    Artifacts stay out of the model context but are forwarded to the browser.
    """

    artifact = getattr(message, "artifact", None)
    if not isinstance(artifact, dict):
        return []
    attachments = artifact.get("attachments", [])
    if not isinstance(attachments, list):
        return []
    try:
        return [DownloadAttachment.model_validate(attachment) for attachment in attachments]
    except ValueError as exc:
        raise AgentInvocationError("A tool returned an invalid downloadable attachment.") from exc


def _tool_messages(messages: list[Any]) -> list[ChatMessage]:
    rendered = []
    for message in messages:
        if isinstance(message, ToolMessage):
            rendered.append(
                ChatMessage(
                    role="tool",
                    tool_name=getattr(message, "name", None),
                    content=_answer_text(message),
                    attachments=_download_attachments(message),
                )
            )
    return rendered


def _current_turn(messages: list[Any]) -> list[Any]:
    """Keep tool output from this request, not prior checkpointed turns."""

    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            return messages[index + 1 :]
    return messages


class ChatService:
    def __init__(self, agent: Any) -> None:
        self._agent = agent

    async def chat(self, request: ChatRequest) -> ChatResult:
        prepared = prepare_attachments(request.files)
        prompt = request.message.strip() or "Please analyze the attached file or files."
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        content.extend(prepared.content_blocks)

        try:
            result = await self._agent.ainvoke(
                {"messages": [HumanMessage(content=content)]},
                config={"configurable": {"thread_id": str(request.thread_id)}},
            )
            messages = result.get("messages", [])
            if not messages:
                raise AgentInvocationError("The agent returned no messages.")
            current_turn = _current_turn(messages)
            answer = _answer_text(messages[-1])
            return ChatResult(
                answer=answer,
                messages=[*_tool_messages(current_turn), ChatMessage(role="assistant", content=answer)],
            )
        except AgentInvocationError:
            raise
        except Exception as exc:
            raise AgentInvocationError("The agent could not complete the request.") from exc
