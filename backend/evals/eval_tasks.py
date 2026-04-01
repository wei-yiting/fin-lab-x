"""Braintrust task functions wrapping the agent engine."""

from __future__ import annotations

import functools
from collections.abc import Mapping
from typing import Any

from backend.agent_engine.agents.base import Orchestrator, OrchestratorResult
from backend.agent_engine.agents.config_loader import VersionConfigLoader


@functools.lru_cache(maxsize=4)
def _get_orchestrator(version: str) -> Orchestrator:
    """Return a cached Orchestrator for the given version to avoid repeated init."""
    config = VersionConfigLoader(version).load()
    return Orchestrator(config)


def run_v1(input: Any) -> OrchestratorResult:
    """Braintrust task function: run v1_baseline agent and return OrchestratorResult."""
    orchestrator = _get_orchestrator("v1_baseline")
    if isinstance(input, str):
        prompt = input
    elif isinstance(input, Mapping):
        prompt = input.get("prompt", str(input))
    else:
        prompt = str(input)
    return orchestrator.run(prompt)
