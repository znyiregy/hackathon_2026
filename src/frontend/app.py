"""Single-page Dash application for the Architect Assistant."""

import os
from uuid import uuid4

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from dotenv import load_dotenv

from src.frontend.client import BackendError, parse_uploads, send_chat


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

app = Dash(
    __name__,
    title="Architect Assistant",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.layout = html.Main(
    className="app-shell",
    children=[
        dcc.Store(id="thread-store", data=str(uuid4())),
        dcc.Store(id="transcript-store", data=[]),
        dbc.Navbar(
            dbc.Container(
                [
                    dbc.NavbarBrand(
                        [
                            html.Img(
                                src=app.get_asset_url("logo.png"),
                                alt="Digital Deutschland",
                                className="brand-logo",
                            ),
                            html.Span("Architect Assistant", className="brand-name"),
                        ],
                        className="brand-lockup",
                    ),
                    dbc.Button("Neuer Chat", id="new-chat", className="new-chat-button"),
                ],
                fluid="xxl",
            ),
            className="app-navbar",
        ),
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H1("Projektgespräch", className="panel-title"),
                                            html.P("Unterlagen analysieren und Fragen klären", className="panel-subtitle"),
                                        ],
                                        className="chat-card-header",
                                    ),
                                    dbc.CardBody(
                                        dcc.Loading(html.Div(id="transcript", className="transcript"), type="dot"),
                                        className="chat-card-body",
                                    ),
                                ],
                                className="workspace-card chat-card",
                            ),
                            html.Div(id="error-message", className="error-message", role="alert"),
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        dcc.Upload(
                                            id="upload",
                                            children=html.Div(
                                                [
                                                    html.Strong("Dateien hinzufügen"),
                                                    html.Span(" oder hierher ziehen"),
                                                ]
                                            ),
                                            multiple=True,
                                            accept=".txt,.md,.csv,.json,.pdf,.png,.jpg,.jpeg",
                                            className="upload-box",
                                        ),
                                        html.Div(id="upload-list", className="upload-list"),
                                        dbc.Textarea(
                                            id="message-input",
                                            placeholder="Frage stellen oder Unterlagen zur Prüfung einreichen…",
                                            className="message-input",
                                        ),
                                        dbc.Button("Senden", id="send", className="send-button", size="lg"),
                                    ],
                                    className="composer-card-body",
                                ),
                                className="workspace-card composer-card",
                            ),
                        ],
                        lg=5,
                        className="chat-column",
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.H2("Dossierauswertung", className="panel-title"),
                                        html.P(
                                            "Aktuellste strukturierte Prüfung dieses Chats",
                                            className="panel-subtitle",
                                        ),
                                    ],
                                    className="result-card-header",
                                ),
                                dbc.CardBody(html.Div(id="result-panel"), className="result-card-body"),
                            ],
                            className="workspace-card result-card",
                        ),
                        lg=7,
                        className="result-column",
                    ),
                ],
                className="workspace-row g-4",
            ),
            fluid="xxl",
            className="workspace-container",
        ),
    ],
)


@app.callback(Output("upload-list", "children"), Input("upload", "filename"))
def show_uploads(filenames: list[str] | str | None):
    if not filenames:
        return ""
    names = filenames if isinstance(filenames, list) else [filenames]
    return [dbc.Badge(name, pill=True, className="file-chip") for name in names]


def _download_links(item: dict[str, object]) -> list[html.A]:
    attachments = item.get("attachments", [])
    if not isinstance(attachments, list):
        return []

    links = []
    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue
        name = attachment.get("name")
        mime_type = attachment.get("mime_type")
        content_base64 = attachment.get("content_base64")
        if all(isinstance(value, str) and value for value in (name, mime_type, content_base64)):
            links.append(
                html.A(
                    f"Download {name}",
                    href=f"data:{mime_type};base64,{content_base64}",
                    download=name,
                    className="download-link",
                )
            )
    return links


def _tool_title(tool_name: object) -> str:
    if tool_name == "submit_result":
        return "Strukturierte Auswertung übermittelt"
    return f"Tool: {tool_name or 'unbekannt'}"


def render_tool_message(item: dict[str, object], index: int):
    """Render tool output only when the visitor opens its accordion item."""

    downloads = _download_links(item)
    content = [html.Div(str(item.get("content", "")), className="tool-output-content")]
    if downloads:
        content.append(html.Div(downloads, className="message-downloads"))
    return dbc.Accordion(
        dbc.AccordionItem(
            content,
            title=_tool_title(item.get("tool_name")),
            item_id=f"tool-{index}",
        ),
        active_item=None,
        start_collapsed=True,
        className="tool-output",
    )


def _result_table(headers: list[str], rows: list[list[object]]):
    return dbc.Table(
        [
            html.Thead(html.Tr([html.Th(header) for header in headers])),
            html.Tbody([html.Tr([html.Td(value) for value in row]) for row in rows]),
        ],
        bordered=False,
        hover=True,
        responsive=True,
        className="result-table",
    )


def _section_heading(title: str, accent: str):
    return html.H3([html.Span(className=f"section-accent section-accent-{accent}"), title], className="result-section-title")


