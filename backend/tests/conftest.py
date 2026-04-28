"""Shared pytest fixtures for the backend test suite."""

import os

import pytest


@pytest.fixture(autouse=True)
def _edgar_identity_placeholder(monkeypatch):
    """Provide a synthetic ``EDGAR_IDENTITY`` for tests that don't set one.

    ``Orchestrator.__init__`` fast-fails when a version config loads any SEC
    tool without ``EDGAR_IDENTITY`` set. Most unit/integration tests fully
    mock the underlying edgartools, so the value is meaningless to them —
    but the startup check still fires. CI doesn't export the variable, so
    every Orchestrator-constructing test would crash there.

    Use ``setdefault`` semantics: never override an already-populated env
    (so ``sec_integration`` tests keep hitting real EDGAR with the
    developer's identity), and any test that explicitly ``monkeypatch.delenv``
    or ``monkeypatch.setenv`` keeps full control within its own scope.
    """
    if not os.environ.get("EDGAR_IDENTITY"):
        monkeypatch.setenv("EDGAR_IDENTITY", "Test Reporter test@example.com")


@pytest.fixture(autouse=True)
def _reset_braintrust_global_handler():
    """Ensure no Braintrust global handler leaks between tests (S-obs-09).

    `set_global_handler()` stores the handler in a process-wide `ContextVar`
    that survives across tests. If a test (directly or transitively via
    imports of `backend.evals.eval_runner`) registers one, subsequent tests
    share it — causing cross-attributed trace events and hard-to-debug
    coupling.

    The fixture is a no-op when `braintrust_langchain` is not installed
    (e.g. a minimal test env without the `[dev]` extras).
    """
    _clear_if_available()
    yield
    _clear_if_available()


def _clear_if_available() -> None:
    try:
        from braintrust_langchain.context import clear_global_handler
    except ImportError:
        return
    clear_global_handler()
