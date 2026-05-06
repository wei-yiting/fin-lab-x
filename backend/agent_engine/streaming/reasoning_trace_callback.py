"""ReasoningTraceCallback — per-LLM-call Langfuse metadata persistence (D4 / D29).

Subclasses LangChain ``BaseCallbackHandler``. On every chat-model / LLM call
completion, it extracts the joined reasoning text from the final
``AIMessage.content_blocks`` and writes it to the matching Langfuse
generation as ``metadata.reasoning``.

``BaseCallbackHandler`` does not expose ``on_chat_model_end``; LangChain
dispatches chat-model completions through ``on_llm_end``. We override that
hook for both LLM and chat-model spans.

Lookup-by-run_id (not contextvars):
    Earlier versions called ``client.update_current_generation()``, which
    targets whatever OTel span is current at call time. On LangChain's async
    dispatch path the OTel context that ``langfuse.langchain.CallbackHandler``
    attaches to the GENERATION span does not always reach our callback's
    frame — the dispatcher snapshots context per-callback, so the "current"
    span can be ``None`` or a parent CHAIN, and the update silently no-ops.
    The smoking gun for that is "Context error: No active span in current
    context" warning lines around ``on_llm_end``.

    Instead we reach into ``langfuse.langchain.CallbackHandler._runs`` —
    the run_id → ``LangfuseGeneration`` mapping the handler maintains for
    its own bookkeeping (see Langfuse 4.x source: ``_attach_observation``
    sets ``self._runs[run_id] = observation``; ``on_llm_new_token`` already
    relies on the same dict). Looking up the GENERATION by ``run_id`` is
    deterministic regardless of dispatch ordering or OTel context state.

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
from typing import TYPE_CHECKING, Any, Literal
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langfuse import LangfuseGeneration, get_client

if TYPE_CHECKING:
    from langfuse.langchain import CallbackHandler as LangfuseLangchainHandler

logger = logging.getLogger(__name__)


class ReasoningTraceCallback(BaseCallbackHandler):
    SIZE_CAP_BYTES = 500_000  # D29.2
    UNSUPPORTED_SENTINEL = "<unsupported>"  # D29.3
    METADATA_KEY = "reasoning"  # D29.1
    # Even with lookup-by-run_id, we still want to dispatch inline so the
    # write happens before any teardown that could end the generation span
    # (and before any other callback runs that might depend on metadata
    # being present).
    run_inline = True

    def __init__(
        self,
        *,
        agent_reasoning_capability: Literal["on", "off", "unsupported"],
        langfuse_handler: "LangfuseLangchainHandler | None" = None,
    ) -> None:
        super().__init__()
        self._capability = agent_reasoning_capability
        # Cache the Langfuse client at construction (mirrors
        # langfuse.langchain.CallbackHandler's own pattern — single resolution
        # per request-scoped callback instance). Only used for the no-handler
        # fallback path (legacy / unit tests).
        self._client = get_client()
        # Optional reference to the Langfuse Langchain handler. When supplied
        # we look up the GENERATION span by run_id rather than relying on
        # OTel current-span propagation. This is the production path.
        self._handler = langfuse_handler

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

        if self._handler is not None:
            generation = self._handler._runs.get(run_id)
            if isinstance(generation, LangfuseGeneration):
                generation.update(metadata={self.METADATA_KEY: value})
                return
            logger.warning(
                "ReasoningTraceCallback: run_id %s not found in handler._runs "
                "(or not a LangfuseGeneration: %s); falling back to "
                "update_current_generation()",
                run_id,
                type(generation).__name__ if generation is not None else None,
            )

        # Fallback: legacy / unit-test path with no handler reference. Targets
        # the OTel current-span — works for sync dispatch, may silently no-op
        # on async paths.
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
            truncated = encoded[: self.SIZE_CAP_BYTES].decode("utf-8", errors="ignore")
            return f"{truncated}... [truncated, original {len(encoded)} bytes]"
        return joined
