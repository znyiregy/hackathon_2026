from pathlib import Path

import dash_bootstrap_components as dbc
from dash import html


def walk_components(component):
    """Yield a Dash component and all of its descendant components."""

    yield component
    children = getattr(component, "children", None)
    child_items = children if isinstance(children, (list, tuple)) else [children]
    for child in child_items:
        if child is not None and hasattr(child, "children"):
            yield from walk_components(child)


def structured_result(name: str):
    return {
        "file_renaming": [{"old_filename": f"{name}-old.pdf", "new_filename": f"{name}-new.pdf"}],
        "checklist_status": [{"item": "Antragsformular", "status": "offen", "reason": "Fehlt."}],
        "next_steps": [{"evidence": "Antragsformular", "reason": "Erforderlich."}],
        "conflicts": [
            {"title": "Namenskonflikt", "detail": "Abweichende Namen.", "requested_action": "Auszug anfordern."}
        ],
    }


def test_header_uses_served_logo_and_product_name():
    from src.frontend.app import app

    images = [component for component in walk_components(app.layout) if isinstance(component, html.Img)]
    names = [component.children for component in walk_components(app.layout) if isinstance(component, html.Span)]

    assert app.title == "Architect Assistant"
    assert Path("src/frontend/assets/logo.png").is_file()
    assert images[0].src == app.get_asset_url("logo.png")
    assert "Architect Assistant" in names


def test_render_transcript_renders_tool_message_as_closed_accordion_with_download_link():
    from src.frontend.app import render_transcript

    accordion = render_transcript(
        [
            {
                "role": "tool",
                "tool_name": "build_report",
                "content": "Generated report.",
                "attachments": [
                    {"name": "report.txt", "mime_type": "text/plain", "content_base64": "SGVsbG8="}
                ],
            }
        ]
    )[0]

    item = accordion.children
    content, downloads = item.children
    link = downloads.children[0]
    assert isinstance(accordion, dbc.Accordion)
    assert accordion.active_item is None
    assert accordion.start_collapsed is True
    assert item.title == "Tool: build_report"
    assert content.children == "Generated report."
    assert link.children == "Download report.txt"
    assert link.href == "data:text/plain;base64,SGVsbG8="
    assert link.download == "report.txt"


def test_structured_result_is_an_accordion_in_chat_and_a_colored_result_panel():
    from src.frontend.app import render_result_panel, render_transcript

    transcript = [
        {
            "role": "tool",
            "tool_name": "submit_result",
            "content": "Structured dossier result submitted.",
            "result": structured_result("first"),
        }
    ]

    accordion = render_transcript(transcript)[0]
    panel = render_result_panel(transcript)
    components = list(walk_components(panel))

    assert accordion.children.title == "Strukturierte Auswertung übermittelt"
    assert accordion.children.children[0].children == "Structured dossier result submitted."
    assert panel.className == "dossier-result"
    assert any(isinstance(component, dbc.Table) for component in components)
    assert any(isinstance(component, dbc.Badge) and component.color == "danger" for component in components)
    assert any(isinstance(component, dbc.Alert) and component.color == "danger" for component in components)
    assert any(isinstance(component, dbc.ListGroup) for component in components)


def test_result_panel_uses_newest_structured_result_and_has_empty_state():
    from src.frontend.app import latest_dossier_result, render_result_panel

    first = structured_result("first")
    second = structured_result("second")
    transcript = [
        {"role": "tool", "tool_name": "submit_result", "result": first},
        {"role": "assistant", "content": "Zwischenmeldung."},
        {"role": "tool", "tool_name": "submit_result", "result": second},
    ]

    panel = render_result_panel(transcript)
    table_cells = [component.children for component in walk_components(panel) if isinstance(component, html.Td)]
    empty_panel = render_result_panel([])

    assert latest_dossier_result(transcript) == second
    assert "second-old.pdf" in table_cells
    assert "first-old.pdf" not in table_cells
    assert empty_panel.className == "result-empty-state"
    assert empty_panel.children[1].children == "Noch keine Auswertung"
