import src.backend.agent as agent_module
from src.backend.agent import ConfigurationError, build_agent
from src.backend.config import Settings


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


def test_build_agent_requires_reasoning_effort():
    settings = Settings(_env_file=None, openai_api_key="test-key", openai_model="test-model")
    try:
        build_agent(settings)
    except ConfigurationError as exc:
        assert str(exc) == "REASONING_EFFORT is not configured."
    else:
        raise AssertionError("build_agent should reject missing reasoning effort")
