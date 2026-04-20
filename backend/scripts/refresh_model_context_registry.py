"""Refresh backend/agent_engine/utils/model_context_registry.yaml using litellm.

Dev-only — requires `litellm` from [project.optional-dependencies].dev.
Reads all backend/agent_engine/agents/versions/*/orchestrator_config.yaml to
collect unique model names. For each name, calls litellm.get_model_info().
Missing/erroring entries preserve any existing `manual` source row; unknown
models log a warning and are skipped (must be filled in manually).

Run with: uv run --extra dev python backend/scripts/refresh_model_context_registry.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VERSIONS_DIR = _REPO_ROOT / "backend" / "agent_engine" / "agents" / "versions"
_REGISTRY_PATH = (
    _REPO_ROOT
    / "backend"
    / "agent_engine"
    / "utils"
    / "model_context_registry.yaml"
)


def _collect_model_names() -> list[str]:
    names: set[str] = set()
    for cfg in sorted(_VERSIONS_DIR.glob("*/orchestrator_config.yaml")):
        data = yaml.safe_load(cfg.read_text()) or {}
        model = (data.get("model") or {}).get("name")
        if isinstance(model, str) and model:
            names.add(model)
    return sorted(names)


def _load_existing_registry() -> dict[str, dict[str, Any]]:
    if _REGISTRY_PATH.exists():
        raw = yaml.safe_load(_REGISTRY_PATH.read_text()) or {}
        return {k: v for k, v in raw.items() if isinstance(v, dict)}
    return {}


def _refresh(names: list[str], existing: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    import litellm  # dev-only; not imported at top level

    out: dict[str, dict[str, Any]] = dict(existing)
    for name in names:
        try:
            info = litellm.get_model_info(name)
            max_input = info.get("max_input_tokens")
            if max_input is None:
                raise ValueError("litellm returned no max_input_tokens")
            out[name] = {"max_input_tokens": int(max_input), "source": "litellm"}
        except Exception as exc:
            if name in existing:
                logger.warning("litellm miss for %r (%s); preserving existing entry.", name, exc)
            else:
                logger.warning(
                    "litellm miss for %r (%s); skip. Add manually as "
                    "{max_input_tokens: <int>, source: manual}.",
                    name,
                    exc,
                )
    return out


def main() -> int:
    names = _collect_model_names()
    if not names:
        logger.error("No model names found under %s", _VERSIONS_DIR)
        return 1
    logger.info("Discovered models: %s", ", ".join(names))
    existing = _load_existing_registry()
    updated = _refresh(names, existing)
    sorted_by_key = {k: updated[k] for k in sorted(updated)}
    _REGISTRY_PATH.write_text(yaml.safe_dump(sorted_by_key, sort_keys=False))
    logger.info("Wrote %d entries to %s", len(sorted_by_key), _REGISTRY_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
