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

Why we accept the ``_runs`` private-API dependency:
    We probed Langfuse 4.5's public API surface: ``CallbackHandler`` exposes
    only the ``on_*`` LangChain hooks, ``ignore_*`` flags, and ``run_inline``
    — there is no ``get_observation_by_run_id`` or equivalent. The other
    options (``start_observation`` / ``start_as_current_observation``) create
    NEW observations, which would duplicate the generation in the trace;
    the ``update_current_*`` family — ``update_current_generation`` (for
    generation-type observations) and ``update_current_span`` (for
    span-type observations) — is the OTel-context-based path with the
    documented async-context bug above. Until Langfuse ships a public lookup
    API, we read from ``_runs``.

    Defense-in-depth against SDK drift:
      1. ``_lookup_generation_by_run_id`` (this file) tries the UUID key
         first, then ``str(run_id)`` and ``run_id.hex`` as fallbacks. Any
         fallback hit logs once-per-process so ops sees the drift signal.
      2. ``_handle_abort_cleanup`` in ``agents/base.py`` iterates
         ``handler._runs.values()`` — value-iteration is immune to key-shape
         drift, only type-shape drift breaks it (caught by isinstance).
      3. ``test_langfuse_runs_contract.py`` drives Langfuse's real
         ``on_chain_start`` and ``on_chat_model_start`` and asserts the
         EXACT UUID key + concrete ``LangfuseChain``/``LangfuseGeneration``
         type, so any SDK drift on either dimension fails CI loudly.

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
    # Class-level latch so the SDK-drift warning fires at most once per
    # process. Without this, every LLM call after the first drift would
    # spam the log line. False = no drift seen yet.
    _drift_warned: bool = False

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
            generation = self._lookup_generation_by_run_id(run_id)
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

    def _lookup_generation_by_run_id(self, run_id: UUID) -> Any:
        """Look up the in-flight Langfuse observation for ``run_id`` with
        SDK-drift fallbacks.

        Tries three key shapes in order:
          1. ``run_id`` (UUID) — the current Langfuse 4.5 contract, asserted
             by ``test_langfuse_runs_contract.py``.
          2. ``str(run_id)`` — most likely drift mode if Langfuse ever
             normalizes keys to strings.
          3. ``run_id.hex`` — second-most-likely drift mode (dashless hex).

        Returns whatever is stored under the first key that hits, or
        ``None``. The caller is responsible for ``isinstance(..., LangfuseGeneration)``
        narrowing before writing metadata.

        Hitting a fallback path logs ONCE per process (class-level
        ``_drift_warned`` latch) telling ops to update the contract test
        and consider pinning the Langfuse version. We don't raise — the
        write still succeeds via the fallback — so production keeps
        working while the drift signal reaches engineering.
        """
        runs = self._handler._runs  # type: ignore[union-attr]
        observation = runs.get(run_id)
        if observation is not None:
            return observation

        # Fallback 1: string-normalized UUID.
        observation = runs.get(str(run_id))
        if observation is not None:
            self._warn_drift_once("str(uuid)")
            return observation

        # Fallback 2: hex without dashes.
        observation = runs.get(run_id.hex)
        if observation is not None:
            self._warn_drift_once("uuid.hex")
            return observation

        return None

    @classmethod
    def _warn_drift_once(cls, drift_mode: str) -> None:
        """Log the SDK-drift warning at most once per process."""
        if cls._drift_warned:
            return
        cls._drift_warned = True
        logger.warning(
            "Langfuse _runs key drifted to %s — production lookup is using "
            "fallback. Update the contract test in "
            "test_langfuse_runs_contract.py and consider pinning a Langfuse "
            "version.",
            drift_mode,
        )

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
