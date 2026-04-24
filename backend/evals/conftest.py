"""Shared fixtures for evaluation tests."""

import pytest

from langgraph.checkpoint.sqlite import SqliteSaver

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import VersionConfigLoader


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
        from braintrust_langchain.context import clear_global_handler
    except ImportError:
        return
    clear_global_handler()


@pytest.fixture(scope="module")
def orchestrator():
    """Real Orchestrator with actual LLM — used for eval tests only."""
    config = VersionConfigLoader("v1_baseline").load()
    with SqliteSaver.from_conn_string(":memory:") as checkpointer:
        yield Orchestrator(config, checkpointer=checkpointer)
