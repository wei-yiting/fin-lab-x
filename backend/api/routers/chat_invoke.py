"""Chat API router for FinLab-X."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.agent_engine.agents.base import Orchestrator, ToolOutput
from backend.agent_engine.byok import ByokKeyRejectedError
from backend.api.byok import KEY_REJECTED_DETAIL, get_byok_api_key

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
    body: ChatRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    api_key: str | None = Depends(get_byok_api_key),
):
    """Process financial analysis chat message."""
    try:
        session_id = body.session_id or str(uuid.uuid4())
        request_id = uuid.uuid4().hex
        result = await orchestrator.arun(
            body.message,
            session_id=session_id,
            request_id=request_id,
            api_key=api_key,
        )

        return ChatResponse(
            response=result["response"],
            tool_outputs=result["tool_outputs"],
            session_id=session_id,
            version=result["version"],
        )
    except ByokKeyRejectedError:
        # The provider rejected the user's own key — a clean, actionable
        # 401, never the provider's raw message.
        raise HTTPException(status_code=401, detail=KEY_REJECTED_DETAIL)
    except Exception:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail="Internal server error")
