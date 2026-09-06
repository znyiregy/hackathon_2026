def test_render_transcript_renders_tool_message_and_download_link():
    from src.frontend.app import render_transcript

    message = render_transcript(
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

    label, content, _files, downloads = message.children
    link = downloads.children[0]
    assert label.children == "Tool: build_report"
    assert content.children == "Generated report."
    assert link.children == "Download report.txt"
    assert link.href == "data:text/plain;base64,SGVsbG8="
    assert link.download == "report.txt"


def test_render_transcript_renders_structured_dossier_result():
    from src.frontend.app import render_transcript

    message = render_transcript(
        [
            {
                "role": "tool",
                "tool_name": "submit_result",
                "content": "Structured dossier result submitted.",
                "result": {
                    "file_renaming": [{"old_filename": "old.pdf", "new_filename": "new.pdf"}],
                    "checklist_status": [{"item": "Antragsformular", "status": "offen", "reason": "Fehlt."}],
                    "next_steps": [{"evidence": "Antragsformular", "reason": "Erforderlich."}],
                    "conflicts": [
                        {"title": "Namenskonflikt", "detail": "Abweichende Namen.", "requested_action": "Auszug anfordern."}
                    ],
                },
            }
        ]
    )[0]

    result = message.children
    assert message.className == "message message-tool dossier-result-message"
    assert result.className == "dossier-result"
    assert result.children[0].children == "Strukturierte Dossierprüfung"
    assert result.children[2].children[1].children[0].children[0].children == "old.pdf"
    assert result.children[4].children[1].children[0].children[1].children.className == "status-chip status-offen"
    assert result.children[6].children[0].children[0].children == "Namenskonflikt"
    assert result.children[8].children[0].children[0].children == "Antragsformular"
