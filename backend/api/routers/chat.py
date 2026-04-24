"""Streaming chat API router for FinLab-X."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, PrivateAttr, model_validator
from typing import Literal

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.streaming.domain_events_schema import Finish, StreamError
from backend.agent_engine.streaming.sse_serializer import serialize_event
from backend.agent_engine.streaming.tool_error_sanitizer import sanitize_tool_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])

_active_sessions: set[str] = set()


class MessagePart(BaseModel):
    type: str
    text: str = ""


class ChatMessage(BaseModel):
    role: str
    parts: list[MessagePart]


class StreamChatRequest(BaseModel):
    id: str = Field(..., min_length=1)
    messages: list[ChatMessage]
    trigger: Literal["submit-message", "regenerate-message"]
    messageId: str | None = None

    _user_text: str | None = PrivateAttr(default=None)
    _normalized_trigger: str | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def validate_request(self):
        is_regenerate = self.trigger == "regenerate-message"
        self._normalized_trigger = "regenerate" if is_regenerate else None

        if is_regenerate:
            if not self.messageId:
                raise ValueError("messageId required for regenerate")
            self._user_text = None
            return self

        user_text = None
        for msg in reversed(self.messages):
            if msg.role == "user":
                joined = " ".join(
                    part.text.strip() for part in msg.parts if part.type == "text"
                )
                if joined:
                    user_text = joined
                    break
        if not user_text:
            raise ValueError("Must have a user message for submit")
        self._user_text = user_text
        return self

    @property
    def user_text(self) -> str | None:
        return self._user_text

    @property
    def normalized_trigger(self) -> str | None:
        return self._normalized_trigger


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
    if body.normalized_trigger == "regenerate":
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

    request_id = uuid.uuid4().hex

    async def generate():
        try:
            async for event in orchestrator.astream_run(
                message=body.user_text,
                session_id=body.id,
                trigger=body.normalized_trigger,
                message_id=body.messageId,
                request_id=request_id,
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
