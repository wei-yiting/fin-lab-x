"""ReasoningTranscriptAccumulator unit tests (F7 / ADR-0007).

Pure-function coverage of the transcript value semantics: segment markers,
abort marker placement, capability sentinel values, and the size cap. No
Langfuse objects involved — the accumulator is platform-agnostic.
"""

from __future__ import annotations

from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    ReasoningDelta,
    ReasoningEnd,
    ReasoningStart,
    TextDelta,
    TextStart,
)
from backend.agent_engine.streaming.reasoning_transcript_accumulator import (
    ReasoningTranscriptAccumulator,
)


def _accumulator(
    capability: str = "on",
) -> ReasoningTranscriptAccumulator:
    return ReasoningTranscriptAccumulator(agent_reasoning_capability=capability)  # type: ignore[arg-type]


def _feed_segment(
    acc: ReasoningTranscriptAccumulator, reasoning_id: str, deltas: list[str]
) -> None:
    acc.observe(ReasoningStart(reasoning_id=reasoning_id))
    for d in deltas:
        acc.observe(ReasoningDelta(reasoning_id=reasoning_id, delta=d))
    acc.observe(ReasoningEnd(reasoning_id=reasoning_id))


class TestTranscriptShape:
    def test_single_segment(self):
        acc = _accumulator()
        _feed_segment(acc, "reasoning-0", ["think", "ing"])
        assert acc.value() == "=== segment 1 ===\nthinking"

    def test_multiple_segments_delimited_by_markers(self):
        acc = _accumulator()
        _feed_segment(acc, "reasoning-0", ["first"])
        _feed_segment(acc, "reasoning-1", ["second"])
        assert acc.value() == ("=== segment 1 ===\nfirst\n=== segment 2 ===\nsecond")

    def test_non_reasoning_events_are_ignored(self):
        acc = _accumulator()
        acc.observe(TextStart(text_id="t0"))
        _feed_segment(acc, "reasoning-0", ["thought"])
        acc.observe(TextDelta(text_id="t0", delta="answer"))
        acc.observe(Finish(finish_reason="ready"))
        assert acc.value() == "=== segment 1 ===\nthought"

    def test_delta_without_start_opens_segment_implicitly(self):
        acc = _accumulator()
        acc.observe(ReasoningDelta(reasoning_id="reasoning-0", delta="orphan"))
        assert acc.value() == "=== segment 1 ===\norphan"


class TestCapabilityValues:
    def test_unsupported_returns_sentinel(self):
        acc = _accumulator("unsupported")
        assert acc.value() == "<unsupported>"

    def test_unsupported_sentinel_never_carries_abort_marker(self):
        acc = _accumulator("unsupported")
        assert acc.value(aborted=True) == "<unsupported>"

    def test_no_reasoning_returns_empty_string(self):
        acc = _accumulator("on")
        assert acc.value() == ""

    def test_off_capability_with_no_events_returns_empty_string(self):
        acc = _accumulator("off")
        assert acc.value() == ""


class TestAbortMarker:
    def test_abort_mid_segment_appends_marker(self):
        acc = _accumulator()
        acc.observe(ReasoningStart(reasoning_id="reasoning-0"))
        acc.observe(ReasoningDelta(reasoning_id="reasoning-0", delta="partial tail"))
        assert acc.value(aborted=True) == (
            "=== segment 1 ===\npartial tail\n=== aborted ==="
        )

    def test_abort_between_segments_has_no_marker(self):
        acc = _accumulator()
        _feed_segment(acc, "reasoning-0", ["complete thought"])
        assert acc.value(aborted=True) == "=== segment 1 ===\ncomplete thought"

    def test_abort_before_any_reasoning_returns_empty_string(self):
        acc = _accumulator()
        assert acc.value(aborted=True) == ""

    def test_abort_marker_after_earlier_complete_segments(self):
        acc = _accumulator()
        _feed_segment(acc, "reasoning-0", ["done"])
        acc.observe(ReasoningStart(reasoning_id="reasoning-1"))
        acc.observe(ReasoningDelta(reasoning_id="reasoning-1", delta="cut"))
        assert acc.value(aborted=True) == (
            "=== segment 1 ===\ndone\n=== segment 2 ===\ncut\n=== aborted ==="
        )


class TestSizeCap:
    def test_under_cap_untouched(self):
        acc = _accumulator()
        _feed_segment(acc, "reasoning-0", ["x" * 1000])
        value = acc.value()
        assert "[truncated" not in value

    def test_over_cap_truncates_tail_and_keeps_head(self):
        acc = _accumulator()
        cap = ReasoningTranscriptAccumulator.SIZE_CAP_BYTES
        _feed_segment(acc, "reasoning-0", ["a" * (cap + 100)])
        value = acc.value()
        assert value.startswith("=== segment 1 ===\naaa")
        assert value.endswith(f"... [truncated, original {cap + 100 + 18} bytes]")

    def test_truncation_respects_utf8_boundaries(self):
        acc = _accumulator()
        cap = ReasoningTranscriptAccumulator.SIZE_CAP_BYTES
        # Multi-byte characters spanning the cap boundary must not produce
        # a decode error or a mangled trailing character.
        _feed_segment(acc, "reasoning-0", ["中" * (cap // 3 + 100)])
        value = acc.value()
        assert "[truncated" in value
        assert "�" not in value
