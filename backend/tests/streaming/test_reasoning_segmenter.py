"""Tests for ReasoningSegmenter — sentence boundary splitting + 80-char CJK fallback."""


from backend.agent_engine.streaming.reasoning_segmenter import ReasoningSegmenter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _feed_all(seg: ReasoningSegmenter, delta: str) -> list[str]:
    return list(seg.feed(delta))


# ---------------------------------------------------------------------------
# Half-width terminator: `.` followed by whitespace
# ---------------------------------------------------------------------------

class TestHalfWidthDotSplit:
    def test_dot_space_splits_sentence(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "Hello. World")
        # "Hello." is emitted; " World" stays buffered
        assert result == ["Hello."]

    def test_numeric_dot_not_split(self):
        # "3.14" — digit before dot, no trailing whitespace split expected
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "3.14 is pi")
        assert result == []

    def test_exclamation_space_splits(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "Wow! Amazing")
        assert result == ["Wow!"]

    def test_question_space_splits(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "Really? Yes")
        assert result == ["Really?"]

    def test_multiple_sentences_in_one_feed(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "First. Second! Third? Tail")
        assert result == ["First.", "Second!", "Third?"]


# ---------------------------------------------------------------------------
# Full-width (CJK) terminators
# ---------------------------------------------------------------------------

class TestCJKTerminatorSplit:
    def test_cjk_period_splits_immediately(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "這是第一句。這是第二")
        assert result == ["這是第一句。"]

    def test_cjk_exclamation_splits(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "太棒了！繼續")
        assert result == ["太棒了！"]

    def test_cjk_question_splits(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "真的嗎？我不知道")
        assert result == ["真的嗎？"]

    def test_multiple_cjk_sentences(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "第一句。第二句！第三句？尾巴")
        assert result == ["第一句。", "第二句！", "第三句？"]


# ---------------------------------------------------------------------------
# Newline terminator — stripped from emitted sentence
# ---------------------------------------------------------------------------

class TestNewlineTerminator:
    def test_newline_splits_and_strips(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "Line one\nLine two")
        # \n is a layout artifact; emitted sentence has \n stripped
        assert result == ["Line one"]

    def test_trailing_newline_no_extra_empty_emit(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "Line one\n")
        assert result == ["Line one"]

    def test_crlf_strips_carriage_return(self):
        seg = ReasoningSegmenter()
        out = list(seg.feed("Line one\r\nLine two"))
        assert out == ["Line one"]
        assert seg.flush() == "Line two"


# ---------------------------------------------------------------------------
# Cross-feed half-width terminator behaviour
# ---------------------------------------------------------------------------

class TestHalfWidthAcrossFeeds:
    def test_halfwidth_dot_at_delta_end_buffers_until_next_whitespace(self):
        """Realistic LLM streaming pattern — punctuation lands at chunk boundary."""
        seg = ReasoningSegmenter()
        assert list(seg.feed("Hello.")) == []  # buffered, no whitespace yet
        out = list(seg.feed(" World"))
        assert out == ["Hello."]
        # leading space consumed by the regex (it's the captured \s)
        assert seg.flush() == "World"

    def test_multiple_halfwidth_terminators_last_buffers(self):
        seg = ReasoningSegmenter()
        out = list(seg.feed("A. B. C."))
        # "A." and "B." emit; "C." buffers because no trailing whitespace
        assert out == ["A.", "B."]
        assert seg.flush() == "C."


# ---------------------------------------------------------------------------
# No terminator — buffering behaviour
# ---------------------------------------------------------------------------

class TestNoTerminatorBuffering:
    def test_short_no_terminator_yields_nothing(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "Short text")
        assert result == []

    def test_empty_feed_yields_nothing(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "")
        assert result == []

    def test_content_accumulates_across_feeds(self):
        seg = ReasoningSegmenter()
        _feed_all(seg, "Hello")
        result = _feed_all(seg, " World")
        assert result == []
        # flush should return the accumulated buffer
        assert seg.flush() == "Hello World"


# ---------------------------------------------------------------------------
# 80-char soft-emit fallback (D26 / S-stream-09)
# ---------------------------------------------------------------------------

