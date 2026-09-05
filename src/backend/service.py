"""Application service coordinating attachments and the chat graph."""

from typing import Any

from langchain.messages import HumanMessage

from src.backend.attachments import prepare_attachments
from src.backend.schemas import ChatRequest


class AgentInvocationError(RuntimeError):
    """Raised when the model or graph cannot complete a chat request."""


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


class ChatService:
    def __init__(self, agent: Any) -> None:
        self._agent = agent

    async def chat(self, request: ChatRequest) -> str:
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
            return _answer_text(messages[-1])
        except AgentInvocationError:
            raise
        except Exception as exc:
            raise AgentInvocationError("The agent could not complete the request.") from exc
