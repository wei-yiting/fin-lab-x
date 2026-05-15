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

When an outer span IS active but Langfuse itself is disabled (no API keys
configured — typical in unit-test environments), the helper falls back to
opening a plain OpenTelemetry child span via the global tracer so that any
``add_event`` calls made by the wrapped code still nest under the outer
span. The yielded object is the no-op ``_NoOpSpan`` in this branch, since
Langfuse-specific ``update``/``update_trace`` semantics do not apply.

Coupling: the disabled-Langfuse detection reads the private ``_otel_tracer``
attribute on the Langfuse client (verified for langfuse 4.5.x). If a future
release renames it, this branch silently stops firing — production paths
with real keys keep working, but unit-test span assertions regress visibly,
which acts as the canary.
"""

from contextlib import contextmanager
from typing import Any

from langfuse import get_client
from opentelemetry import trace as otel_trace
from opentelemetry.trace import NoOpTracer


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
    if isinstance(getattr(lf, "_otel_tracer", None), NoOpTracer):
        # Langfuse is initialized in disabled / no-op mode (no API keys, or
        # any other branch that wires ``_otel_tracer`` to ``NoOpTracer``).
        # Open a plain OTel child span via the global tracer so per-attempt
        # ``add_event`` calls from the caller still attach to a recording
        # span — without this, the langfuse NoOpTracer would swap the
        # current span out for a NonRecordingSpan and silently drop events.
        tracer = otel_trace.get_tracer(__name__)
        with tracer.start_as_current_span(name):
            yield _NoOpSpan()
        return
    with lf.start_as_current_observation(name=name, **kwargs) as span:
        yield span
