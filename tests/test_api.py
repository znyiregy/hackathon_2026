from uuid import uuid4

import httpx
import pytest

from src.backend.api import app, get_chat_service
from src.backend.attachments import AttachmentError, AttachmentTooLargeError
from src.backend.service import AgentInvocationError


class FakeService:
    def __init__(self, result="fake answer", error=None):
        self.result = result
        self.error = error
        self.requests = []

    async def chat(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.result


def override_with(service):
    async def dependency():
        return service

    return dependency


@pytest.mark.anyio
async def test_health():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_chat_contract_and_attachment_only_message():
    fake = FakeService()
    app.dependency_overrides[get_chat_service] = override_with(fake)
    thread_id = str(uuid4())
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/chat",
                json={
                    "thread_id": thread_id,
                    "message": "",
                    "files": [{"name": "a.txt", "mime_type": "text/plain", "content_base64": "YQ=="}],
                },
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"thread_id": thread_id, "answer": "fake answer"}
    assert fake.requests[0].files[0].name == "a.txt"


@pytest.mark.anyio
async def test_rejects_empty_request():
    app.dependency_overrides[get_chat_service] = override_with(FakeService())
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"thread_id": str(uuid4()), "message": "", "files": []})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422


@pytest.mark.anyio
async def test_api_maps_known_errors():
    cases = [
        (AttachmentError("bad attachment"), 400, "bad attachment"),
        (AttachmentTooLargeError("too large"), 413, "too large"),
        (AgentInvocationError("private detail"), 502, "The language model could not complete the request."),
    ]
    for error, expected_status, expected_detail in cases:
        app.dependency_overrides[get_chat_service] = override_with(FakeService(error=error))
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/chat", json={"thread_id": str(uuid4()), "message": "hi"})
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_detail
