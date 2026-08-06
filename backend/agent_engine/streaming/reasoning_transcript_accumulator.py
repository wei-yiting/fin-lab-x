"""ReasoningTranscriptAccumulator — trace-level reasoning transcript (F7 / ADR-0011).

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

        Only segments that carried text are rendered (numbered 1..K over the
        kept list): a provider reasoning block that emitted zero delta text
        must not fabricate a non-empty transcript. Whitespace-only deltas
        still count as text. An abort while an *empty* segment is open still
        carries the marker — the marker signals "a segment was in flight",
        independent of whether that segment ever produced text.
        """
        if self._capability == "unsupported":
            return self.UNSUPPORTED_SENTINEL

        kept = [text for text in self._segments if text != ""]
        body = "\n".join(
            f"=== segment {i} ===\n{text}" for i, text in enumerate(kept, start=1)
        )
        if aborted and self._open:
            # An empty open segment renders no body of its own, so the
            # marker may stand alone (no leading newline on an empty body).
            marker_suffix = f"\n{self.ABORTED_MARKER}" if body else self.ABORTED_MARKER
        else:
            marker_suffix = ""
        return self._cap(body, marker_suffix)

    @classmethod
    def _cap(cls, body: str, marker_suffix: str) -> str:
        """Bound the FINAL rendered value to ``SIZE_CAP_BYTES``.

        Truncates the tail and keeps the head, reserving room for the
        truncation note and the aborted-marker suffix so an oversized aborted
        transcript still ends with ``=== aborted ===``.
        """
        full = f"{body}{marker_suffix}"
        original_bytes = len(full.encode("utf-8"))
        if original_bytes <= cls.SIZE_CAP_BYTES:
            return full
        truncation_note = f"... [truncated, original {original_bytes} bytes]"
        reserved = len(truncation_note.encode("utf-8")) + len(
            marker_suffix.encode("utf-8")
        )
        head = body.encode("utf-8")[: cls.SIZE_CAP_BYTES - reserved].decode(
            "utf-8", errors="ignore"
        )
        return f"{head}{truncation_note}{marker_suffix}"
