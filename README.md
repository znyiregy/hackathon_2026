# Hackathon chat monorepo

A small local-development application with:

- a FastAPI backend exposing a LangGraph-backed OpenAI agent;
- one safe arithmetic tool;
- text, image, and PDF attachments transported as base64 JSON and retained in
  per-chat agent state for download;
- a Dash chat frontend using the backend over REST.

This is intentionally a prototype. Conversation state is held in memory and is
lost whenever the backend restarts.

## Architecture

```text
Dash browser UI
  └─ POST /chat (text + base64 uploads)
       └─ FastAPI API
            └─ ChatService
                 └─ LangGraph agent + in-memory checkpoint
                      ├─ OpenAI chat model
                      ├─ calculation tool
                      ├─ send_file tool
                      └─ analyze_file subagent tool
                      └─ submit_result dossier tool
```

The frontend encodes browser uploads as base64 JSON. The backend validates each
file and stores its original name, MIME type, and base64 content in LangGraph
state for that chat thread. Only filenames are added to the parent agent's
prompt; file content remains outside its normal conversation context.

When the agent uses a tool, its tool message is included in the API response.
The Dash frontend renders tool status messages and turns file artifacts into
download links.

## What the agent can do

- Answer normal chat questions while retaining conversation context per thread.
- Calculate arithmetic expressions with the safe `calculation` tool.
- List and return a previously uploaded file through `send_file`; the user sees
  it as a download link.
- Analyze a selected stored TXT, MD, CSV, JSON, PNG, JPEG, or PDF file through
  `analyze_file`. That subagent receives the user instruction and only the
  selected file's material; text is capped at 200,000 characters, while images
  and PDF pages are converted to JPEG with a maximum side of 1400 pixels.

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
contain at most 10 MiB of decoded file data. PDFs are limited to 10 pages. The
original file data is stored for the chat thread, but never added to the parent
agent's LLM context. The agent sees only uploaded filenames and can return a
requested file through `send_file`, or analyze a selected file through its
`analyze_file` subagent tool.

Responses include the final `answer` and ordered `messages`. Tool messages are
forwarded to the frontend, so their status text is shown in the transcript. A
`submit_result` tool message additionally has a structured `result` object for
the Bonn-Beuel dossier view. It contains `file_renaming`, `checklist_status`,
`next_steps`, and `conflicts`; ordinary messages return `result: null`. A tool can
also return a downloadable file in its LangChain `ToolMessage` artifact:

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
