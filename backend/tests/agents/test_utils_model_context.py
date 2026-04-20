import pytest
from backend.agent_engine.utils import model_context
from backend.agent_engine.utils.model_context import (
    DEFAULT_CONTEXT_WINDOW,
    compute_section_soft_cap_chars,
    get_model_context_window,
)


@pytest.fixture(autouse=True)
def _reset_warned_models():
    model_context._WARNED_MODELS.clear()
    yield
    model_context._WARNED_MODELS.clear()


def test_get_model_context_window_registered(monkeypatch):
    monkeypatch.setattr(
        model_context,
        "_REGISTRY",
        {"gpt-4o-mini": {"max_input_tokens": 128000, "source": "litellm"}},
    )
    assert get_model_context_window("gpt-4o-mini") == 128000


def test_get_model_context_window_unknown_fallback_and_warn_once(monkeypatch, caplog):
    monkeypatch.setattr(model_context, "_REGISTRY", {})
    with caplog.at_level("WARNING", logger=model_context.logger.name):
        r1 = get_model_context_window("made-up-model-9000")
        r2 = get_model_context_window("made-up-model-9000")
        r3 = get_model_context_window("made-up-model-9000")
    assert r1 == r2 == r3 == DEFAULT_CONTEXT_WINDOW
    warnings = [rec for rec in caplog.records if "made-up-model-9000" in rec.getMessage()]
    assert len(warnings) == 1


@pytest.mark.parametrize(
    "ctx_tokens,expected_chars",
    [(128_000, 204_800), (200_000, 320_000), (131_072, 209_715)],
)
def test_compute_section_soft_cap_chars_formula(monkeypatch, ctx_tokens, expected_chars):
    monkeypatch.setattr(
        model_context,
        "_REGISTRY",
        {"fake-model": {"max_input_tokens": ctx_tokens, "source": "litellm"}},
    )
    assert compute_section_soft_cap_chars("fake-model") == expected_chars


def test_registry_yaml_matches_orchestrator_configs():
    """Sanity: committed YAML covers every model referenced in versions/*."""
    from pathlib import Path
    import yaml

    versions = Path("backend/agent_engine/agents/versions")
    needed = set()
    for cfg in versions.glob("*/orchestrator_config.yaml"):
        data = yaml.safe_load(cfg.read_text()) or {}
        name = (data.get("model") or {}).get("name")
        if isinstance(name, str):
            needed.add(name)
    registry = yaml.safe_load(
        Path("backend/agent_engine/utils/model_context_registry.yaml").read_text()
    ) or {}
    missing = needed - set(registry.keys())
    assert not missing, f"YAML missing entries for: {missing}"
