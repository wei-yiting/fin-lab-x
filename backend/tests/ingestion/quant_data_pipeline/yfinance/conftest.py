"""Shared fixtures for yfinance subsystem tests.

The parent ``conftest.py`` at ``backend/tests/ingestion/quant_data_pipeline/``
is auto-discovered by pytest, so its ``tmp_duckdb`` fixture is already
available here — no ``pytest_plugins`` re-registration needed (and adding it
collides with pytest's plugin registry).
"""

import pytest
from langfuse._client.resource_manager import LangfuseResourceManager
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from backend.ingestion.quant_data_pipeline.yfinance import yfinance_client


@pytest.fixture(autouse=True)
def _reset_pacing():
    """Reset module-level pacing counters around every test."""
    yfinance_client.reset_pacing_stats()
    yield
    yfinance_client.reset_pacing_stats()


@pytest.fixture
def otel_in_memory_exporter(monkeypatch):
    """Real OTel ``TracerProvider`` + ``InMemorySpanExporter`` for span-shape
    assertions.

    Swaps in a fresh provider on the global trace API for the duration of the
    test, yields the exporter (for ``get_finished_spans()`` introspection),
    and restores the original on teardown so other tests aren't polluted.

    The ``_TRACER_PROVIDER`` access is a private API but is the established
    way to swap providers per-test — the public ``set_tracer_provider()``
    refuses a second call once the provider has been set.

    Test isolation note: if a prior test (e.g. the API suite via
    ``backend.api.main``) loaded ``backend/.env`` and populated
    ``LANGFUSE_PUBLIC_KEY``/``LANGFUSE_SECRET_KEY``, the langfuse client
    singleton would otherwise route ``traced_span`` through its own
    ``TracerProvider`` and never touch the in-memory exporter. The fixture
    clears those env vars and the langfuse resource-manager singleton so
    ``get_client()`` produces a disabled client and ``traced_span`` falls
    back to opening plain OTel spans against our provider.
    """
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    saved_instances = dict(LangfuseResourceManager._instances)
    LangfuseResourceManager._instances.clear()

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    original_provider = otel_trace._TRACER_PROVIDER
    otel_trace._TRACER_PROVIDER = provider
    try:
        yield exporter
    finally:
        otel_trace._TRACER_PROVIDER = original_provider
        LangfuseResourceManager._instances.clear()
        LangfuseResourceManager._instances.update(saved_instances)
