"""Chat API router for FinLab-X."""

import logging
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import VersionConfigLoader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    tool_outputs: list[dict[str, Any]]
    session_id: str
    version: str


@lru_cache(maxsize=1)
def _get_orchestrator() -> Orchestrator:
    config = VersionConfigLoader("v1_baseline").load()
    return Orchestrator(config)


def get_orchestrator() -> Orchestrator:
    return _get_orchestrator()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Process financial analysis chat message."""
    try:
        result = orchestrator.run(request.message)

        return ChatResponse(
            response=result.get("response", ""),
            tool_outputs=result.get("tool_outputs", []),
            session_id=request.session_id or "new_session",
            version=result.get("version", "0.1.0"),
        )
    except Exception:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail="Internal server error")
