"""Langfuse span helper that only emits when an outer trace is active.

`search()` is the single trace entry point for the SEC dense pipeline. When
`search()` is running, OpenTelemetry has a valid current span (created by
`@observe`), and calls to `traced_span(...)` inside any helper nest correctly
as children.

Outside `search()` — batch CLI ingest, unit tests that exercise helpers
directly, agent layers that have not opened their own span — there is no
valid current span, so `traced_span(...)` yields a no-op object and emits
nothing. This keeps batch and test runs off the Langfuse UI by construction,
without per-entry-point env-var toggling.
"""

from contextlib import contextmanager
from typing import Any

from langfuse import get_client
from opentelemetry import trace as otel_trace


class _NoOpSpan:
    """Drop-in span object for the untraced path — `.update()` is a no-op."""

    def update(self, **kwargs: Any) -> None:
        pass

    def update_trace(self, **kwargs: Any) -> None:
        pass


@contextmanager
def traced_span(name: str, **kwargs: Any):
    """Yield a Langfuse span if an outer trace is active, else a no-op."""
    current = otel_trace.get_current_span()
    if not current.get_span_context().is_valid:
        yield _NoOpSpan()
        return
    lf = get_client()
    with lf.start_as_current_observation(name=name, **kwargs) as span:
        yield span
