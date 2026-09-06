import src.backend.agent as agent_module
import base64
from io import BytesIO

import pymupdf
import pytest
from langchain.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from PIL import Image

from src.backend.agent import (
    ConfigurationError,
    _merge_attachments,
    build_agent,
    build_file_analysis_tool,
    send_file,
    submit_result,
)
from src.backend.config import Settings
from src.backend.schemas import DossierResult


def invoke_send_file(state):
    graph = StateGraph(dict)
    graph.add_node("tools", ToolNode([send_file, submit_result]))
    graph.add_edge(START, "tools")
    graph.add_edge("tools", END)
    return graph.compile().invoke(state)


async def invoke_file_analysis(tool, state):
    graph = StateGraph(dict)
    graph.add_node("tools", ToolNode([tool]))
    graph.add_edge(START, "tools")
    graph.add_edge("tools", END)
    return await graph.compile().ainvoke(state)


class FileAnalysisModel:
    def __init__(self):
        self.messages = None

    async def ainvoke(self, messages):
        self.messages = messages
        return AIMessage(content="File analysis response")


def test_build_agent_passes_reasoning_effort_to_responses_api(monkeypatch):
    captured = {}

    def fake_model(**kwargs):
        captured["model"] = kwargs
        return "model"

    def fake_create_agent(**kwargs):
        captured["agent"] = kwargs
        return "agent"

    monkeypatch.setattr(agent_module, "ChatOpenAI", fake_model)
    monkeypatch.setattr(agent_module, "create_agent", fake_create_agent)

    settings = Settings(
        openai_api_key="test-key",
        openai_model="test-model",
        reasoning_effort="medium",
    )
    assert build_agent(settings) == "agent"
    assert captured["model"] == {
        "api_key": "test-key",
        "model": "test-model",
        "use_responses_api": True,
        "reasoning": {"effort": "medium"},
    }
    assert [tool.name for tool in captured["agent"]["tools"]] == [
        "calculation",
        "send_file",
        "analyze_file",
        "submit_result",
    ]
    assert captured["agent"]["state_schema"] is agent_module.ChatAgentState
    assert "analyze_file" in captured["agent"]["system_prompt"]
    assert "submit_result" in captured["agent"]["system_prompt"]


def test_bonn_beuel_demo_playbook_requires_two_passes_and_safe_status_output():
    playbook = agent_module.BONN_BEUEL_DEMO_PLAYBOOK

    assert "exactly once for every current filename" in playbook
    assert "Second pass" in playbook
    assert "YYYY-MM-DD_Dokumenttyp_Detail_V01.ext" in playbook
    assert "YYYY-MM-DD-E" in playbook
    assert "original filename as a document date" in playbook
    assert all(status in playbook for status in ("belegt", "teilweise", "offen", "nicht pruefbar"))
    assert "Jennifer Hoenig-Singh" in playbook
    assert "Amardeep Singh" in playbook
    assert "Amardeep Zoltan Nyiregyhazi" in playbook
    assert "land-registry extract" in playbook


def test_build_agent_requires_reasoning_effort():
    settings = Settings(_env_file=None, openai_api_key="test-key", openai_model="test-model")
    try:
        build_agent(settings)
    except ConfigurationError as exc:
        assert str(exc) == "REASONING_EFFORT is not configured."
    else:
        raise AssertionError("build_agent should reject missing reasoning effort")


def test_attachment_state_merges_and_newest_filename_wins():
    original = {"report.txt": {"name": "report.txt", "mime_type": "text/plain", "content_base64": "b2xk"}}
    incoming = {
        "report.txt": {"name": "report.txt", "mime_type": "text/plain", "content_base64": "bmV3"},
        "notes.txt": {"name": "notes.txt", "mime_type": "text/plain", "content_base64": "bm90ZXM="},
    }

    assert _merge_attachments(original, incoming) == {
        "report.txt": {"name": "report.txt", "mime_type": "text/plain", "content_base64": "bmV3"},
        "notes.txt": {"name": "notes.txt", "mime_type": "text/plain", "content_base64": "bm90ZXM="},
    }


def test_send_file_reads_state_and_returns_download_artifact():
    tool_call = {"name": "send_file", "args": {"filename": "report.txt"}, "id": "call-1", "type": "tool_call"}
    result = invoke_send_file(
        {
            "messages": [AIMessage(content="", tool_calls=[tool_call])],
            "attachments": {
                "report.txt": {"name": "report.txt", "mime_type": "text/plain", "content_base64": "SGVsbG8="}
            },
        }
    )
    message = result["messages"][0]

    assert message.content == "Sending 'report.txt' to the user."
    assert message.artifact == {
        "attachments": [{"name": "report.txt", "mime_type": "text/plain", "content_base64": "SGVsbG8="}]
    }


def test_send_file_reports_a_missing_file():
    tool_call = {"name": "send_file", "args": {"filename": "missing.txt"}, "id": "call-1", "type": "tool_call"}
    result = invoke_send_file({"messages": [AIMessage(content="", tool_calls=[tool_call])]})

    assert result["messages"][0].content == "No stored file named 'missing.txt' is available."
    assert result["messages"][0].artifact == {"attachments": []}


