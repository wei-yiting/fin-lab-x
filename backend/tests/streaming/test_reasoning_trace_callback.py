"""Tests for ReasoningTraceCallback (D4 / D29 Langfuse persistence).

Covers:
- D29 schema 5 cases (S-trace-02): reasoning text non-empty, empty, off, unsupported, > 500_000 bytes truncate.
- Defensive: empty generations, internal exception fallback.
- Always-write-key contract: metadata["reasoning"] is written exactly once for every
  (capability, response shape) combination on the completed path (D29 / C5.2).
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from backend.agent_engine.streaming import reasoning_trace_callback as rtc_module
from backend.agent_engine.streaming.reasoning_trace_callback import ReasoningTraceCallback


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _llm_result(message: AIMessage | None) -> LLMResult:
    """Wrap an AIMessage in an LLMResult, mirroring LangChain ChatGeneration shape."""
    if message is None:
        return LLMResult(generations=[])
    return LLMResult(generations=[[ChatGeneration(message=message)]])


def _llm_result_empty_inner() -> LLMResult:
    """Empty inner generation list (e.g. [[]])."""
    return LLMResult(generations=[[]])


def _install_mock_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace get_client in the callback module with a MagicMock returning a fake client."""
    fake_client = MagicMock()
    monkeypatch.setattr(rtc_module, "get_client", lambda: fake_client)
    return fake_client


def _invoke(cb: ReasoningTraceCallback, response: LLMResult) -> None:
    cb.on_llm_end(response, run_id=uuid4(), parent_run_id=None)


def _written_metadata(client: MagicMock) -> dict[str, Any]:
    """Pull metadata kwargs out of update_current_generation call_args."""
    assert client.update_current_generation.call_count == 1
    return client.update_current_generation.call_args.kwargs["metadata"]


# ---------------------------------------------------------------------------
# D29 schema — 5 scenarios (S-trace-02)
# ---------------------------------------------------------------------------


