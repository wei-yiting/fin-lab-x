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
    if _REGISTRY_PATH.exists():
        raw = yaml.safe_load(_REGISTRY_PATH.read_text()) or {}
        _REGISTRY = {k: v for k, v in raw.items() if isinstance(v, dict)}


_load_registry()


def get_model_context_window(model_name: str) -> int:
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
    ctx = get_model_context_window(model_name)
    return int(ctx * fraction * _SOFT_CAP_CHARS_PER_TOKEN)
