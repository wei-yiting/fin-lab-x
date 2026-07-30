"""ReasoningTranscriptAccumulator — trace-level reasoning transcript (F7 / ADR-0007).

Observes the reasoning domain events (``ReasoningStart`` / ``ReasoningDelta`` /
``ReasoningEnd``) that ``StreamEventMapper`` already emits to the client, and
builds the single transcript string written once to the root trace metadata
when the conversation ends. Collecting from the event stream (not from
``on_llm_end`` content blocks) is what makes the abort tail available: an
aborted in-flight LLM call never fires ``on_llm_end``, but its streamed
deltas have already passed through here.

Transcript shape (single ``reasoning`` key, markers inside the value):

- one ``=== segment N ===`` header per reasoning segment (a segment is one
  provider reasoning block — the same unit as a frontend reasoning chip)
- ``=== aborted ===`` appended only when the conversation aborts while a
  segment is still open; it marks transcript integrity ("the last segment may
  be cut mid-thought"). Conversation-level aborts are owned by the separate
  ``status: "aborted"`` metadata key, not by this marker.

Always-write-key contract (carried over from D29 / C5.2): the caller writes
the ``reasoning`` key on every conversation — ``"<unsupported>"`` for agents
without reasoning capability, ``""`` when no reasoning was produced.

This class is platform-agnostic — it knows nothing about Langfuse and moves
unchanged to the Braintrust backend (DEV-114).
"""

from __future__ import annotations

from typing import Literal

from backend.agent_engine.streaming.domain_events_schema import (
    DomainEvent,
    ReasoningDelta,
    ReasoningEnd,
    ReasoningStart,
)


class ReasoningTranscriptAccumulator:
    SIZE_CAP_BYTES = 500_000
    UNSUPPORTED_SENTINEL = "<unsupported>"
    METADATA_KEY = "reasoning"
    ABORTED_MARKER = "=== aborted ==="

    def __init__(
        self,
        *,
        agent_reasoning_capability: Literal["on", "off", "unsupported"],
    ) -> None:
        self._capability = agent_reasoning_capability
        self._segments: list[str] = []
        self._open = False

    def observe(self, event: DomainEvent) -> None:
        if isinstance(event, ReasoningStart):
            self._segments.append("")
            self._open = True
        elif isinstance(event, ReasoningDelta):
            # The mapper contract guarantees Start before Delta; open a
            # segment implicitly anyway so contract drift degrades to a
            # missing header instead of silently dropped text.
            if not self._open:
                self._segments.append("")
                self._open = True
            self._segments[-1] += event.delta
        elif isinstance(event, ReasoningEnd):
            self._open = False

    def value(self, *, aborted: bool = False) -> str:
        """Render the transcript to write under the ``reasoning`` key.

        ``aborted=True`` appends the aborted marker only when a segment is
        still open — a conversation aborted between segments has a complete
        transcript and carries no marker.
        """
        if self._capability == "unsupported":
            return self.UNSUPPORTED_SENTINEL

        parts = [
            f"=== segment {i} ===\n{text}"
            for i, text in enumerate(self._segments, start=1)
        ]
        if aborted and self._open:
            parts.append(self.ABORTED_MARKER)
        return self._cap(("\n".join(parts)))

    @classmethod
    def _cap(cls, transcript: str) -> str:
        encoded = transcript.encode("utf-8")
        if len(encoded) <= cls.SIZE_CAP_BYTES:
            return transcript
        truncated = encoded[: cls.SIZE_CAP_BYTES].decode("utf-8", errors="ignore")
        return f"{truncated}... [truncated, original {len(encoded)} bytes]"
