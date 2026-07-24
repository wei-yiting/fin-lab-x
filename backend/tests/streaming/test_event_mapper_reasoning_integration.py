"""Provider-shape integration tests for StreamEventMapper reasoning dispatch.

Each test feeds a sequence of AIMessageChunks shaped to mimic a real provider's
streaming output, then asserts the resulting domain-event ordering matches the
design contract (D12, D13, D26).
"""

from langchain_core.messages import AIMessage, AIMessageChunk

from backend.agent_engine.streaming.domain_events_schema import (
    MessageStart,
    ReasoningStatus,
)
from backend.agent_engine.streaming.event_mapper import StreamEventMapper
from backend.agent_engine.streaming.reasoning_segmenter import ReasoningSegmenter

SESSION_ID = "sess-int"


def _messages_chunk(msg: AIMessageChunk) -> dict:
    return {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}


class TestAnthropicInterleave:
    """D13: Anthropic emits reasoning_A → text_1 → reasoning_B → text_2 in one LLM call."""

    def test_interleave_ordering(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        # reasoning_A — terminator-bounded sentence emits immediately
        events_a = mapper.process_chunk(
            _messages_chunk(
                AIMessageChunk(
                    content=[{"type": "reasoning", "reasoning": "Thinking step A.\n"}],
                    id="msg-anth",
                )
            )
        )
        # text_1 — D28 hold-and-flush guarantees no buffered reasoning leaks past TextStart
        events_t1 = mapper.process_chunk(
            _messages_chunk(
                AIMessageChunk(
                    content=[{"type": "text", "text": "Answer-1 "}],
                    id="msg-anth",
                )
            )
        )
        # reasoning_B — re-entry, same reasoning_id (D27.2 same chunk.id)
        events_b = mapper.process_chunk(
            _messages_chunk(
                AIMessageChunk(
                    content=[{"type": "reasoning", "reasoning": "Thinking step B.\n"}],
                    id="msg-anth",
                )
            )
        )
        # text_2 — same text block continues
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
        # Reasoning sentences emitted (terminator + \n strips newline)
        reasoning_events = [e for e in all_events if isinstance(e, ReasoningStatus)]
        assert len(reasoning_events) == 2
        assert reasoning_events[0].text == "Thinking step A."
        assert reasoning_events[1].text == "Thinking step B."
        # Same reasoning_id across the same LLM call
        assert reasoning_events[0].reasoning_id == reasoning_events[1].reasoning_id

        # Verify ordering: ReasoningStatus(A) before TextStart, TextStart before
        # ReasoningStatus(B), and ReasoningStatus(B) before TextDelta(2).
        types_in_order = [type(e).__name__ for e in all_events]
        assert types_in_order == [
            "MessageStart",
            "ReasoningStatus",  # A
            "TextStart",
            "TextDelta",  # Answer-1
            "ReasoningStatus",  # B
            "TextDelta",  # Answer-2 (same text block)
        ]


class TestOpenAIMultiSummary:
    """D12: OpenAI Responses summary array → LangChain explodes into multiple reasoning blocks."""

    def test_two_summary_blocks_emit_two_reasoning_status(self):
        # AIMessage carrying OpenAI summary structure. The model_provider hint
        # routes through LangChain's OpenAI translator which explodes the
        # `summary` list into one reasoning block per `summary_text` entry.
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
        # Wrap as an AIMessageChunk-shaped payload by feeding both blocks
        # via a single chunk whose content is the exploded list. We pass the
        # already-normalized list directly so content_blocks short-circuits.
        chunk = AIMessageChunk(
            content=blocks,
            id="msg-openai",
            response_metadata={"output_version": "v1"},
        )
        events = mapper.process_chunk(_messages_chunk(chunk))
        events += mapper.finalize()

        reasoning = [e for e in events if isinstance(e, ReasoningStatus)]
        # D12: 2 summary blocks joined by `\n` → segmenter sees `Summary one.\nSummary two.`
        # and emits two ReasoningStatus events (newline strips, terminator preserved)
        assert len(reasoning) == 2
        assert reasoning[0].text == "Summary one."
        assert reasoning[1].text == "Summary two."


class TestGeminiSoftEmit:
    """D26: Gemini CJK reasoning without 。 should soft-emit at 80-char threshold."""

    def test_gemini_cjk_no_terminator_soft_emit(self):
        # 110 CJK chars without any terminator (single contiguous reasoning chunk)
        long_cjk = "繁" * 110
        assert len(long_cjk) > ReasoningSegmenter.SOFT_EMIT_CHAR_THRESHOLD

        mapper = StreamEventMapper(session_id=SESSION_ID)
        events = mapper.process_chunk(
            _messages_chunk(
                AIMessageChunk(
                    content=[{"type": "reasoning", "reasoning": long_cjk}],
                    id="msg-gemini",
                )
            )
        )

        reasoning = [e for e in events if isinstance(e, ReasoningStatus)]
        # 80-char soft-emit fires once during feed(); the entire 110-char buffer
        # is yielded as a single soft-emitted segment.
        assert len(reasoning) == 1
        assert reasoning[0].text == long_cjk
