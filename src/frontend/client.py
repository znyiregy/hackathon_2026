"""REST client and Dash-upload translation helpers."""

from dataclasses import dataclass
from typing import Any

import requests


class BackendError(RuntimeError):
    """A readable error returned by or raised while calling the backend."""


@dataclass(frozen=True)
class UploadedFile:
    name: str
    mime_type: str
    content_base64: str

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "mime_type": self.mime_type,
            "content_base64": self.content_base64,
        }


@dataclass(frozen=True)
class ChatReply:
    answer: str
    messages: list[dict[str, Any]]


def parse_uploads(contents: list[str] | str | None, filenames: list[str] | str | None) -> list[UploadedFile]:
    if contents is None or filenames is None:
        return []
    content_items = contents if isinstance(contents, list) else [contents]
    filename_items = filenames if isinstance(filenames, list) else [filenames]
    if len(content_items) != len(filename_items):
        raise BackendError("The browser returned inconsistent upload metadata.")

    files = []
    for data_url, filename in zip(content_items, filename_items, strict=True):
        try:
            header, encoded = data_url.split(",", maxsplit=1)
            mime_type = header.removeprefix("data:").split(";", maxsplit=1)[0]
        except (AttributeError, ValueError) as exc:
            raise BackendError(f"Could not read upload {filename!r}.") from exc
        if not header.startswith("data:") or ";base64" not in header or not mime_type or not encoded:
            raise BackendError(f"Could not read upload {filename!r}.")
        files.append(UploadedFile(name=filename, mime_type=mime_type, content_base64=encoded))
    return files


def send_chat(
    backend_url: str,
    thread_id: str,
    message: str,
    files: list[UploadedFile],
    timeout: float = 120,
) -> ChatReply:
    payload: dict[str, Any] = {
        "thread_id": thread_id,
        "message": message,
        "files": [file.as_dict() for file in files],
    }
    try:
        response = requests.post(f"{backend_url.rstrip('/')}/chat", json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise BackendError(f"Could not reach the backend: {exc}") from exc

    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise BackendError(f"Backend returned {response.status_code}: {detail}")
    try:
        payload = response.json()
        answer = payload["answer"]
        messages = payload["messages"]
    except (KeyError, TypeError, ValueError) as exc:
        raise BackendError("The backend returned an invalid response.") from exc
    if not isinstance(answer, str) or not isinstance(messages, list):
        raise BackendError("The backend returned an invalid response.")
    if not all(isinstance(message, dict) for message in messages):
        raise BackendError("The backend returned an invalid response.")
    return ChatReply(answer=answer, messages=messages)
