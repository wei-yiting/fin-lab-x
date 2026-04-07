"""Shared fixtures for evaluation tests."""

import pytest

from langgraph.checkpoint.sqlite import SqliteSaver

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import VersionConfigLoader


@pytest.fixture(scope="module")
def orchestrator():
    """Real Orchestrator with actual LLM — used for eval tests only."""
    config = VersionConfigLoader("v1_baseline").load()
    with SqliteSaver.from_conn_string(":memory:") as checkpointer:
        yield Orchestrator(config, checkpointer=checkpointer)