def test_submit_result_validates_and_emits_structured_artifact():
    tool_call = {
        "name": "submit_result",
        "args": {
            "file_renaming": [{"old_filename": "old.pdf", "new_filename": "2026-01-01_report_V01.pdf"}],
            "checklist_status": [{"item": "Application form", "status": "offen", "reason": "Not supplied."}],
            "next_steps": [{"evidence": "Application form", "reason": "Required for submission."}],
            "conflicts": [
                {
                    "title": "Owner name conflict",
                    "detail": "The named owners differ between documents.",
                    "requested_action": "Request the current land-registry extract.",
                }
            ],
        },
        "id": "call-1",
        "type": "tool_call",
    }
    result = invoke_send_file({"messages": [AIMessage(content="", tool_calls=[tool_call])]})
    message = result["messages"][0]

    assert set(submit_result.tool_call_schema.model_json_schema()["properties"]) == {
        "file_renaming",
        "checklist_status",
        "next_steps",
        "conflicts",
    }
    assert DossierResult.model_json_schema()["$defs"]["ChecklistStatus"]["properties"]["status"]["enum"] == [
        "belegt",
        "teilweise",
        "offen",
        "nicht pruefbar",
    ]
    assert message.content == "Structured dossier result submitted."
    assert message.artifact == {
        "result": {
            "file_renaming": [{"old_filename": "old.pdf", "new_filename": "2026-01-01_report_V01.pdf"}],
            "checklist_status": [{"item": "Application form", "status": "offen", "reason": "Not supplied."}],
            "next_steps": [{"evidence": "Application form", "reason": "Required for submission."}],
            "conflicts": [
                {
                    "title": "Owner name conflict",
                    "detail": "The named owners differ between documents.",
                    "requested_action": "Request the current land-registry extract.",
                }
            ],
        }
    }


@pytest.mark.anyio
async def test_analyze_file_exposes_only_instruction_and_filename_and_sends_text_to_subagent(monkeypatch):
    monkeypatch.setattr(agent_module, "_receipt_date", lambda: "2026-09-05")
    model = FileAnalysisModel()
    tool = build_file_analysis_tool(model)
    tool_call = {
        "name": "analyze_file",
        "args": {"instruction": "List the key fact.", "filename": "notes.txt"},
        "id": "call-1",
        "type": "tool_call",
    }

    result = await invoke_file_analysis(
        tool,
        {
            "messages": [AIMessage(content="", tool_calls=[tool_call])],
            "attachments": {
                "notes.txt": {
                    "name": "notes.txt",
                    "mime_type": "text/plain",
                    "content_base64": base64.b64encode(b"The key fact is 42.").decode("ascii"),
                }
            },
        },
    )

    assert set(tool.tool_call_schema.model_json_schema()["properties"]) == {"instruction", "filename"}
    assert result["messages"][0].content == "File analysis response"
    assert model.messages[1].content == [
        {
            "type": "text",
            "text": (
                "Instruction:\nList the key fact.\n\nFilename: notes.txt\n\n"
                "Receipt date for a filename fallback: 2026-09-05. Use it only with a -E marker "
                "when the supplied material does not support a document date.\n\nFile content follows."
            ),
        },
        {"type": "text", "text": "The key fact is 42."},
    ]


@pytest.mark.anyio
async def test_analyze_file_downscales_image_and_rendered_pdf_pages():
    image = Image.new("RGBA", (2000, 1000), (255, 0, 0, 128))
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    document = pymupdf.open()
    document.new_page(width=1000, height=1600)
    pdf_bytes = document.tobytes()
    document.close()
    model = FileAnalysisModel()
    tool = build_file_analysis_tool(model)

    for filename, mime_type, content in [
        ("wide.png", "image/png", image_bytes.getvalue()),
        ("pages.pdf", "application/pdf", pdf_bytes),
    ]:
        tool_call = {
            "name": "analyze_file",
            "args": {"instruction": "Describe it.", "filename": filename},
            "id": f"call-{filename}",
            "type": "tool_call",
        }
        await invoke_file_analysis(
            tool,
            {
                "messages": [AIMessage(content="", tool_calls=[tool_call])],
                "attachments": {
                    filename: {
                        "name": filename,
                        "mime_type": mime_type,
                        "content_base64": base64.b64encode(content).decode("ascii"),
                    }
                },
            },
        )
        image_block = model.messages[1].content[1]
        with Image.open(BytesIO(base64.b64decode(image_block["base64"]))) as rendered:
            assert rendered.format == "JPEG"
            assert rendered.mode == "RGB"
            assert max(rendered.size) == 1400


@pytest.mark.anyio
async def test_analyze_file_reports_a_missing_file_without_calling_subagent():
    model = FileAnalysisModel()
    tool = build_file_analysis_tool(model)
    tool_call = {
        "name": "analyze_file",
        "args": {"instruction": "Summarize it.", "filename": "missing.txt"},
        "id": "call-1",
        "type": "tool_call",
    }

    result = await invoke_file_analysis(tool, {"messages": [AIMessage(content="", tool_calls=[tool_call])]})

    assert result["messages"][0].content == "No stored file named 'missing.txt' is available."
    assert model.messages is None
