"""Streaming chat API router for FinLab-X."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator
from typing import Literal

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.streaming.domain_events_schema import Finish, StreamError
from backend.agent_engine.streaming.sse_serializer import serialize_event
from backend.agent_engine.streaming.tool_error_sanitizer import sanitize_tool_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])

_active_sessions: set[str] = set()


class StreamChatRequest(BaseModel):
    id: str = Field(..., min_length=1)
    message: str | None = None
    trigger: Literal["regenerate"] | None = None
    messageId: str | None = None

    @model_validator(mode="after")
    def validate_request(self):
        has_message = self.message is not None and self.message.strip() != ""
        if has_message and self.trigger:
            raise ValueError("Cannot have both message and trigger")
        if not has_message and not self.trigger:
            raise ValueError("Must have either message or trigger")
        if self.trigger == "regenerate" and not self.messageId:
            raise ValueError("messageId required for regenerate")
        if has_message:
            self.message = self.message.strip()
        return self


def get_orchestrator(request: Request) -> Orchestrator:
    """Get orchestrator from application state (initialized in lifespan)."""
    return request.app.state.orchestrator


@router.post("/chat")
async def stream_chat(
    body: StreamChatRequest,
    request: Request,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """Stream financial analysis chat response via SSE."""
    if body.trigger == "regenerate":
        try:
            await orchestrator.validate_regenerate(
                session_id=body.id, message_id=body.messageId
            )
        except ValueError as e:
            err_msg = str(e)
            if "no conversation" in err_msg.lower() or "no assistant" in err_msg.lower():
                raise HTTPException(status_code=404, detail=err_msg)
            raise HTTPException(status_code=422, detail=err_msg)

    if body.id in _active_sessions:
        raise HTTPException(status_code=409, detail="Session busy")
    _active_sessions.add(body.id)

    async def generate():
        try:
            async for event in orchestrator.astream_run(
                message=body.message,
                session_id=body.id,
                trigger=body.trigger,
                message_id=body.messageId,
            ):
                if await request.is_disconnected():
                    break
                yield serialize_event(event)
        except ValueError as e:
            yield serialize_event(StreamError(error_text=sanitize_tool_error(str(e))))
            yield serialize_event(Finish(finish_reason="error"))
        finally:
            _active_sessions.discard(body.id)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "x-vercel-ai-ui-message-stream": "v1",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
