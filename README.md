# Hackathon chat monorepo

A small local-development application with:

- a FastAPI backend exposing a LangGraph-backed OpenAI agent;
- one safe arithmetic tool;
- text, image, and PDF attachments transported as base64 JSON and retained in
  per-chat agent state for download;
- a Dash chat frontend using the backend over REST.

This is intentionally a prototype. Conversation state is held in memory and is
lost whenever the backend restarts.

## Setup

```bash
conda env create -f environment.yml
conda activate hackathon
cp .env.example .env
```

Set `OPENAI_API_KEY`, `OPENAI_MODEL`, and `REASONING_EFFORT` in `.env`. The
model must support function calling. Use a reasoning effort the selected model
supports, such as `medium`. `BACKEND_URL` and `FRONTEND_PORT` are optional.

## Run

Start the backend from the repository root:

```bash
conda activate hackathon
uvicorn src.backend.api:app --reload --port 8000
```

In a second terminal, start the frontend:

```bash
conda activate hackathon
python -m src.frontend.app
```

Open <http://127.0.0.1:8050>. FastAPI's interactive API documentation is at
<http://127.0.0.1:8000/docs>.

## REST API

`GET /health` returns `{"status": "ok"}`.

`POST /chat` accepts:

```json
{
  "thread_id": "2f8e5cc6-4c82-4dd9-a62f-c429208159b3",
  "message": "Summarize these files",
  "files": [
    {
      "name": "notes.txt",
      "mime_type": "text/plain",
      "content_base64": "SGVsbG8="
    }
  ]
}
```

Supported uploads are TXT, MD, CSV, JSON, PDF, PNG, and JPEG. A request may
contain at most 10 MiB of decoded file data. PDFs are limited to 10 pages. The
original file data is stored for the chat thread, but never added to LLM
context; the agent sees only uploaded filenames and can return a requested file
through its `send_file` tool.

Responses include the final `answer` and ordered `messages`. Tool messages are
forwarded to the frontend, so their status text is shown in the transcript. A
tool can also return a downloadable file in its LangChain `ToolMessage`
artifact:

```python
(
    "Report created.",
    {
        "attachments": [
            {
                "name": "report.txt",
                "mime_type": "text/plain",
                "content_base64": "SGVsbG8=",
            }
        ]
    },
)
```

Use this tuple with a LangChain tool configured with
`response_format="content_and_artifact"`. The frontend renders each attachment
as a download link.

## Tests

The automated tests do not call OpenAI and do not need an API key:

```bash
conda activate hackathon
pytest -q
```

For a manual smoke test, start both services and verify normal chat, a request
such as `Calculate (17 * 4) + sqrt(81)`, and TXT, image, and PDF uploads. Click
**New chat** and confirm that prior context is no longer used.