class TestSchemaScenarios:
    def test_capability_on_with_reasoning_blocks_writes_joined_text(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = _install_mock_client(monkeypatch)
        msg = AIMessage(
            content=[
                {"type": "reasoning", "reasoning": "first thought"},
                {"type": "text", "text": "answer"},
                {"type": "reasoning", "reasoning": "second thought"},
            ]
        )
        cb = ReasoningTraceCallback(agent_reasoning_capability="on")

        _invoke(cb, _llm_result(msg))

        assert _written_metadata(client) == {"reasoning": "first thought\nsecond thought"}

    def test_capability_on_no_reasoning_blocks_writes_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = _install_mock_client(monkeypatch)
        msg = AIMessage(content=[{"type": "text", "text": "just an answer"}])
        cb = ReasoningTraceCallback(agent_reasoning_capability="on")

        _invoke(cb, _llm_result(msg))

        assert _written_metadata(client) == {"reasoning": ""}

    def test_capability_off_no_reasoning_blocks_writes_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = _install_mock_client(monkeypatch)
        msg = AIMessage(content=[{"type": "text", "text": "answer"}])
        cb = ReasoningTraceCallback(agent_reasoning_capability="off")

        _invoke(cb, _llm_result(msg))

        assert _written_metadata(client) == {"reasoning": ""}

    def test_capability_unsupported_writes_sentinel_regardless_of_content(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = _install_mock_client(monkeypatch)
        msg = AIMessage(
            content=[{"type": "reasoning", "reasoning": "should be ignored"}]
        )
        cb = ReasoningTraceCallback(agent_reasoning_capability="unsupported")

        _invoke(cb, _llm_result(msg))

        assert _written_metadata(client) == {"reasoning": "<unsupported>"}

    def test_truncation_ascii_over_size_cap(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = _install_mock_client(monkeypatch)
        # 500_001 bytes of ASCII reasoning.
        original_text = "a" * (ReasoningTraceCallback.SIZE_CAP_BYTES + 1)
        msg = AIMessage(content=[{"type": "reasoning", "reasoning": original_text}])
        cb = ReasoningTraceCallback(agent_reasoning_capability="on")

        _invoke(cb, _llm_result(msg))

        written = _written_metadata(client)["reasoning"]
        original_len = len(original_text.encode("utf-8"))
        assert written.startswith("a" * 100)  # leading body preserved
        assert written.endswith(f"... [truncated, original {original_len} bytes]")
        # Truncated body must come from the SIZE_CAP_BYTES byte slice.
        prefix = "a" * ReasoningTraceCallback.SIZE_CAP_BYTES
        assert written == f"{prefix}... [truncated, original {original_len} bytes]"

    def test_truncation_cjk_three_byte_chars_drops_partial_codepoint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = _install_mock_client(monkeypatch)
        # 中 is 3 bytes in UTF-8. SIZE_CAP_BYTES is 500_000 — divisible by 3? 500_000 % 3 = 2,
        # so cutting at byte 500_000 lands mid-codepoint and errors='ignore' should drop it.
        char = "中"
        # Need encoded len > 500_000. 166_667 chars * 3 = 500_001 bytes.
        original_text = char * 166_667
        msg = AIMessage(content=[{"type": "reasoning", "reasoning": original_text}])
        cb = ReasoningTraceCallback(agent_reasoning_capability="on")

        _invoke(cb, _llm_result(msg))

        written = _written_metadata(client)["reasoning"]
        original_len = len(original_text.encode("utf-8"))
        assert written.endswith(f"... [truncated, original {original_len} bytes]")
        # Body portion must be valid UTF-8 (errors='ignore' dropped any half codepoint).
        body = written[: -len(f"... [truncated, original {original_len} bytes]")]
        # Round-trip must succeed.
        assert body.encode("utf-8").decode("utf-8") == body
        # Body byte length must be <= cap.
        assert len(body.encode("utf-8")) <= ReasoningTraceCallback.SIZE_CAP_BYTES


# ---------------------------------------------------------------------------
# Malformed reasoning block values — `dict.get("reasoning", "")` returns the
# stored value when the key is present, so a present-but-None entry would slip
# through and crash str.join. The implementation must coerce non-string values
# to "" so the block contributes nothing instead of poisoning the whole join.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "block,expected_joined",
    [
        # Single block, value is None (key present).
        ([{"type": "reasoning", "reasoning": None}], ""),
        # Single block, value is a non-string scalar.
        ([{"type": "reasoning", "reasoning": 123}], ""),
        # Single block, "reasoning" key entirely missing.
        ([{"type": "reasoning"}], ""),
        # Mixed: malformed block must not poison the valid block — only the
        # valid block contributes; the malformed one becomes "" and the join
        # produces "\n<valid>" (leading \n from the empty contribution).
        (
            [
                {"type": "reasoning", "reasoning": None},
                {"type": "reasoning", "reasoning": "valid thought"},
            ],
            "\nvalid thought",
        ),
    ],
    ids=["none_value", "non_string_value", "missing_key", "mixed_with_valid"],
)
def test_malformed_reasoning_block_value_does_not_crash(
    monkeypatch: pytest.MonkeyPatch,
    block: list[dict[str, Any]],
    expected_joined: str,
) -> None:
    client = _install_mock_client(monkeypatch)
    msg = AIMessage(content=block)
    cb = ReasoningTraceCallback(agent_reasoning_capability="on")

    _invoke(cb, _llm_result(msg))

    assert _written_metadata(client) == {"reasoning": expected_joined}


# ---------------------------------------------------------------------------
# Defensive scenarios
# ---------------------------------------------------------------------------


class TestDefensive:
    def test_empty_generations_writes_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = _install_mock_client(monkeypatch)
        cb = ReasoningTraceCallback(agent_reasoning_capability="on")

        _invoke(cb, _llm_result(None))

        assert _written_metadata(client) == {"reasoning": ""}

    def test_internal_exception_caught_and_writes_empty_string(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        client = _install_mock_client(monkeypatch)
        cb = ReasoningTraceCallback(agent_reasoning_capability="on")

        def _boom(_response: LLMResult) -> str:
            raise RuntimeError("synthetic explode")

        monkeypatch.setattr(cb, "_compute_reasoning_value", _boom)

        with caplog.at_level(logging.ERROR, logger=rtc_module.__name__):
            _invoke(cb, _llm_result(AIMessage(content=[])))

        assert _written_metadata(client) == {"reasoning": ""}
        assert any(
            "ReasoningTraceCallback failed" in rec.message for rec in caplog.records
        ), "Expected exception log line containing 'ReasoningTraceCallback failed'"


# ---------------------------------------------------------------------------
# Always-write-key contract — D29 / C5.2 explicit guard
# ---------------------------------------------------------------------------


def _shape_empty_generations() -> LLMResult:
    return _llm_result(None)


def _shape_empty_inner() -> LLMResult:
    return _llm_result_empty_inner()


def _shape_all_text() -> LLMResult:
    return _llm_result(AIMessage(content=[{"type": "text", "text": "hi"}]))


def _shape_has_reasoning() -> LLMResult:
    return _llm_result(
        AIMessage(content=[{"type": "reasoning", "reasoning": "thinking"}])
    )


_RESPONSE_SHAPES: list[tuple[str, Any]] = [
    ("empty_generations", _shape_empty_generations),
    ("empty_inner_generations", _shape_empty_inner),
    ("all_text_content", _shape_all_text),
    ("has_reasoning", _shape_has_reasoning),
]

_CAPABILITIES = ["on", "off", "unsupported"]


@pytest.mark.parametrize("capability", _CAPABILITIES)
@pytest.mark.parametrize(
    "shape_name,shape_factory",
    _RESPONSE_SHAPES,
    ids=[name for name, _ in _RESPONSE_SHAPES],
)
def test_always_writes_reasoning_key_completed_path(
    monkeypatch: pytest.MonkeyPatch,
    capability: str,
    shape_name: str,
    shape_factory: Any,
) -> None:
    """D29 / C5.2: every (capability × response shape) writes metadata['reasoning'] exactly once."""
    client = _install_mock_client(monkeypatch)
    cb = ReasoningTraceCallback(agent_reasoning_capability=capability)  # type: ignore[arg-type]

    _invoke(cb, shape_factory())

    assert client.update_current_generation.call_count == 1, (
        f"capability={capability} shape={shape_name}: expected exactly 1 update call"
    )
    metadata = client.update_current_generation.call_args.kwargs["metadata"]
    assert "reasoning" in metadata, (
        f"capability={capability} shape={shape_name}: 'reasoning' key missing"
    )


@pytest.mark.parametrize("capability", _CAPABILITIES)
def test_always_writes_reasoning_key_when_internal_exception(
    monkeypatch: pytest.MonkeyPatch,
    capability: str,
) -> None:
    """The 4th shape: callback internally raises — must still write metadata['reasoning']."""
    client = _install_mock_client(monkeypatch)
    cb = ReasoningTraceCallback(agent_reasoning_capability=capability)  # type: ignore[arg-type]
    monkeypatch.setattr(
        cb,
        "_compute_reasoning_value",
        lambda _r: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )

    _invoke(cb, _shape_has_reasoning())

    assert client.update_current_generation.call_count == 1
    assert "reasoning" in client.update_current_generation.call_args.kwargs["metadata"]
