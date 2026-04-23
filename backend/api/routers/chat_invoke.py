"""Chat API router for FinLab-X."""

import logging
import uuid

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


@router.post("/chat/invoke", response_model=ChatResponse)
async def chat(
    body: ChatRequest, orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Process financial analysis chat message."""
    try:
        session_id = body.session_id or str(uuid.uuid4())
        request_id = uuid.uuid4().hex
        result = await orchestrator.arun(
            body.message, session_id=session_id, request_id=request_id
        )

        return ChatResponse(
            response=result["response"],
            tool_outputs=result["tool_outputs"],
            session_id=session_id,
            version=result["version"],
        )
    except Exception:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail="Internal server error")
