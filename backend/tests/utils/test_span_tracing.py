from unittest.mock import MagicMock

from backend.utils.span_tracing import traced_span


def test_no_outer_span_yields_noop(monkeypatch):
    fake_span = MagicMock()
    fake_span.get_span_context.return_value.is_valid = False
    monkeypatch.setattr(
        "backend.utils.span_tracing.otel_trace.get_current_span",
        lambda: fake_span,
    )
    fake_client = MagicMock()
    monkeypatch.setattr(
        "backend.utils.span_tracing.get_client",
        lambda: fake_client,
    )
    with traced_span("foo") as span:
        span.update(output={"x": 1})
        span.update_trace(metadata={})
    fake_client.start_as_current_observation.assert_not_called()


def test_outer_span_active_opens_observation(monkeypatch):
    fake_span = MagicMock()
    fake_span.get_span_context.return_value.is_valid = True
    monkeypatch.setattr(
        "backend.utils.span_tracing.otel_trace.get_current_span",
        lambda: fake_span,
    )
    fake_client = MagicMock()
    fake_observation = MagicMock()
    fake_client.start_as_current_observation.return_value.__enter__ = lambda self: fake_observation
    fake_client.start_as_current_observation.return_value.__exit__ = lambda self, *args: None
    monkeypatch.setattr(
        "backend.utils.span_tracing.get_client",
        lambda: fake_client,
    )
    with traced_span("yf_fetch"):
        pass
    fake_client.start_as_current_observation.assert_called_once_with(name="yf_fetch")
