import src.backend.agent as agent_module
from langchain.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.backend.agent import ConfigurationError, _merge_attachments, build_agent, send_file
from src.backend.config import Settings


def invoke_send_file(state):
    graph = StateGraph(dict)
    graph.add_node("tools", ToolNode([send_file]))
    graph.add_edge(START, "tools")
    graph.add_edge("tools", END)
    return graph.compile().invoke(state)


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
    assert captured["agent"]["tools"] == [agent_module.calculation, send_file]
    assert captured["agent"]["state_schema"] is agent_module.ChatAgentState


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
