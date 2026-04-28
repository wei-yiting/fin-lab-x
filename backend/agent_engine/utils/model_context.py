import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONTEXT_WINDOW = 128_000
_SOFT_CAP_CHARS_PER_TOKEN = 4
_REGISTRY_PATH = Path(__file__).with_name("model_context_registry.yaml")
_REGISTRY: dict[str, dict] = {}
_WARNED_MODELS: set[str] = set()


def _load_registry() -> None:
    global _REGISTRY
    if not _REGISTRY_PATH.exists():
        return
    raw = yaml.safe_load(_REGISTRY_PATH.read_text())
    if not isinstance(raw, dict):
        logger.warning(
            "model_context_registry.yaml did not parse to a mapping; "
            "falling back to empty registry."
        )
        return
    _REGISTRY = {k: v for k, v in raw.items() if isinstance(v, dict)}


_load_registry()


def get_model_context_window(model_name: str) -> int:
    """Return max input tokens for ``model_name``; falls back to
    ``DEFAULT_CONTEXT_WINDOW`` with a warn-once log on miss."""
    entry = _REGISTRY.get(model_name)
    if entry and "max_input_tokens" in entry:
        return int(entry["max_input_tokens"])
    if model_name not in _WARNED_MODELS:
        _WARNED_MODELS.add(model_name)
        logger.warning(
            "Model %r not in model_context_registry.yaml; falling back to default "
            "%d tokens. Run backend/scripts/refresh_model_context_registry.py to "
            "materialize.",
            model_name,
            DEFAULT_CONTEXT_WINDOW,
        )
    return DEFAULT_CONTEXT_WINDOW


def compute_section_soft_cap_chars(model_name: str, fraction: float = 0.4) -> int:
    """Compute a soft char-count cap for an SEC section worth inlining.

    Returns ``int(ctx_tokens * fraction * 4)`` using the 4-chars-per-token
    heuristic. Caller picks ``fraction`` (default 0.4 = 40% of context).

    Args:
        model_name: registered model (see model_context_registry.yaml).
        fraction: strictly positive, at most 1.0.
    """
    if not 0 < fraction <= 1:
        raise ValueError(
            f"fraction must be in (0, 1], got {fraction}"
        )
    ctx = get_model_context_window(model_name)
    return int(ctx * fraction * _SOFT_CAP_CHARS_PER_TOKEN)
