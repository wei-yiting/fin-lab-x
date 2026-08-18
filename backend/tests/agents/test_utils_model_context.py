from pathlib import Path

import pytest
import yaml

from backend.agent_engine.agents.config_loader import ModelConfig
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
    warnings = [
        rec for rec in caplog.records if "made-up-model-9000" in rec.getMessage()
    ]
    assert len(warnings) == 1


@pytest.mark.parametrize(
    "ctx_tokens,expected_chars",
    [(128_000, 204_800), (200_000, 320_000), (131_072, 209_715)],
)
def test_compute_section_soft_cap_chars_formula(
    monkeypatch, ctx_tokens, expected_chars
):
    monkeypatch.setattr(
        model_context,
        "_REGISTRY",
        {"fake-model": {"max_input_tokens": ctx_tokens, "source": "litellm"}},
    )
    assert compute_section_soft_cap_chars("fake-model") == expected_chars


@pytest.mark.parametrize("bad_fraction", [0, -0.1, 1.1, 2.0])
def test_compute_section_soft_cap_chars_rejects_invalid_fraction(
    monkeypatch, bad_fraction
):
    monkeypatch.setattr(
        model_context,
        "_REGISTRY",
        {"fake-model": {"max_input_tokens": 128_000, "source": "litellm"}},
    )
    with pytest.raises(ValueError):
        compute_section_soft_cap_chars("fake-model", fraction=bad_fraction)


def test_load_registry_handles_non_dict_yaml(tmp_path, monkeypatch, caplog):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("- just a list\n- not a mapping\n")
    monkeypatch.setattr(model_context, "_REGISTRY_PATH", bad_yaml)
    monkeypatch.setattr(model_context, "_REGISTRY", {})
    with caplog.at_level("WARNING", logger=model_context.logger.name):
        model_context._load_registry()
    # Registry stays empty, no crash
    assert model_context._REGISTRY == {}
    assert any(
        "did not parse to a mapping" in rec.getMessage() for rec in caplog.records
    )


def test_registry_yaml_matches_orchestrator_configs():
    """Sanity: committed YAML covers every model referenced in profiles/*.

    Registry keys must be BARE model names — the runtime lookup receives
    ``ModelConfig.bare_name`` and does no stripping of its own, so a
    prefixed registry key would never be hit. Uses ``ModelConfig`` for the
    parsing rather than re-splitting the string (single parsing owner).
    """
    profiles = Path("backend/agent_engine/agents/profiles")
    needed = set()
    for cfg in profiles.glob("*/orchestrator_config.yaml"):
        data = yaml.safe_load(cfg.read_text()) or {}
        name = (data.get("model") or {}).get("name")
        if isinstance(name, str):
            needed.add(ModelConfig(name=name).bare_name)
    registry = (
        yaml.safe_load(
            Path("backend/agent_engine/utils/model_context_registry.yaml").read_text()
        )
        or {}
    )
    registry_keys = set(registry.keys())
    missing = sorted(needed - registry_keys)
    assert not missing, f"YAML missing bare-name entries for: {missing}"


def test_lookup_expects_bare_names_from_config_boundary(monkeypatch):
    """Registry lookup takes bare names only — callers holding a
    ``provider:model`` identifier pass ``ModelConfig.bare_name``. The old
    in-lookup prefix-stripping fallback was removed when parsing moved to
    the single ModelConfig owner; a prefixed name is now simply a miss."""
    monkeypatch.setattr(
        model_context,
        "_REGISTRY",
        {
            "gemini-2.5-flash": {
                "max_input_tokens": 1_048_576,
                "source": "google_official",
            }
        },
    )
    assert get_model_context_window("gemini-2.5-flash") == 1_048_576
    assert (
        get_model_context_window("google_genai:gemini-2.5-flash")
        == DEFAULT_CONTEXT_WINDOW
    )
