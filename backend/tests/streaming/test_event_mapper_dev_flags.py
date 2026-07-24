"""Dev-only env-flag handlers in StreamEventMapper.

Task 15 ships four mapper-level flags consumed via os.environ. Production
must NOT set any of them; they exist exclusively to drive Playwright
visual lifecycle scenarios for which there is no natural-stream
equivalent (stalled indicator, late post-finish event, content_blocks
normalizer regression, reasoning-only stub).

Test naming intentionally matches the ``-k "dev_flag or stub or force"``
filter from the Task 15 verification command.
"""

from __future__ import annotations

from langchain_core.messages import AIMessageChunk

from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    ReasoningStatus,
    TextDelta,
    TextStart,
)
from backend.agent_engine.streaming.event_mapper import StreamEventMapper

SESSION_ID = "sess-dev-flag"


def _messages_chunk(msg: AIMessageChunk) -> dict:
    return {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}


def _msg_with_blocks(blocks: list[dict], msg_id: str = "msg-flag") -> dict:
    return _messages_chunk(AIMessageChunk(content=blocks, id=msg_id))


class TestStubReasoningOnlyDevFlag:
    """STUB_REASONING_ONLY — drop text + tool_call_chunk blocks; reasoning passes through.

    Drives S-trace-05 (trace tail emits reasoning even with no text/tool stream).
    """

    def test_stub_reasoning_only_skips_text_blocks(self, monkeypatch):
        monkeypatch.setenv("STUB_REASONING_ONLY", "1")
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            _msg_with_blocks(
                [
                    {"type": "reasoning", "reasoning": "Thinking.\n"},
                    {"type": "text", "text": "ANSWER"},
                ]
            )
        )

        assert any(isinstance(e, ReasoningStatus) for e in events)
        assert not any(isinstance(e, TextStart) for e in events)
        assert not any(isinstance(e, TextDelta) for e in events)

    def test_stub_reasoning_only_skips_tool_call_chunk_blocks(self, monkeypatch):
        monkeypatch.setenv("STUB_REASONING_ONLY", "1")
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            _msg_with_blocks(
                [
                    {"type": "reasoning", "reasoning": "Plan.\n"},
                    {"type": "tool_call_chunk", "id": "tc-1", "name": "fn"},
                ]
            )
        )
        # No tool_call should survive the stub. Reasoning should still flow.
        assert any(isinstance(e, ReasoningStatus) for e in events)
        assert mapper._pending_tool_calls == {}

    def test_unset_passes_text_through(self, monkeypatch):
        monkeypatch.delenv("STUB_REASONING_ONLY", raising=False)
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            _msg_with_blocks([{"type": "text", "text": "OK"}])
        )
        assert any(isinstance(e, TextDelta) for e in events)


class TestStubContentBlocksNoReasoningDevFlag:
    """STUB_CONTENT_BLOCKS_NO_REASONING=<provider> — simulate normalizer drop of reasoning blocks.

    Drives S-trace-09 (regression: content_blocks normalizer fails for a provider
    so no reasoning blocks reach the mapper).
    """

    def test_stub_content_blocks_no_reasoning_drops_reasoning(self, monkeypatch):
        monkeypatch.setenv("STUB_CONTENT_BLOCKS_NO_REASONING", "gemini")
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            _msg_with_blocks(
                [
                    {"type": "reasoning", "reasoning": "Hidden thought.\n"},
                    {"type": "text", "text": "answer"},
                ]
            )
        )
        # Reasoning is filtered out; text still streams.
        assert not any(isinstance(e, ReasoningStatus) for e in events)
        assert any(isinstance(e, TextDelta) for e in events)

    def test_unset_passes_reasoning_through(self, monkeypatch):
        monkeypatch.delenv("STUB_CONTENT_BLOCKS_NO_REASONING", raising=False)
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            _msg_with_blocks([{"type": "reasoning", "reasoning": "Visible.\n"}])
        )
        assert any(isinstance(e, ReasoningStatus) for e in events)


class TestEmitDelayedReasoningDevFlag:
    """EMIT_DELAYED_REASONING — only the FIRST reasoning chunk emits; subsequent
    reasoning blocks are dropped within the same mapper instance.

    Drives S-rsn-06 (stalled visual). The "delay" comes from the natural
    stream's silence between the lone reasoning emission and finish — the
    frontend's STALLED_THRESHOLD_MS poll flips ``stalled=true`` after 10s.
    Doing a real time.sleep here would block the sync mapper path; the
    "drop subsequent" semantic produces the same observable effect with
    no async machinery.
    """

    def test_emit_delayed_reasoning_emits_only_first_chunk(self, monkeypatch):
        monkeypatch.setenv("EMIT_DELAYED_REASONING", "1")
        mapper = StreamEventMapper(session_id=SESSION_ID)

        first = mapper.process_chunk(
            _msg_with_blocks(
                [{"type": "reasoning", "reasoning": "First.\n"}], msg_id="m1"
            )
        )
        second = mapper.process_chunk(
            _msg_with_blocks(
                [{"type": "reasoning", "reasoning": "Second.\n"}], msg_id="m1"
            )
        )

        first_reasoning = [e for e in first if isinstance(e, ReasoningStatus)]
        second_reasoning = [e for e in second if isinstance(e, ReasoningStatus)]
        assert len(first_reasoning) == 1
        assert first_reasoning[0].text == "First."
        assert second_reasoning == []

    def test_unset_emits_every_reasoning_chunk(self, monkeypatch):
        monkeypatch.delenv("EMIT_DELAYED_REASONING", raising=False)
        mapper = StreamEventMapper(session_id=SESSION_ID)

        first = mapper.process_chunk(
            _msg_with_blocks([{"type": "reasoning", "reasoning": "A.\n"}], msg_id="m1")
        )
        second = mapper.process_chunk(
            _msg_with_blocks([{"type": "reasoning", "reasoning": "B.\n"}], msg_id="m1")
        )
        assert any(isinstance(e, ReasoningStatus) for e in first)
        assert any(isinstance(e, ReasoningStatus) for e in second)


class TestEmitLateReasoningDevFlag:
    """EMIT_LATE_REASONING — finalize injects a synthetic ReasoningStatus AFTER
    the Finish event. Drives S-rsn-12.

    The frontend's ``finishedRef`` (latched on ``finish`` / ``error``) is the
    actual consumer-side guard; this flag fabricates the wire-side stimulus
    that exercises it.
    """

    def test_emit_late_reasoning_appends_after_finish(self, monkeypatch):
        monkeypatch.setenv("EMIT_LATE_REASONING", "1")
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(_msg_with_blocks([{"type": "text", "text": "ok"}]))

        events = mapper.finalize()
        types = [type(e).__name__ for e in events]
        assert "Finish" in types
        finish_idx = types.index("Finish")
        # ReasoningStatus must appear AFTER Finish.
        assert "ReasoningStatus" in types[finish_idx + 1 :]
        late = [e for e in events[finish_idx + 1 :] if isinstance(e, ReasoningStatus)]
        assert late and "late" in late[0].reasoning_id

    def test_unset_finalize_does_not_emit_late_reasoning(self, monkeypatch):
        monkeypatch.delenv("EMIT_LATE_REASONING", raising=False)
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(_msg_with_blocks([{"type": "text", "text": "ok"}]))

        events = mapper.finalize()
        last = events[-1]
        assert isinstance(last, Finish)
