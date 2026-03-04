"""Chat API router for FinLab-X."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

from backend.agent_engine.orchestrator.base import Orchestrator
from backend.agent_engine.workflows.config_loader import VersionConfigLoader

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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process financial analysis chat message.

    Args:
        request: Chat request with message and optional session ID

    Returns:
        Chat response with analysis results
    """
    try:
        config_loader = VersionConfigLoader("v1_baseline")
        config = config_loader.load()

        orchestrator = Orchestrator(config)

        result = orchestrator.run(request.message)

        return ChatResponse(
            response=result.get("response", ""),
            tool_outputs=result.get("tool_outputs", []),
            session_id=request.session_id or "new_session",
            version=result.get("version", "0.1.0"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