def render_dossier_result(result: dict[str, object]):
    """Render a structured dossier result with Bootstrap components."""

    file_renaming = result.get("file_renaming", [])
    checklist_status = result.get("checklist_status", [])
    conflicts = result.get("conflicts", [])
    next_steps = result.get("next_steps", [])

    renaming_rows = [
        [entry.get("old_filename", ""), entry.get("new_filename", "")]
        for entry in file_renaming
        if isinstance(entry, dict)
    ] if isinstance(file_renaming, list) else []

    status_colors = {"belegt": "success", "teilweise": "warning", "offen": "danger", "nicht pruefbar": "secondary"}
    checklist_rows = []
    if isinstance(checklist_status, list):
        for entry in checklist_status:
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status", ""))
            checklist_rows.append(
                [
                    entry.get("item", ""),
                    dbc.Badge(status, color=status_colors.get(status, "secondary"), pill=True, className="status-badge"),
                    entry.get("reason", ""),
                ]
            )

    conflict_cards = [
        dbc.Alert(
            [
                html.H4(entry.get("title", ""), className="conflict-title"),
                html.P(entry.get("detail", ""), className="mb-2"),
                html.P([html.Strong("Nächste Aktion: "), entry.get("requested_action", "")], className="mb-0"),
            ],
            color="danger",
            className="conflict-card",
        )
        for entry in conflicts
        if isinstance(entry, dict)
    ] if isinstance(conflicts, list) else []

    next_step_items = [
        dbc.ListGroupItem(
            [html.Strong(entry.get("evidence", "")), html.Span(f" — {entry.get('reason', '')}")],
            className="next-step-item",
        )
        for entry in next_steps
        if isinstance(entry, dict)
    ] if isinstance(next_steps, list) else []

    return html.Div(
        [
            _section_heading("Dateibenennung", "red"),
            _result_table(["Bisheriger Dateiname", "Vorgeschlagener Dateiname"], renaming_rows)
            if renaming_rows
            else dbc.Alert("Keine Dateiumbenennungen vorgeschlagen.", color="light", className="empty-section"),
            _section_heading("Checklistenstatus", "gold"),
            _result_table(["Prüfpunkt", "Status", "Begründung"], checklist_rows)
            if checklist_rows
            else dbc.Alert("Keine Checklistenpunkte bewertet.", color="light", className="empty-section"),
            _section_heading("Konflikte und Klärungen", "red"),
            html.Div(conflict_cards, className="conflict-list")
            if conflict_cards
            else dbc.Alert("Keine Konflikte festgestellt.", color="success", className="empty-section"),
            _section_heading("Nächste benötigte Nachweise", "gold"),
            dbc.ListGroup(next_step_items, className="next-steps-list")
            if next_step_items
            else dbc.Alert("Keine weiteren Nachweise benannt.", color="light", className="empty-section"),
        ],
        className="dossier-result",
    )


def latest_dossier_result(transcript: list[dict[str, object]] | None) -> dict[str, object] | None:
    """Return the newest submitted structured result in a chat transcript."""

    for item in reversed(transcript or []):
        if not isinstance(item, dict):
            continue
        result = item.get("result")
        if item.get("tool_name") == "submit_result" and isinstance(result, dict):
            return result
    return None


def render_result_panel(transcript: list[dict[str, object]] | None):
    result = latest_dossier_result(transcript)
    if result is not None:
        return render_dossier_result(result)
    return html.Div(
        [
            html.Div("▦", className="result-empty-icon", **{"aria-hidden": "true"}),
            html.H3("Noch keine Auswertung", className="result-empty-title"),
            html.P("Sobald die Unterlagen strukturiert geprüft wurden, erscheint die Dossierauswertung hier."),
        ],
        className="result-empty-state",
    )


@app.callback(Output("transcript", "children"), Input("transcript-store", "data"))
def render_transcript(transcript: list[dict[str, object]]):
    if not transcript:
        return html.Div("Starten Sie ein Gespräch oder fügen Sie Unterlagen hinzu.", className="empty-state")

    rendered = []
    for index, item in enumerate(transcript):
        role = str(item.get("role", "assistant"))
        if role == "tool":
            rendered.append(render_tool_message(item, index))
            continue

        files = item.get("files", [])
        file_names = ", ".join(str(file) for file in files) if isinstance(files, list) else ""
        label = "Sie" if role == "user" else "Assistant"
        rendered.append(
            html.Article(
                [
                    html.Div(label, className="message-role"),
                    html.Div(str(item.get("content", "")), className="message-content"),
                    html.Div(file_names, className="message-files") if file_names else None,
                ],
                className=f"message message-{role}",
            )
        )
    return rendered


@app.callback(Output("result-panel", "children"), Input("transcript-store", "data"))
def update_result_panel(transcript: list[dict[str, object]] | None):
    return render_result_panel(transcript)


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
        (Output("send", "children"), "Wird gesendet…", "Senden"),
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
            return no_update, no_update, "Bitte geben Sie eine Nachricht ein oder fügen Sie eine Datei hinzu.", no_update, no_update, no_update
        reply = send_chat(BACKEND_URL, thread_id, message, files)
    except BackendError as exc:
        return no_update, no_update, str(exc), no_update, no_update, no_update

    user_text = message.strip() or "Bitte prüfen Sie die angehängten Unterlagen."
    updated = list(transcript or [])
    updated.append({"role": "user", "content": user_text, "files": [file.name for file in files]})
    updated.extend(reply.messages)
    return updated, thread_id, "", "", None, None


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("FRONTEND_PORT", "8050")))
