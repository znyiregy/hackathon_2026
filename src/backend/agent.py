"""Construction of the LangGraph-backed chat agent."""

from typing import Any

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from src.backend.calculator import CalculationError, calculate_expression
from src.backend.config import Settings


SYSTEM_PROMPT = """You are a helpful assistant in a local hackathon application.
Use the calculation tool whenever arithmetic accuracy matters. Uploaded text and
images are part of the user's message. Mention attachment limitations honestly,
and never claim to have read content that was not provided."""


class ConfigurationError(RuntimeError):
    """Raised when required runtime configuration is missing."""


@tool
def calculation(expression: str) -> str:
    """Safely calculate a mathematical expression and return its numeric result."""

    try:
        return str(calculate_expression(expression))
    except CalculationError as exc:
        return f"Calculation error: {exc}"


def build_agent(settings: Settings) -> Any:
    if not settings.openai_api_key:
        raise ConfigurationError("OPENAI_API_KEY is not configured.")
    if not settings.openai_model:
        raise ConfigurationError("OPENAI_MODEL is not configured.")

    model = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        use_responses_api=True,
    )
    return create_agent(
        model=model,
        tools=[calculation],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
