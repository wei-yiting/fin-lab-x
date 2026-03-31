"""Scorer registry helpers for evaluation scenarios."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from autoevals import LLMClassifier

from backend.evals.scenario_config import ScorerConfig


def _resolve_function(dotpath: str) -> Callable[..., Any]:
    """Import and return a callable from a Python dotpath."""
    module_path, separator, attr_name = dotpath.rpartition(".")
    if not separator:
        raise ImportError(f"Invalid scorer dotpath: {dotpath}")

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise ImportError(
            f"Could not import scorer module '{module_path}' from '{dotpath}'"
        ) from exc

    try:
        scorer = getattr(module, attr_name)
    except AttributeError as exc:
        raise ImportError(
            f"Could not find scorer function '{attr_name}' in '{dotpath}'"
        ) from exc

    if not callable(scorer):
        raise ImportError(f"Scorer target is not callable: {dotpath}")

    return scorer


def _build_llm_judge(scorer_config: ScorerConfig) -> LLMClassifier:
    """Construct an autoevals LLM classifier from scenario config."""
    if scorer_config.rubric is None:
        raise ValueError("llm_judge ScorerConfig must include rubric")

    choice_scores = scorer_config.choice_scores or {"Y": 1.0, "N": 0.0}

    return LLMClassifier(
        name=scorer_config.name,
        prompt_template=scorer_config.rubric,
        choice_scores=choice_scores,
        use_cot=scorer_config.use_cot,
        model=scorer_config.model,
    )


def resolve_scorers(scorer_configs: list[ScorerConfig]) -> list[Callable[..., Any]]:
    """Convert scorer configs into callable scorers."""
    resolved_scorers: list[Callable[..., Any]] = []

    for scorer_config in scorer_configs:
        if scorer_config.function is not None:
            resolved_scorers.append(_resolve_function(scorer_config.function))
            continue

        if scorer_config.type == "llm_judge":
            resolved_scorers.append(_build_llm_judge(scorer_config))
            continue

        raise ValueError(f"Unsupported scorer config: {scorer_config.name}")

    return resolved_scorers
