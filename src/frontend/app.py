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


def _result_table(headers: list[str], rows: list[list[object]], class_name: str) -> html.Table:
    return html.Table(
        [
            html.Thead(html.Tr([html.Th(header) for header in headers])),
            html.Tbody([html.Tr([html.Td(value) for value in row]) for row in rows]),
        ],
        className=class_name,
    )


def render_dossier_result(result: dict[str, object]):
    """Render the validated structured dossier result returned by the backend."""

    file_renaming = result.get("file_renaming", [])
    checklist_status = result.get("checklist_status", [])
    conflicts = result.get("conflicts", [])
    next_steps = result.get("next_steps", [])

    renaming_rows = [
        [entry.get("old_filename", ""), entry.get("new_filename", "")]
        for entry in file_renaming
        if isinstance(entry, dict)
    ] if isinstance(file_renaming, list) else []
    checklist_rows = []
    if isinstance(checklist_status, list):
        for entry in checklist_status:
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status", ""))
            checklist_rows.append(
                [
                    entry.get("item", ""),
                    html.Span(status, className=f"status-chip status-{status.replace(' ', '-')}"),
                    entry.get("reason", ""),
                ]
            )
    conflict_cards = [
        html.Article(
            [
                html.H4(entry.get("title", "")),
                html.P(entry.get("detail", "")),
                html.P([html.Strong("Nächste Aktion: "), entry.get("requested_action", "")]),
            ],
            className="conflict-card",
        )
        for entry in conflicts
        if isinstance(entry, dict)
    ] if isinstance(conflicts, list) else []
    next_step_items = [
        html.Li([html.Strong(entry.get("evidence", "")), html.Span(f": {entry.get('reason', '')}")])
        for entry in next_steps
        if isinstance(entry, dict)
    ] if isinstance(next_steps, list) else []

    return html.Section(
        [
            html.H3("Strukturierte Dossierprüfung"),
            html.H4("Dateibenennung"),
            _result_table(["Bisheriger Dateiname", "Vorgeschlagener Dateiname"], renaming_rows, "result-table"),
            html.H4("Checklistenstatus"),
            _result_table(["Prüfpunkt", "Status", "Begründung"], checklist_rows, "result-table"),
            html.H4("Konflikte und Klärungen"),
            html.Div(conflict_cards or [html.P("Keine Konflikte festgestellt.")], className="conflict-list"),
            html.H4("Nächste benötigte Nachweise"),
            html.Ul(next_step_items or [html.Li("Keine weiteren Nachweise benannt.")], className="next-steps-list"),
        ],
        className="dossier-result",
    )


@app.callback(Output("transcript", "children"), Input("transcript-store", "data"))
def render_transcript(transcript: list[dict[str, object]]):
    if not transcript:
        return html.Div("Start a conversation or attach a file.", className="empty-state")
    rendered = []
    for item in transcript:
        role = str(item.get("role", "assistant"))
        result = item.get("result")
        if item.get("tool_name") == "submit_result" and isinstance(result, dict):
            rendered.append(
                html.Div(
                    className="message message-tool dossier-result-message",
                    children=render_dossier_result(result),
                )
            )
            continue
        files = item.get("files", [])
        attachments = item.get("attachments", [])
        downloads = []
        if isinstance(attachments, list):
            for attachment in attachments:
                if not isinstance(attachment, dict):
                    continue
                name = attachment.get("name")
                mime_type = attachment.get("mime_type")
                content_base64 = attachment.get("content_base64")
                if all(isinstance(value, str) and value for value in (name, mime_type, content_base64)):
                    downloads.append(
                        html.A(
                            f"Download {name}",
                            href=f"data:{mime_type};base64,{content_base64}",
                            download=name,
                            className="download-link",
                        )
                    )
        label = "You" if role == "user" else (f"Tool: {item['tool_name']}" if item.get("tool_name") else "Assistant")
        rendered.append(
            html.Div(
                className=f"message message-{role}",
                children=[
                    html.Div(label, className="message-role"),
                    html.Div(str(item.get("content", "")), className="message-content"),
                    html.Div(", ".join(files), className="message-files") if files else None,
                    html.Div(downloads, className="message-downloads") if downloads else None,
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
        reply = send_chat(BACKEND_URL, thread_id, message, files)
    except BackendError as exc:
        return no_update, no_update, str(exc), no_update, no_update, no_update

    user_text = message.strip() or "Please analyze the attached file or files."
    updated = list(transcript or [])
    updated.append({"role": "user", "content": user_text, "files": [file.name for file in files]})
    updated.extend(reply.messages)
    return updated, thread_id, "", "", None, None


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("FRONTEND_PORT", "8050")))
