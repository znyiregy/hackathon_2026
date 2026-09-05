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
