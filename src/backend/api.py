"""FastAPI presentation layer."""

import logging
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, status
from src.backend.agent import ConfigurationError, build_agent
from src.backend.attachments import AttachmentError, AttachmentTooLargeError
from src.backend.config import get_settings
from src.backend.schemas import ChatRequest, ChatResponse, HealthResponse
from src.backend.service import AgentInvocationError, ChatService


logger = logging.getLogger(__name__)
app = FastAPI(title="Hackathon LangGraph API", version="0.1.0")


@lru_cache
def _build_chat_service() -> ChatService:
    return ChatService(build_agent(get_settings()))


async def get_chat_service() -> ChatService:
    try:
        return _build_chat_service()
    except ConfigurationError as exc:
        logger.error("Backend configuration error: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    try:
        result = await service.chat(request)
    except AttachmentTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc
    except AttachmentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ConfigurationError as exc:
        logger.error("Backend configuration error: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except AgentInvocationError as exc:
        logger.exception("Agent invocation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The language model could not complete the request.",
        ) from exc
    return ChatResponse(thread_id=request.thread_id, answer=result.answer, messages=result.messages)
