"""Tests for ProfileConfigLoader strict-schema behavior."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from backend.agent_engine.agents.config_loader import (
    ModelConfig,
    ProfileConfigLoader,
)


def _write_profile_yaml(base_dir: Path, profile_name: str, payload: dict) -> None:
    profile_dir = base_dir / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "orchestrator_config.yaml").write_text(yaml.safe_dump(payload))


def _valid_payload(name: str) -> dict:
    return {
        "version": "0.0.1",
        "name": name,
        "description": "test version",
        "tools": [],
        "model": {"name": "openai:gpt-5-nano", "temperature": 0.0},
        "constraints": {"max_tool_calls_per_run": 5},
    }


def test_load_raises_on_unknown_constraint_key(tmp_path, monkeypatch):
    """Renamed or typo'd constraint keys must fail fast instead of silently
    falling back to defaults."""
    payload = _valid_payload("v_test_stale_constraint")
    # Simulate a stale YAML still using the old key name.
    payload["constraints"] = {"max_tool_calls_per_step": 5}
    _write_profile_yaml(tmp_path, "v_test_stale_constraint", payload)

    monkeypatch.setattr(ProfileConfigLoader, "PROFILES_DIR", tmp_path)

    loader = ProfileConfigLoader("v_test_stale_constraint")
    with pytest.raises(ValidationError) as exc_info:
        loader.load()

    assert "max_tool_calls_per_step" in str(exc_info.value)


def test_load_raises_on_unknown_top_level_key(tmp_path, monkeypatch):
    """Typos at the top level of WorkflowProfileConfig must fail fast."""
    payload = _valid_payload("v_test_stale_top_level")
    payload["descripton"] = "typo of description"  # intentional typo
    _write_profile_yaml(tmp_path, "v_test_stale_top_level", payload)

    monkeypatch.setattr(ProfileConfigLoader, "PROFILES_DIR", tmp_path)

    loader = ProfileConfigLoader("v_test_stale_top_level")
    with pytest.raises(ValidationError) as exc_info:
        loader.load()

    assert "descripton" in str(exc_info.value)


def test_load_accepts_valid_payload(tmp_path, monkeypatch):
    """Sanity: the strict schema still accepts a well-formed payload."""
    payload = _valid_payload("v_test_valid")
    _write_profile_yaml(tmp_path, "v_test_valid", payload)

    monkeypatch.setattr(ProfileConfigLoader, "PROFILES_DIR", tmp_path)

    loader = ProfileConfigLoader("v_test_valid")
    config = loader.load()

    assert config.name == "v_test_valid"
    assert config.constraints.max_tool_calls_per_run == 5


# ---------------------------------------------------------------------------
# ModelConfig.reasoning / thinking_budget: admin-configured reasoning
# capability, independent of the loader's strict-schema behavior above.
# ---------------------------------------------------------------------------


def test_model_config_defaults_reasoning_off():
    cfg = ModelConfig()
    assert cfg.reasoning == "off"
    assert cfg.thinking_budget is None


@pytest.mark.parametrize(
    ("name", "expected_provider", "expected_bare"),
    [
        ("openai:gpt-5-nano", "openai", "gpt-5-nano"),
        ("gpt-5-nano", "openai", "gpt-5-nano"),
        ("google_genai:gemini-3.1-flash-lite", "google_genai", "gemini-3.1-flash-lite"),
        ("anthropic:claude-haiku-4-5", "anthropic", "claude-haiku-4-5"),
    ],
    ids=["openai-prefix", "bare-defaults-openai", "gemini", "anthropic"],
)
def test_model_config_owns_name_parsing(name, expected_provider, expected_bare):
    """``provider``/``bare_name`` are the single owner of ``name`` parsing —
    every consumer (_init_model routing, context-window lookup, registry
    refresh) reads these instead of re-splitting the string."""
    cfg = ModelConfig(name=name)
    assert cfg.provider == expected_provider
    assert cfg.bare_name == expected_bare


def test_model_config_accepts_reasoning_on_with_null_budget(tmp_path, monkeypatch):
    payload = _valid_payload("v_test_reasoning_on")
    payload["model"] = {
        "name": "google_genai:gemini-2.5-flash",
        "temperature": 0.0,
        "reasoning": "on",
        "thinking_budget": None,
    }
    _write_profile_yaml(tmp_path, "v_test_reasoning_on", payload)
    monkeypatch.setattr(ProfileConfigLoader, "PROFILES_DIR", tmp_path)

    config = ProfileConfigLoader("v_test_reasoning_on").load()
    assert config.model.reasoning == "on"
    assert config.model.thinking_budget is None
    assert config.model.name == "google_genai:gemini-2.5-flash"


def test_model_config_accepts_explicit_thinking_budget(tmp_path, monkeypatch):
    payload = _valid_payload("v_test_explicit_budget")
    payload["model"] = {
        "name": "anthropic:claude-sonnet-4-5",
        "temperature": 0.0,
        "reasoning": "on",
        "thinking_budget": 2048,
    }
    _write_profile_yaml(tmp_path, "v_test_explicit_budget", payload)
    monkeypatch.setattr(ProfileConfigLoader, "PROFILES_DIR", tmp_path)

    config = ProfileConfigLoader("v_test_explicit_budget").load()
    assert config.model.thinking_budget == 2048


def test_model_config_rejects_unknown_reasoning_literal(tmp_path, monkeypatch):
    payload = _valid_payload("v_test_bad_reasoning")
    payload["model"] = {
        "name": "google_genai:gemini-2.5-flash",
        "temperature": 0.0,
        "reasoning": "invalid",
    }
    _write_profile_yaml(tmp_path, "v_test_bad_reasoning", payload)
    monkeypatch.setattr(ProfileConfigLoader, "PROFILES_DIR", tmp_path)

    with pytest.raises(ValidationError) as exc_info:
        ProfileConfigLoader("v_test_bad_reasoning").load()
    assert "reasoning" in str(exc_info.value)


def test_model_config_accepts_unsupported_literal():
    cfg = ModelConfig(reasoning="unsupported")
    assert cfg.reasoning == "unsupported"


def test_model_config_rejects_unknown_field():
    """``extra='forbid'`` still applies — typos in the model section fail fast."""
    with pytest.raises(ValidationError):
        ModelConfig(thinking_budgett=1024)  # type: ignore[call-arg]


def test_model_config_reasoning_effort_defaults_to_none():
    cfg = ModelConfig()
    assert cfg.reasoning_effort is None


def test_model_config_accepts_reasoning_effort_string(tmp_path, monkeypatch):
    payload = _valid_payload("v_test_reasoning_effort")
    payload["model"] = {
        "name": "openai:gpt-5.6-luna",
        "temperature": 0.0,
        "reasoning": "on",
        "reasoning_effort": "none",
    }
    _write_profile_yaml(tmp_path, "v_test_reasoning_effort", payload)
    monkeypatch.setattr(ProfileConfigLoader, "PROFILES_DIR", tmp_path)

    config = ProfileConfigLoader("v_test_reasoning_effort").load()
    assert config.model.reasoning_effort == "none"


# ---------------------------------------------------------------------------
# ProfileConfigLoader.load_from_dir: arbitrary-directory loading for
# benchmark/experiment configs that must not live under profiles/. Unlike
# the profile-name constructor, this never auto-discovers a sibling
# system_prompt.md — injection is explicit-only via prompt_path.
# ---------------------------------------------------------------------------


def test_load_from_dir_loads_config_without_prompt_path(tmp_path):
    config_dir = tmp_path / "sample_config"
    config_dir.mkdir()
    (config_dir / "orchestrator_config.yaml").write_text(
        yaml.safe_dump(_valid_payload("sample_config"))
    )

    config = ProfileConfigLoader.load_from_dir(config_dir)

    assert config.name == "sample_config"
    assert config.system_prompt is None


def test_load_from_dir_injects_prompt_from_explicit_path(tmp_path):
    config_dir = tmp_path / "sample_config"
    config_dir.mkdir()
    (config_dir / "orchestrator_config.yaml").write_text(
        yaml.safe_dump(_valid_payload("sample_config"))
    )
    prompt_file = tmp_path / "shared_prompt" / "system_prompt.md"
    prompt_file.parent.mkdir()
    prompt_file.write_text("You are the shared benchmark prompt.\n")

    config = ProfileConfigLoader.load_from_dir(config_dir, prompt_path=prompt_file)

    assert config.system_prompt == "You are the shared benchmark prompt."


def test_load_from_dir_ignores_sibling_system_prompt_md(tmp_path):
    """A stray sibling system_prompt.md must NOT be auto-loaded — unlike the
    profile-name constructor, injection here is explicit-only via
    prompt_path, so N configs sharing one canonical prompt can never drift
    into N slightly-different copies."""
    config_dir = tmp_path / "sample_config"
    config_dir.mkdir()
    (config_dir / "orchestrator_config.yaml").write_text(
        yaml.safe_dump(_valid_payload("sample_config"))
    )
    (config_dir / "system_prompt.md").write_text("Should not be picked up.\n")

    config = ProfileConfigLoader.load_from_dir(config_dir)

    assert config.system_prompt is None


def test_load_from_dir_raises_on_missing_config(tmp_path):
    with pytest.raises(FileNotFoundError):
        ProfileConfigLoader.load_from_dir(tmp_path / "does_not_exist")


def test_load_from_dir_applies_strict_schema_validation(tmp_path):
    config_dir = tmp_path / "bad_config"
    config_dir.mkdir()
    payload = _valid_payload("bad_config")
    payload["descripton"] = "typo of description"
    (config_dir / "orchestrator_config.yaml").write_text(yaml.safe_dump(payload))

    with pytest.raises(ValidationError):
        ProfileConfigLoader.load_from_dir(config_dir)


# ---------------------------------------------------------------------------
# Benchmark configs: the 4 real, shipped candidate configs must load via
# load_from_dir, validate, hold no baked-in system_prompt of their own, and
# correctly carry the reasoning_effort each candidate pins.
# ---------------------------------------------------------------------------

_BENCHMARK_CONFIGS_DIR = (
    Path(__file__).parents[2]
    / "evals"
    / "scenarios"
    / "baseline_behavior_diagnostic_zh"
    / "benchmark"
    / "configs"
)


@pytest.mark.parametrize(
    ("config_name", "expected_provider", "expected_effort"),
    [
        ("luna_none", "openai", "none"),
        ("luna_medium", "openai", "medium"),
        ("gemini_minimal", "google_genai", "minimal"),
        ("gemini_medium", "google_genai", "medium"),
    ],
)
def test_benchmark_configs_load_and_validate(
    config_name, expected_provider, expected_effort
):
    config = ProfileConfigLoader.load_from_dir(_BENCHMARK_CONFIGS_DIR / config_name)

    assert config.model.provider == expected_provider
    assert config.model.reasoning == "on"
    assert config.model.reasoning_effort == expected_effort
    # No prompt file ships inside a benchmark config directory — injection
    # is the loader's job (single canonical prompt, zero drift).
    assert config.system_prompt is None


def test_benchmark_configs_share_the_same_canonical_prompt():
    prompt_path = _BENCHMARK_CONFIGS_DIR.parent / "prompt" / "system_prompt.md"
    for config_name in [
        "luna_none",
        "luna_medium",
        "gemini_minimal",
        "gemini_medium",
    ]:
        config = ProfileConfigLoader.load_from_dir(
            _BENCHMARK_CONFIGS_DIR / config_name, prompt_path=prompt_path
        )
        assert config.system_prompt == prompt_path.read_text().strip()


# ---------------------------------------------------------------------------
# Loader contract: every shipped profile YAML parses into a valid ModelConfig
# with a non-empty model name and a recognized reasoning literal. We
# deliberately do NOT pin the exact model/reasoning values below — see the
# test body's own docstring for why.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "profile",
    ["baseline", "reader", "quant", "graph", "analyst"],
)
def test_all_shipped_profiles_load_into_valid_model_config(profile):
    """Loader contract: every shipped profile YAML parses into a ModelConfig
    with a non-empty model name and a recognized reasoning literal. We do NOT
    pin the exact model/reasoning values here — that is a product decision the
    loader test should not change-detect (a deliberate model swap must not
    require editing this test)."""
    config = ProfileConfigLoader(profile).load()
    assert config.model.name
    assert config.model.reasoning in {"on", "off", "unsupported"}
