"""Shared fixtures for evaluation tests."""

import pytest


@pytest.fixture(autouse=True)
def _reset_braintrust_global_handler():
    """Clear any Braintrust global handler set by eval-runner imports (S-obs-09).

    See `backend/tests/conftest.py` for rationale. Duplicated here because
    eval-path tests live outside `backend/tests/` and pytest only loads a
    `conftest.py` along the discovered test file's directory chain.
    """
    _clear_if_available()
    yield
    _clear_if_available()


def _clear_if_available() -> None:
    try:
        from braintrust.integrations.langchain.context import clear_global_handler
    except ImportError:
        return
    clear_global_handler()