class TestSoftEmitFallback:
    def test_80_char_cjk_no_terminator_soft_emits(self):
        """Single feed of 85 CJK chars with no terminator triggers soft-emit."""
        seg = ReasoningSegmenter()
        delta = "甲" * 85  # 85 CJK chars, no terminator
        result = _feed_all(seg, delta)
        # entire buffer (85 chars) is emitted as one segment
        assert len(result) == 1
        assert result[0] == delta

    def test_soft_emit_resets_buffer_for_next_feed(self):
        """After soft-emit the next feed starts from an empty buffer."""
        seg = ReasoningSegmenter()
        _feed_all(seg, "甲" * 85)
        # subsequent short feed should buffer, not emit
        result = _feed_all(seg, "乙" * 5)
        assert result == []
        assert seg.flush() == "乙" * 5

    def test_exactly_80_chars_triggers_soft_emit(self):
        """Buffer at exactly SOFT_EMIT_CHAR_THRESHOLD without terminator triggers soft-emit."""
        seg = ReasoningSegmenter()
        delta = "a" * ReasoningSegmenter.SOFT_EMIT_CHAR_THRESHOLD
        result = _feed_all(seg, delta)
        assert len(result) == 1
        assert result[0] == delta

    def test_79_chars_no_emit(self):
        """One char below threshold does not trigger soft-emit."""
        seg = ReasoningSegmenter()
        delta = "a" * (ReasoningSegmenter.SOFT_EMIT_CHAR_THRESHOLD - 1)
        result = _feed_all(seg, delta)
        assert result == []

    def test_terminator_before_80_chars_wins(self):
        """If a terminator appears before 80 chars are reached, normal split fires."""
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "Short sentence. " + "a" * 30)
        # Only the terminated sentence emitted; remaining < 80, stays buffered
        assert result == ["Short sentence."]

    def test_soft_emit_then_terminator_in_next_feed(self):
        """Soft-emit clears buffer; terminator in the next feed splits normally."""
        seg = ReasoningSegmenter()
        _feed_all(seg, "甲" * 85)
        result = _feed_all(seg, "續集。後文")
        assert result == ["續集。"]


# ---------------------------------------------------------------------------
# flush() behaviour
# ---------------------------------------------------------------------------

class TestFlush:
    def test_flush_returns_remaining_buffer(self):
        seg = ReasoningSegmenter()
        _feed_all(seg, "Partial sentence")
        assert seg.flush() == "Partial sentence"

    def test_flush_clears_buffer(self):
        seg = ReasoningSegmenter()
        _feed_all(seg, "Something")
        seg.flush()
        assert seg.flush() is None

    def test_flush_on_empty_returns_none(self):
        seg = ReasoningSegmenter()
        assert seg.flush() is None

    def test_flush_idempotent_on_empty(self):
        """Repeated flush on already-empty buffer never raises."""
        seg = ReasoningSegmenter()
        assert seg.flush() is None
        assert seg.flush() is None


# ---------------------------------------------------------------------------
# reset() behaviour
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_clears_buffer(self):
        seg = ReasoningSegmenter()
        _feed_all(seg, "Some text")
        seg.reset()
        assert seg.flush() is None

    def test_reset_allows_fresh_start(self):
        seg = ReasoningSegmenter()
        _feed_all(seg, "Old text. Still here")
        seg.reset()
        result = _feed_all(seg, "New text")
        assert result == []
        assert seg.flush() == "New text"


# ---------------------------------------------------------------------------
# feed() is a lazy generator (not a list)
# ---------------------------------------------------------------------------

class TestFeedIsGenerator:
    def test_feed_returns_iterator(self):
        import types
        seg = ReasoningSegmenter()
        result = seg.feed("Hello. World")
        assert isinstance(result, types.GeneratorType)


# ---------------------------------------------------------------------------
# Mixed CJK + half-width in same feed
# ---------------------------------------------------------------------------

class TestMixedTerminators:
    def test_cjk_then_halfwidth(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "CJK結束。Half end. Tail")
        assert result == ["CJK結束。", "Half end."]

    def test_halfwidth_then_cjk(self):
        seg = ReasoningSegmenter()
        result = _feed_all(seg, "Half end. CJK結束。Tail")
        assert result == ["Half end.", "CJK結束。"]
