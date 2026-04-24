"""Shared pytest fixtures for the backend test suite."""

import pytest


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
