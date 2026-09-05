import pytest
import requests

from src.frontend.client import BackendError, ChatReply, UploadedFile, parse_uploads, send_chat


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.ok = 200 <= status_code < 400

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_parse_uploads_strips_data_url_prefix():
    files = parse_uploads(
        ["data:text/plain;base64,aGVsbG8=", "data:image/png;base64,AA=="],
        ["hello.txt", "pixel.png"],
    )
    assert files == [
        UploadedFile("hello.txt", "text/plain", "aGVsbG8="),
        UploadedFile("pixel.png", "image/png", "AA=="),
    ]


@pytest.mark.parametrize(
    ("contents", "filenames"),
    [(["data:text/plain;base64,YQ=="], ["a.txt", "b.txt"]), ("not-a-data-url", "a.txt")],
)
def test_parse_uploads_rejects_invalid_browser_data(contents, filenames):
    with pytest.raises(BackendError):
        parse_uploads(contents, filenames)


def test_send_chat_constructs_expected_request(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured.update(url=url, json=json, timeout=timeout)
        return FakeResponse(payload={"answer": "hello", "messages": [{"role": "assistant", "content": "hello"}]})

    monkeypatch.setattr(requests, "post", fake_post)
    answer = send_chat("http://backend/", "thread", "hi", [UploadedFile("a.txt", "text/plain", "YQ==")])
    assert answer == ChatReply(answer="hello", messages=[{"role": "assistant", "content": "hello"}])
    assert captured == {
        "url": "http://backend/chat",
        "json": {
            "thread_id": "thread",
            "message": "hi",
            "files": [{"name": "a.txt", "mime_type": "text/plain", "content_base64": "YQ=="}],
        },
        "timeout": 120,
    }


def test_send_chat_surfaces_backend_error(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: FakeResponse(400, {"detail": "bad file"}))
    with pytest.raises(BackendError, match="bad file"):
        send_chat("http://backend", "thread", "hi", [])
