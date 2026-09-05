from uuid import uuid4

import pytest
from langchain.messages import AIMessage, ToolMessage

from src.backend.schemas import ChatRequest
from src.backend.service import ChatService


class MemoryFakeAgent:
    def __init__(self):
        self.messages_by_thread = {}
        self.last_payload = None

    async def ainvoke(self, payload, config):
        self.last_payload = payload
        thread_id = config["configurable"]["thread_id"]
        count = self.messages_by_thread.get(thread_id, 0) + 1
        self.messages_by_thread[thread_id] = count
        return {"messages": [*payload["messages"], AIMessage(content=f"message {count}")]}


@pytest.mark.anyio
async def test_service_passes_thread_id_and_threads_are_isolated():
    service = ChatService(MemoryFakeAgent())
    first_thread = uuid4()
    second_thread = uuid4()

    assert (await service.chat(ChatRequest(thread_id=first_thread, message="one"))).answer == "message 1"
    assert (await service.chat(ChatRequest(thread_id=first_thread, message="two"))).answer == "message 2"
    assert (await service.chat(ChatRequest(thread_id=second_thread, message="one"))).answer == "message 1"


@pytest.mark.anyio
async def test_attachment_only_message_gets_a_default_instruction():
    agent = MemoryFakeAgent()
    service = ChatService(agent)
    request = ChatRequest(
        thread_id=uuid4(),
        files=[{"name": "a.txt", "mime_type": "text/plain", "content_base64": "aGVsbG8="}],
    )
    assert (await service.chat(request)).answer == "message 1"


@pytest.mark.anyio
async def test_uploaded_files_are_stored_but_not_sent_to_the_model():
    agent = MemoryFakeAgent()
    request = ChatRequest(
        thread_id=uuid4(),
        message="Send the report back.",
        files=[{"name": "report.txt", "mime_type": "text/plain", "content_base64": "cHJpdmF0ZSBjb250ZW50"}],
    )

    await ChatService(agent).chat(request)
    payload = agent.last_payload
    message = payload["messages"][0]

    assert isinstance(message.content, str)
    assert message.content == "Send the report back.\n\nFiles stored for this conversation:\n- report.txt"
    assert "cHJpdmF0ZSBjb250ZW50" not in message.content
    assert "private content" not in message.content
    assert payload["attachments"] == {
        "report.txt": {"name": "report.txt", "mime_type": "text/plain", "content_base64": "cHJpdmF0ZSBjb250ZW50"}
    }


class ToolMessageAgent:
    async def ainvoke(self, payload, config):
        return {
            "messages": [
                *payload["messages"],
                ToolMessage(
                    content="The file is ready.",
                    name="build_report",
                    tool_call_id="call-1",
                    artifact={
                        "attachments": [
                            {
                                "name": "report.txt",
                                "mime_type": "text/plain",
                                "content_base64": "SGVsbG8=",
                            }
                        ]
                    },
                ),
                AIMessage(content="I created the report."),
            ]
        }


@pytest.mark.anyio
async def test_service_forwards_tool_messages_and_downloadable_attachments():
    result = await ChatService(ToolMessageAgent()).chat(ChatRequest(thread_id=uuid4(), message="make a report"))

    assert result.answer == "I created the report."
    assert [message.model_dump() for message in result.messages] == [
        {
            "role": "tool",
            "content": "The file is ready.",
            "tool_name": "build_report",
            "attachments": [
                {"name": "report.txt", "mime_type": "text/plain", "content_base64": "SGVsbG8="}
            ],
        },
        {"role": "assistant", "content": "I created the report.", "tool_name": None, "attachments": []},
    ]
