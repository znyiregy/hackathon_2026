"""Construction of the LangGraph-backed chat agent."""

from typing import Annotated, Any, TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentState
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import InjectedState

from src.backend.calculator import CalculationError, calculate_expression
from src.backend.config import Settings


SYSTEM_PROMPT = """You are a helpful assistant in a local hackathon application.
Use the calculation tool whenever arithmetic accuracy matters. Uploaded files
are stored privately and only their filenames are provided to you; you cannot
read or analyze their contents. When the user asks to download or receive a
stored file, call send_file with its exact filename. Mention attachment
limitations honestly, and never claim to have read content that was not
provided."""


class ConfigurationError(RuntimeError):
    """Raised when required runtime configuration is missing."""


class StoredAttachment(TypedDict):
    name: str
    mime_type: str
    content_base64: str


def _merge_attachments(
    current: dict[str, StoredAttachment] | None,
    incoming: dict[str, StoredAttachment] | None,
) -> dict[str, StoredAttachment]:
    """Retain thread files while letting later equal filenames replace earlier ones."""

    return {**(current or {}), **(incoming or {})}


class ChatAgentState(AgentState):
    attachments: Annotated[dict[str, StoredAttachment], _merge_attachments]


@tool
def calculation(expression: str) -> str:
    """Safely calculate a mathematical expression and return its numeric result."""

    try:
        return str(calculate_expression(expression))
    except CalculationError as exc:
        return f"Calculation error: {exc}"


@tool(response_format="content_and_artifact")
def send_file(
    filename: str,
    state: Annotated[dict[str, Any], InjectedState],
) -> tuple[str, dict[str, list[StoredAttachment]]]:
    """Send a previously uploaded file to the user by its exact filename."""

    attachments = state.get("attachments", {})
    attachment = attachments.get(filename) if isinstance(attachments, dict) else None
    if not isinstance(attachment, dict):
        return f"No stored file named {filename!r} is available.", {"attachments": []}
    return f"Sending {filename!r} to the user.", {"attachments": [attachment]}


def build_agent(settings: Settings) -> Any:
    if not settings.openai_api_key:
        raise ConfigurationError("OPENAI_API_KEY is not configured.")
    if not settings.openai_model:
        raise ConfigurationError("OPENAI_MODEL is not configured.")
    if not settings.reasoning_effort:
        raise ConfigurationError("REASONING_EFFORT is not configured.")

    model = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        use_responses_api=True,
        reasoning={"effort": settings.reasoning_effort},
    )
    return create_agent(
        model=model,
        tools=[calculation, send_file],
        system_prompt=SYSTEM_PROMPT,
        state_schema=ChatAgentState,
        checkpointer=InMemorySaver(),
    )
