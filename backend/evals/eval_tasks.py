"""Braintrust task functions wrapping the agent engine."""

from typing import Any

from backend.agent_engine.agents.base import Orchestrator, OrchestratorResult
from backend.agent_engine.agents.config_loader import VersionConfigLoader


def run_v1(input: Any) -> OrchestratorResult:
    """Braintrust task function: run v1_baseline agent and return OrchestratorResult."""
    config = VersionConfigLoader("v1_baseline").load()
    orchestrator = Orchestrator(config)
    prompt = input if isinstance(input, str) else input.get("prompt", str(input))
    return orchestrator.run(prompt)
