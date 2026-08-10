"""Provider-shape integration tests for StreamEventMapper reasoning dispatch.

Each test feeds a sequence of AIMessageChunks shaped to mimic a real provider's
streaming output, then asserts the resulting native reasoning part sequence
matches the contract: one provider reasoning block maps to one part
(ReasoningStart / ReasoningDelta* / ReasoningEnd), deltas verbatim,
part ids turn-unique.
"""

from langchain_core.messages import AIMessage, AIMessageChunk

from backend.agent_engine.streaming.domain_events_schema import (
    MessageStart,
    ReasoningDelta,
    ReasoningEnd,
    ReasoningStart,
)
from backend.agent_engine.streaming.event_mapper import StreamEventMapper

SESSION_ID = "sess-int"


def _messages_chunk(msg: AIMessageChunk) -> dict:
    return {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}


class TestAnthropicInterleave:
    """Anthropic emits reasoning_A → text_1 → reasoning_B → text_2 in one LLM
    call — interleaved reasoning yields one part per contiguous block."""

    def test_interleave_ordering(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events_a = mapper.process_chunk(
            _messages_chunk(
                AIMessageChunk(
                    content=[{"type": "reasoning", "reasoning": "Thinking step A.\n"}],
                    id="msg-anth",
                )
            )
        )
        events_t1 = mapper.process_chunk(
            _messages_chunk(
                AIMessageChunk(
                    content=[{"type": "text", "text": "Answer-1 "}],
                    id="msg-anth",
                )
            )
        )
        events_b = mapper.process_chunk(
            _messages_chunk(
                AIMessageChunk(
                    content=[{"type": "reasoning", "reasoning": "Thinking step B.\n"}],
                    id="msg-anth",
                )
            )
        )
        events_t2 = mapper.process_chunk(
            _messages_chunk(
                AIMessageChunk(
                    content=[{"type": "text", "text": "Answer-2"}],
                    id="msg-anth",
                )
            )
        )

        all_events = events_a + events_t1 + events_b + events_t2

        assert all_events[0] == MessageStart(
            message_id="msg-anth", session_id=SESSION_ID
        )
        # Two distinct parts with turn-unique ids, deltas verbatim (the
        # trailing `\n` is preserved — no terminator stripping).
        starts = [e for e in all_events if isinstance(e, ReasoningStart)]
        deltas = [e for e in all_events if isinstance(e, ReasoningDelta)]
        assert [s.reasoning_id for s in starts] == ["reasoning-0", "reasoning-1"]
        assert [d.delta for d in deltas] == ["Thinking step A.\n", "Thinking step B.\n"]

        # Ordering: part A closes before text starts; part B opens after.
        types_in_order = [type(e).__name__ for e in all_events]
        assert types_in_order == [
            "MessageStart",
            "ReasoningStart",  # A
            "ReasoningDelta",  # A
            "ReasoningEnd",  # A — closed by text_1
            "TextStart",
            "TextDelta",  # Answer-1
            "ReasoningStart",  # B
            "ReasoningDelta",  # B
            "ReasoningEnd",  # B — closed by text_2
            "TextDelta",  # Answer-2 (same open text block)
        ]


class TestOpenAIMultiSummary:
    """OpenAI Responses summary array → LangChain explodes into multiple
    reasoning blocks → one part per summary block (no `\\n` join)."""

    def test_two_summary_blocks_become_two_parts(self):
        msg = AIMessage(
            content=[
                {
                    "type": "reasoning",
                    "id": "rs_abc",
                    "summary": [
                        {"type": "summary_text", "text": "Summary one."},
                        {"type": "summary_text", "text": "Summary two."},
                    ],
                }
            ],
            response_metadata={"model_provider": "openai"},
        )
        blocks = list(msg.content_blocks)
        assert len(blocks) == 2, "LangChain should explode summary array into 2 blocks"
        assert all(b.get("type") == "reasoning" for b in blocks)

        mapper = StreamEventMapper(session_id=SESSION_ID)
        chunk = AIMessageChunk(
            content=blocks,
            id="msg-openai",
            response_metadata={"output_version": "v1"},
        )
        events = mapper.process_chunk(_messages_chunk(chunk))
        events += mapper.finalize()

        reasoning_events = [
            e
            for e in events
            if isinstance(e, ReasoningStart | ReasoningDelta | ReasoningEnd)
        ]
        assert reasoning_events == [
            ReasoningStart(reasoning_id="reasoning-0"),
            ReasoningDelta(reasoning_id="reasoning-0", delta="Summary one."),
            ReasoningEnd(reasoning_id="reasoning-0"),
            ReasoningStart(reasoning_id="reasoning-1"),
            ReasoningDelta(reasoning_id="reasoning-1", delta="Summary two."),
            ReasoningEnd(reasoning_id="reasoning-1"),  # closed by finalize()
        ]


class TestGeminiRawPassthrough:
    """Gemini CJK reasoning without terminators streams through verbatim —
    no 80-char soft-emit re-chunking (that segmenter has been removed)."""

    def test_gemini_cjk_no_terminator_passthrough(self):
        long_cjk = "繁" * 110

        mapper = StreamEventMapper(session_id=SESSION_ID)
        events = mapper.process_chunk(
            _messages_chunk(
                AIMessageChunk(
                    content=[{"type": "reasoning", "reasoning": long_cjk}],
                    id="msg-gemini",
                )
            )
        )

        deltas = [e for e in events if isinstance(e, ReasoningDelta)]
        assert deltas == [ReasoningDelta(reasoning_id="reasoning-0", delta=long_cjk)]
