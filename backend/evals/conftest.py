"""Shared fixtures for evaluation tests."""

import pytest

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import VersionConfigLoader


@pytest.fixture(scope="module")
def orchestrator():
    """Real Orchestrator with actual LLM — used for eval tests only."""
    config = VersionConfigLoader("v1_baseline").load()
    return Orchestrator(config)
