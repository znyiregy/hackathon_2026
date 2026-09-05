from uuid import uuid4

import pytest
from langchain.messages import AIMessage

from src.backend.schemas import ChatRequest
from src.backend.service import ChatService


class MemoryFakeAgent:
    def __init__(self):
        self.messages_by_thread = {}

    async def ainvoke(self, payload, config):
        thread_id = config["configurable"]["thread_id"]
        count = self.messages_by_thread.get(thread_id, 0) + 1
        self.messages_by_thread[thread_id] = count
        return {"messages": [*payload["messages"], AIMessage(content=f"message {count}")]}


@pytest.mark.anyio
async def test_service_passes_thread_id_and_threads_are_isolated():
    service = ChatService(MemoryFakeAgent())
    first_thread = uuid4()
    second_thread = uuid4()

    assert await service.chat(ChatRequest(thread_id=first_thread, message="one")) == "message 1"
    assert await service.chat(ChatRequest(thread_id=first_thread, message="two")) == "message 2"
    assert await service.chat(ChatRequest(thread_id=second_thread, message="one")) == "message 1"


@pytest.mark.anyio
async def test_attachment_only_message_gets_a_default_instruction():
    agent = MemoryFakeAgent()
    service = ChatService(agent)
    request = ChatRequest(
        thread_id=uuid4(),
        files=[{"name": "a.txt", "mime_type": "text/plain", "content_base64": "aGVsbG8="}],
    )
    assert await service.chat(request) == "message 1"
