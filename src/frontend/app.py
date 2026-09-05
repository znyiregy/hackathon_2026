"""Single-page Dash chat application."""

import os
from uuid import uuid4

from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from dotenv import load_dotenv

from src.frontend.client import BackendError, parse_uploads, send_chat


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

app = Dash(__name__, title="Hackathon Assistant")
app.layout = html.Main(
    className="page-shell",
    children=[
        dcc.Store(id="thread-store", data=str(uuid4())),
        dcc.Store(id="transcript-store", data=[]),
        html.Header(
            className="app-header",
            children=[
                html.Div([html.H1("Hackathon Assistant"), html.P("LangGraph · FastAPI · Dash")]),
                html.Button("New chat", id="new-chat", className="secondary-button"),
            ],
        ),
        dcc.Loading(html.Div(id="transcript", className="transcript"), type="dot"),
        html.Div(id="error-message", className="error-message"),
        html.Section(
            className="composer",
            children=[
                dcc.Upload(
                    id="upload",
                    children=html.Div(["Drop files here or ", html.Span("choose files")]),
                    multiple=True,
                    accept=".txt,.md,.csv,.json,.pdf,.png,.jpg,.jpeg",
                    className="upload-box",
                ),
                html.Div(id="upload-list", className="upload-list"),
                dcc.Textarea(
                    id="message-input",
                    placeholder="Ask a question…",
                    className="message-input",
                ),
                html.Button("Send", id="send", className="primary-button"),
            ],
        ),
    ],
)


@app.callback(Output("upload-list", "children"), Input("upload", "filename"))
def show_uploads(filenames: list[str] | str | None):
    if not filenames:
        return ""
    names = filenames if isinstance(filenames, list) else [filenames]
    return [html.Span(name, className="file-chip") for name in names]


@app.callback(Output("transcript", "children"), Input("transcript-store", "data"))
def render_transcript(transcript: list[dict[str, object]]):
    if not transcript:
        return html.Div("Start a conversation or attach a file.", className="empty-state")
    rendered = []
    for item in transcript:
        role = str(item.get("role", "assistant"))
        files = item.get("files", [])
        rendered.append(
            html.Div(
                className=f"message message-{role}",
                children=[
                    html.Div("You" if role == "user" else "Assistant", className="message-role"),
                    html.Div(str(item.get("content", "")), className="message-content"),
                    html.Div(", ".join(files), className="message-files") if files else None,
                ],
            )
        )
    return rendered


@app.callback(
    Output("transcript-store", "data"),
    Output("thread-store", "data"),
    Output("error-message", "children"),
    Output("message-input", "value"),
    Output("upload", "contents"),
    Output("upload", "filename"),
    Input("send", "n_clicks"),
    Input("new-chat", "n_clicks"),
    State("message-input", "value"),
    State("upload", "contents"),
    State("upload", "filename"),
    State("transcript-store", "data"),
    State("thread-store", "data"),
    prevent_initial_call=True,
    running=[
        (Output("send", "disabled"), True, False),
        (Output("send", "children"), "Sending…", "Send"),
    ],
)
def handle_action(
    _send_clicks: int | None,
    _new_chat_clicks: int | None,
    message: str | None,
    contents: list[str] | str | None,
    filenames: list[str] | str | None,
    transcript: list[dict[str, object]],
    thread_id: str,
):
    if ctx.triggered_id == "new-chat":
        return [], str(uuid4()), "", "", None, None

    message = message or ""
    try:
        files = parse_uploads(contents, filenames)
        if not message.strip() and not files:
            return no_update, no_update, "Enter a message or attach at least one file.", no_update, no_update, no_update
        answer = send_chat(BACKEND_URL, thread_id, message, files)
    except BackendError as exc:
        return no_update, no_update, str(exc), no_update, no_update, no_update

    user_text = message.strip() or "Please analyze the attached file or files."
    updated = list(transcript or [])
    updated.append({"role": "user", "content": user_text, "files": [file.name for file in files]})
    updated.append({"role": "assistant", "content": answer})
    return updated, thread_id, "", "", None, None


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("FRONTEND_PORT", "8050")))
