"""Dev-only SSE serializer flag tests.

FORCE_REASONING_NON_TRANSIENT removes the ``transient`` key from the
ReasoningStatus payload before the assert helper runs. In production
``APP_ENV=production`` the helper warns instead of raising, so the
malformed payload reaches the wire and exercises the frontend filter
that drops non-transient ``data-reasoning-status`` parts (S-chan-03).
"""

from __future__ import annotations

import json
import logging

import pytest

from backend.agent_engine.streaming.domain_events_schema import ReasoningStatus
from backend.agent_engine.streaming.sse_serializer import serialize_event


def _parse_sse(raw: str) -> dict:
    assert raw.startswith("data: ")
    return json.loads(raw.removeprefix("data: ").removesuffix("\n\n"))


class TestForceReasoningNonTransientDevFlag:
    def test_force_reasoning_non_transient_strips_flag_in_production(
        self, monkeypatch, caplog
    ):
        # Production-mode env so the assert helper logs a warning instead of
        # raising — this is the path Playwright actually exercises.
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("FORCE_REASONING_NON_TRANSIENT", "1")

        with caplog.at_level(
            logging.WARNING, logger="backend.agent_engine.streaming.sse_serializer"
        ):
            raw = serialize_event(ReasoningStatus(reasoning_id="r-0", text="x"))
        payload = _parse_sse(raw)
        assert "transient" not in payload
        assert any(
            "reasoning SSE event missing transient=True flag" in record.message
            for record in caplog.records
        )

    def test_force_reasoning_non_transient_raises_in_dev(self, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.setenv("FORCE_REASONING_NON_TRANSIENT", "1")
        # Dev/CI: assert helper raises so the regression is caught loudly.
        with pytest.raises(AssertionError, match="missing transient=True flag"):
            serialize_event(ReasoningStatus(reasoning_id="r-0", text="x"))

    def test_unset_keeps_transient_flag(self, monkeypatch):
        monkeypatch.delenv("FORCE_REASONING_NON_TRANSIENT", raising=False)
        raw = serialize_event(ReasoningStatus(reasoning_id="r-0", text="x"))
        payload = _parse_sse(raw)
        assert payload["transient"] is True
