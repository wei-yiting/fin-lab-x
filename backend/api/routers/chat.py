"""Chat API router for FinLab-X."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.agent_engine.agents.base import Orchestrator, ToolOutput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    tool_outputs: list[ToolOutput]
    session_id: str
    version: str


def get_orchestrator(request: Request) -> Orchestrator:
    """Get orchestrator from application state (initialized in lifespan)."""
    return request.app.state.orchestrator


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest, orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Process financial analysis chat message."""
    try:
        result = await orchestrator.arun(body.message)

        return ChatResponse(
            response=result["response"],
            tool_outputs=result["tool_outputs"],
            session_id=body.session_id or "new_session",
            version=result["version"],
        )
    except Exception:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail="Internal server error")
