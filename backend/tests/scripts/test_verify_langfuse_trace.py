"""Unit tests for the Langfuse trace verifier CLI (F7 / ADR-0007 shape).

These tests cover argument parsing and Langfuse JSON parsing logic only —
no live Langfuse calls. The SDK fetch is mocked via ``monkeypatch`` so the
CLI's polling wiring exists but never reaches the network.

Trace dict shape mirrors the SDK's ``api.trace.get(...).dict()`` output
(camelCase keys, matching the public API JSON): ``{id, name, metadata,
observations: [{id, type, name, metadata, parentObservationId,
startTime}]}``. The transcript lives on the root ``chat_turn`` span's
``metadata.reasoning``.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from backend.scripts.validation import verify_langfuse_trace as vlt


def _root_span(
    *,
    reasoning: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Build the Orchestrator-owned root span. Only includes
    ``metadata.reasoning`` when explicitly passed (None means "key absent")."""
    metadata: dict[str, Any] = {}
    if reasoning is not None:
        metadata["reasoning"] = reasoning
    if status is not None:
        metadata["status"] = status
    return {
        "id": "root",
        "type": "SPAN",
        "name": "chat_turn",
        "metadata": metadata,
        "parentObservationId": None,
        "startTime": "2026-05-05T00:00:00Z",
    }


def _trace(observations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": "trace-abc",
        "name": "quant_stream",
        "metadata": {},
        "observations": observations,
    }


def _install_fake_fetch(
    monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]
) -> None:
    """Replace the module's SDK fetch with a function that returns ``payload``."""

    def _fake(trace_id: str) -> dict[str, Any]:
        return payload

    monkeypatch.setattr(vlt, "fetch_trace", _fake)


TRANSCRIPT = "=== segment 1 ===\nstep 1\nstep 2\n=== segment 2 ===\nstep 3"


def test_expect_reasoning_on_passes_with_marked_transcript(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_fake_fetch(monkeypatch, _trace([_root_span(reasoning=TRANSCRIPT)]))

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["expectation"] == "reasoning-on"


def test_expect_reasoning_on_fails_when_transcript_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(monkeypatch, _trace([_root_span(reasoning="")]))

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0


def test_expect_reasoning_on_fails_with_unsupported_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(monkeypatch, _trace([_root_span(reasoning="<unsupported>")]))

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0


def test_expect_reasoning_on_fails_when_no_segment_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-empty text without segment markers means the transcript shape
    regressed (e.g. raw join without the per-segment headers)."""
    _install_fake_fetch(
        monkeypatch, _trace([_root_span(reasoning="bare text, no markers")])
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0


def test_expect_reasoning_on_fails_with_marker_only_transcript(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A transcript that is only a segment header with no reasoning text
    (zero-delta reasoning block) must not pass as a real transcript."""
    _install_fake_fetch(
        monkeypatch, _trace([_root_span(reasoning="=== segment 1 ===\n")])
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0


def test_expect_reasoning_on_fails_when_metadata_reasoning_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Always-write-key contract: the root span must carry the reasoning key."""
    _install_fake_fetch(monkeypatch, _trace([_root_span(reasoning=None)]))

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0


def test_expect_aborted_passes_with_tail_marker_and_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    aborted_transcript = "=== segment 1 ===\npartial tail\n=== aborted ==="
    _install_fake_fetch(
        monkeypatch,
        _trace([_root_span(reasoning=aborted_transcript, status="aborted")]),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on", "--expect-aborted"])

    assert code == 0


def test_expect_aborted_fails_when_root_span_missing_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    aborted_transcript = "=== segment 1 ===\npartial tail\n=== aborted ==="
    _install_fake_fetch(monkeypatch, _trace([_root_span(reasoning=aborted_transcript)]))

    code = vlt.main(["trace-abc", "--expect-reasoning-on", "--expect-aborted"])

    assert code != 0


def test_expect_aborted_fails_when_transcript_lacks_aborted_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(
        monkeypatch,
        _trace([_root_span(reasoning=TRANSCRIPT, status="aborted")]),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on", "--expect-aborted"])

    assert code != 0


def test_missing_expectation_rejected() -> None:
    with pytest.raises(SystemExit):
        vlt.main(["trace-abc"])


def test_root_span_missing_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a root chat_turn span, trace topology is invalid."""
    parentless_generation = {
        "id": "g1",
        "type": "GENERATION",
        "name": "chat_model",
        "metadata": {"reasoning": "x"},
        "parentObservationId": None,
        "startTime": "2026-05-05T00:00:00Z",
    }
    _install_fake_fetch(monkeypatch, _trace([parentless_generation]))

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0
