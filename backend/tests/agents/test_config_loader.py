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
        "model": {"name": "gpt-4o-mini", "temperature": 0.0},
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
# Task 5: ModelConfig reasoning + thinking_budget fields
# ---------------------------------------------------------------------------


def test_model_config_defaults_reasoning_off():
    cfg = ModelConfig()
    assert cfg.reasoning == "off"
    assert cfg.thinking_budget is None


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


# ---------------------------------------------------------------------------
# Task 5: profile yaml smoke load — every shipped profile runs on OpenAI
# gpt-5-mini with reasoning summaries via the Responses API.
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
