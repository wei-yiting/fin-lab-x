"""ReasoningTraceCallback — per-LLM-call Langfuse metadata persistence (D4 / D29).

Subclasses LangChain ``BaseCallbackHandler``. On every chat-model / LLM call
completion, it extracts the joined reasoning text from the final
``AIMessage.content_blocks`` and writes it to the current Langfuse generation
as ``metadata.reasoning``.

``BaseCallbackHandler`` does not expose ``on_chat_model_end``; LangChain
dispatches chat-model completions through ``on_llm_end``. We override that
hook for both LLM and chat-model spans.

The current observation at ``on_llm_end`` time is the chat_model generation
that ``langfuse.langchain.CallbackHandler`` pushed onto the contextvars stack
when the same LLM call started.

WARNING — callback ordering:
    To guarantee this callback writes BEFORE the Langfuse handler ends and
    detaches the generation off contextvars, callers MUST register this
    callback ahead of ``langfuse.langchain.CallbackHandler``.

    callbacks=[ReasoningTraceCallback(...), CallbackHandler()]   # correct
    callbacks=[CallbackHandler(), ReasoningTraceCallback(...)]   # WRONG — Langfuse pops the generation off contextvars first

D29 schema (completed path; abort path lives in Task 6):

- capability == "unsupported"   -> ``"<unsupported>"`` regardless of message.
- capability ∈ {"on","off"}, no reasoning blocks -> ``""``.
- capability ∈ {"on","off"}, reasoning blocks present -> joined text (``"\n".join``).
- joined > SIZE_CAP_BYTES (UTF-8) -> truncate at byte boundary + suffix.

Always-write-key contract (D29 / C5.2): the ``"reasoning"`` key is written on
every invocation, including when extraction internally raises — defensive
fallback writes ``""``.
"""

from __future__ import annotations

import logging
from typing import Any, Literal
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langfuse import get_client

logger = logging.getLogger(__name__)


class ReasoningTraceCallback(BaseCallbackHandler):
    SIZE_CAP_BYTES = 500_000  # D29.2
    UNSUPPORTED_SENTINEL = "<unsupported>"  # D29.3
    METADATA_KEY = "reasoning"  # D29.1

    def __init__(
        self, *, agent_reasoning_capability: Literal["on", "off", "unsupported"]
    ) -> None:
        super().__init__()
        self._capability = agent_reasoning_capability
        # Cache the Langfuse client at construction (mirrors
        # langfuse.langchain.CallbackHandler's own pattern — single resolution
        # per request-scoped callback instance).
        self._client = get_client()

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        try:
            value = self._compute_reasoning_value(response)
        except Exception:
            logger.exception("ReasoningTraceCallback failed; emitting empty string")
            value = ""
        # chat_model spans are Langfuse "generations"; update_current_generation
        # targets the contextvars-current generation pushed by langfuse.langchain.CallbackHandler.
        self._client.update_current_generation(metadata={self.METADATA_KEY: value})

    def _compute_reasoning_value(self, response: LLMResult) -> str:
        if self._capability == "unsupported":
            return self.UNSUPPORTED_SENTINEL

        gens = response.generations
        if not gens or not gens[0]:
            return ""
        message = getattr(gens[0][0], "message", None)
        if message is None:
            return ""

        reasoning_blocks = [
            b
            for b in message.content_blocks
            if isinstance(b, dict) and b.get("type") == "reasoning"
        ]
        # `dict.get(k, default)` returns the stored value when the key exists,
        # so a present-but-None value would slip through and crash str.join.
        # Coerce non-string / None to "" defensively.
        joined = "\n".join(
            b["reasoning"] if isinstance(b.get("reasoning"), str) else ""
            for b in reasoning_blocks
        )
        if not joined:
            return ""

        encoded = joined.encode("utf-8")
        if len(encoded) > self.SIZE_CAP_BYTES:
            truncated = encoded[: self.SIZE_CAP_BYTES].decode(
                "utf-8", errors="ignore"
            )
            return f"{truncated}... [truncated, original {len(encoded)} bytes]"
        return joined
