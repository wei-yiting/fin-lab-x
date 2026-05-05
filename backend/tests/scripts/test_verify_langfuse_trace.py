"""Unit tests for the Langfuse trace verifier CLI.

These tests cover argument parsing and Langfuse JSON parsing logic only —
no live Langfuse calls. The HTTP client is mocked via ``monkeypatch`` so
the CLI's polling/auth wiring exists but never reaches the network.

Trace JSON shape mirrors Langfuse 4.x ``GET /api/public/traces/{id}``:
``{id, name, metadata, observations: [{id, type, name, metadata,
parentObservationId, startTime}]}``.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from backend.scripts.validation import verify_langfuse_trace as vlt


def _gen(
    obs_id: str,
    *,
    reasoning: str | None = None,
    reasoning_tail_aborted: str | None = None,
    parent: str | None = "root",
    start: str = "2026-05-05T00:00:00Z",
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a fake GENERATION observation. Only includes ``metadata.reasoning``
    when explicitly passed (None means "key absent")."""
    metadata: dict[str, Any] = dict(extra_metadata or {})
    if reasoning is not None:
        metadata["reasoning"] = reasoning
    if reasoning_tail_aborted is not None:
        metadata["reasoning_tail_aborted"] = reasoning_tail_aborted
    return {
        "id": obs_id,
        "type": "GENERATION",
        "name": "chat_model",
        "metadata": metadata,
        "parentObservationId": parent,
        "startTime": start,
    }


def _root_span(*, status: str | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if status is not None:
        metadata["status"] = status
    return {
        "id": "root",
        "type": "SPAN",
        "name": "chat-turn",
        "metadata": metadata,
        "parentObservationId": None,
        "startTime": "2026-05-05T00:00:00Z",
    }


def _trace(observations: list[dict[str, Any]], trace_metadata: dict | None = None) -> dict[str, Any]:
    return {
        "id": "trace-abc",
        "name": "v3_quant_stream",
        "metadata": trace_metadata or {},
        "observations": observations,
    }


def _install_fake_fetch(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> None:
    """Replace the module's network call with a function that returns ``payload``."""

    def _fake(trace_id: str, *, base_url: str, public_key: str, secret_key: str) -> dict[str, Any]:
        return payload

    monkeypatch.setattr(vlt, "fetch_trace", _fake)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")


def test_expect_reasoning_on_passes_when_all_generations_have_nonempty_reasoning(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_fake_fetch(
        monkeypatch,
        _trace([_root_span(), _gen("g1", reasoning="step 1\nstep 2")]),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["expectation"] == "reasoning-on"


def test_expect_reasoning_on_fails_when_generation_has_empty_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(
        monkeypatch,
        _trace([_root_span(), _gen("g1", reasoning="")]),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0


def test_expect_reasoning_on_fails_when_metadata_reasoning_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(
        monkeypatch,
        _trace([_root_span(), _gen("g1", reasoning=None)]),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0


def test_expect_reasoning_off_passes_when_all_generations_have_empty_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(
        monkeypatch,
        _trace([_root_span(), _gen("g1", reasoning=""), _gen("g2", reasoning="")]),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-off"])

    assert code == 0


def test_expect_reasoning_off_fails_when_any_generation_has_nonempty_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(
        monkeypatch,
        _trace([_root_span(), _gen("g1", reasoning=""), _gen("g2", reasoning="leaked")]),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-off"])

    assert code != 0


def test_expect_unsupported_passes_when_all_generations_have_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(
        monkeypatch,
        _trace([_root_span(), _gen("g1", reasoning="<unsupported>")]),
    )

    code = vlt.main(["trace-abc", "--expect-unsupported"])

    assert code == 0


def test_expect_unsupported_fails_when_generation_has_real_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(
        monkeypatch,
        _trace([_root_span(), _gen("g1", reasoning="actual reasoning")]),
    )

    code = vlt.main(["trace-abc", "--expect-unsupported"])

    assert code != 0


def test_expect_aborted_passes_when_root_span_status_aborted_and_tail_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Root chat-turn span has status=aborted; latest GENERATION carries the
    segmenter tail under ``reasoning_tail_aborted``."""
    _install_fake_fetch(
        monkeypatch,
        _trace(
            [
                _root_span(status="aborted"),
                _gen("g1", reasoning="thought 1", start="2026-05-05T00:00:01Z"),
                _gen(
                    "g2",
                    reasoning="thought 2 partial",
                    reasoning_tail_aborted="tail segment",
                    start="2026-05-05T00:00:02Z",
                ),
            ]
        ),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on", "--expect-aborted"])

    assert code == 0


def test_expect_aborted_fails_when_root_span_missing_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_fetch(
        monkeypatch,
        _trace(
            [
                _root_span(status=None),
                _gen(
                    "g1",
                    reasoning="thought 1",
                    reasoning_tail_aborted="tail",
                ),
            ]
        ),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on", "--expect-aborted"])

    assert code != 0


def test_expect_aborted_accepts_empty_tail_when_segmenter_buffer_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per design: a missing/empty reasoning_tail_aborted is acceptable when
    the segmenter buffer was empty at abort. Status check is the hard gate."""
    _install_fake_fetch(
        monkeypatch,
        _trace(
            [
                _root_span(status="aborted"),
                _gen("g1", reasoning="thought 1"),
            ]
        ),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on", "--expect-aborted"])

    assert code == 0


def test_mutually_exclusive_expectations_rejected() -> None:
    with pytest.raises(SystemExit):
        vlt.main(["trace-abc", "--expect-reasoning-on", "--expect-reasoning-off"])


def test_missing_expectation_rejected() -> None:
    with pytest.raises(SystemExit):
        vlt.main(["trace-abc"])


def test_no_generation_observations_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """A trace with only the root span and no chat_model children means the
    agent never invoked an LLM — that's a verification failure regardless of
    expectation."""
    _install_fake_fetch(monkeypatch, _trace([_root_span()]))

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0


def test_root_span_missing_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a root agent.run / chat-turn span, trace topology is invalid."""
    _install_fake_fetch(
        monkeypatch,
        _trace([_gen("g1", reasoning="x", parent=None)]),
    )

    code = vlt.main(["trace-abc", "--expect-reasoning-on"])

    assert code != 0
