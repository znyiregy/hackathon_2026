# Hackathon chat monorepo

A small local-development application with:

- a FastAPI backend exposing a LangGraph-backed OpenAI agent;
- one safe arithmetic tool;
- text, image, and PDF attachments transported as base64 JSON;
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
model must support image input and function calling. Use a reasoning effort the
selected model supports, such as `medium`. `BACKEND_URL` and `FRONTEND_PORT`
are optional.

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
contain at most 10 MiB of decoded file data. PDFs are limited to 10 pages.
Images and rendered PDF pages are converted to JPEG quality 92 with a maximum
long side of 1400 pixels. Combined text attachment content is truncated at
200,000 characters with a visible notice.

## Tests

The automated tests do not call OpenAI and do not need an API key:

```bash
conda activate hackathon
pytest -q
```

For a manual smoke test, start both services and verify normal chat, a request
such as `Calculate (17 * 4) + sqrt(81)`, and TXT, image, and PDF uploads. Click
**New chat** and confirm that prior context is no longer used.
