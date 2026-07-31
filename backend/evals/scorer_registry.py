"""Scorer registry helpers for evaluation scenarios."""

from __future__ import annotations

import importlib
import logging
import os
import re
from collections.abc import Callable
from typing import Any

from autoevals import LLMClassifier  # pyright: ignore[reportMissingImports]
from openai import OpenAI

from backend.evals.eval_spec_schema import ScorerConfig

logger = logging.getLogger(__name__)

# LLM-judge calls go straight to OpenAI, deliberately bypassing the Braintrust
# gateway and any OPENAI_BASE_URL override — see ADR-0007 before changing this.
_JUDGE_BASE_URL = "https://api.openai.com/v1"

_TEMPLATE_VAR_RE = re.compile(r"\{\{(expected\.\w+|input)\}\}")


def resolve_function(dotpath: str, *, label: str = "scorer") -> Callable[..., Any]:
    """Import and return a callable from a Python dotpath."""
    module_path, separator, attr_name = dotpath.rpartition(".")
    if not separator:
        raise ImportError(f"Invalid {label} dotpath: {dotpath}")

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise ImportError(
            f"Could not import {label} module '{module_path}' from '{dotpath}'"
        ) from exc

    try:
        func = getattr(module, attr_name)
    except AttributeError as exc:
        raise ImportError(
            f"Could not find {label} function '{attr_name}' in '{dotpath}'"
        ) from exc

    if not callable(func):
        raise ImportError(f"{label.capitalize()} target is not callable: {dotpath}")

    return func


def _build_judge_client() -> OpenAI:
    """Build the OpenAI client injected into every LLM-judge scorer."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. The eval LLM-judge client calls "
            f"{_JUDGE_BASE_URL} directly; set OPENAI_API_KEY to run "
            "llm_judge scorers."
        )
    return OpenAI(api_key=api_key, base_url=_JUDGE_BASE_URL)


def _build_llm_judge(scorer_config: ScorerConfig) -> Callable[..., Any]:
    """Construct an autoevals LLM classifier from scenario config.

    Returns a wrapper that checks rubric template variables before calling
    the classifier.  If any ``{{expected.X}}`` variable resolves to None or
    empty string, the row is skipped with a warning instead of sending a
    meaningless rubric to the LLM.
    """
    if scorer_config.rubric is None:
        raise ValueError("llm_judge ScorerConfig must include rubric")

    choice_scores = scorer_config.choice_scores or {"Y": 1.0, "N": 0.0}

    classifier = LLMClassifier(
        name=scorer_config.name,
        prompt_template=scorer_config.rubric,
        choice_scores=choice_scores,
        use_cot=scorer_config.use_cot,
        model=scorer_config.model,
        temperature=scorer_config.temperature,
        client=_build_judge_client(),
    )

    template_vars = _TEMPLATE_VAR_RE.findall(scorer_config.rubric)

    def _llm_judge_wrapper(
        output: Any, expected: Any, *, input: Any = None, **kwargs: Any
    ) -> Any:
        """Skip scoring when rubric template variables are missing or empty."""
        for var in template_vars:
            if var == "input":
                if input is None or input == "":
                    logger.warning(
                        "Scorer '%s' skipped: rubric variable {{input}} is empty",
                        scorer_config.name,
                    )
                    return None
            elif var.startswith("expected."):
                field = var.split(".", 1)[1]
                val = expected.get(field) if isinstance(expected, dict) else None
                if val is None or val == "":
                    logger.warning(
                        "Scorer '%s' skipped: rubric variable {{%s}} is empty",
                        scorer_config.name,
                        var,
                    )
                    return None
        return classifier(output=output, expected=expected, input=input, **kwargs)

    _llm_judge_wrapper.__name__ = scorer_config.name
    return _llm_judge_wrapper


def resolve_scorers(scorer_configs: list[ScorerConfig]) -> list[Callable[..., Any]]:
    """Convert scorer configs into callable scorers."""
    resolved_scorers: list[Callable[..., Any]] = []

    for scorer_config in scorer_configs:
        if scorer_config.function is not None:
            resolved_scorers.append(resolve_function(scorer_config.function))
            continue

        if scorer_config.type == "llm_judge":
            resolved_scorers.append(_build_llm_judge(scorer_config))
            continue

        raise ValueError(f"Unsupported scorer config: {scorer_config.name}")

    return resolved_scorers
