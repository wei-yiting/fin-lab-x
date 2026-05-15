"""Tests for VersionConfigLoader strict-schema behavior."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from backend.agent_engine.agents.config_loader import (
    ModelConfig,
    VersionConfigLoader,
)


def _write_version_yaml(base_dir: Path, version_name: str, payload: dict) -> None:
    version_dir = base_dir / version_name
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "orchestrator_config.yaml").write_text(yaml.safe_dump(payload))


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
    _write_version_yaml(tmp_path, "v_test_stale_constraint", payload)

    monkeypatch.setattr(VersionConfigLoader, "VERSIONS_DIR", tmp_path)

    loader = VersionConfigLoader("v_test_stale_constraint")
    with pytest.raises(ValidationError) as exc_info:
        loader.load()

    assert "max_tool_calls_per_step" in str(exc_info.value)


def test_load_raises_on_unknown_top_level_key(tmp_path, monkeypatch):
    """Typos at the top level of VersionConfig must fail fast."""
    payload = _valid_payload("v_test_stale_top_level")
    payload["descripton"] = "typo of description"  # intentional typo
    _write_version_yaml(tmp_path, "v_test_stale_top_level", payload)

    monkeypatch.setattr(VersionConfigLoader, "VERSIONS_DIR", tmp_path)

    loader = VersionConfigLoader("v_test_stale_top_level")
    with pytest.raises(ValidationError) as exc_info:
        loader.load()

    assert "descripton" in str(exc_info.value)


def test_load_accepts_valid_payload(tmp_path, monkeypatch):
    """Sanity: the strict schema still accepts a well-formed payload."""
    payload = _valid_payload("v_test_valid")
    _write_version_yaml(tmp_path, "v_test_valid", payload)

    monkeypatch.setattr(VersionConfigLoader, "VERSIONS_DIR", tmp_path)

    loader = VersionConfigLoader("v_test_valid")
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
    _write_version_yaml(tmp_path, "v_test_reasoning_on", payload)
    monkeypatch.setattr(VersionConfigLoader, "VERSIONS_DIR", tmp_path)

    config = VersionConfigLoader("v_test_reasoning_on").load()
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
    _write_version_yaml(tmp_path, "v_test_explicit_budget", payload)
    monkeypatch.setattr(VersionConfigLoader, "VERSIONS_DIR", tmp_path)

    config = VersionConfigLoader("v_test_explicit_budget").load()
    assert config.model.thinking_budget == 2048


def test_model_config_rejects_unknown_reasoning_literal(tmp_path, monkeypatch):
    payload = _valid_payload("v_test_bad_reasoning")
    payload["model"] = {
        "name": "google_genai:gemini-2.5-flash",
        "temperature": 0.0,
        "reasoning": "invalid",
    }
    _write_version_yaml(tmp_path, "v_test_bad_reasoning", payload)
    monkeypatch.setattr(VersionConfigLoader, "VERSIONS_DIR", tmp_path)

    with pytest.raises(ValidationError) as exc_info:
        VersionConfigLoader("v_test_bad_reasoning").load()
    assert "reasoning" in str(exc_info.value)


def test_model_config_accepts_unsupported_literal():
    cfg = ModelConfig(reasoning="unsupported")
    assert cfg.reasoning == "unsupported"


def test_model_config_rejects_unknown_field():
    """``extra='forbid'`` still applies — typos in the model section fail fast."""
    with pytest.raises(ValidationError):
        ModelConfig(thinking_budgett=1024)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Task 5: v1-v5 yaml smoke load — v1_baseline ships on OpenAI gpt-5-mini
# (reasoning summaries via the Responses API); v2-v5 keep the Gemini A/B
# baseline pending a per-version audit.
# ---------------------------------------------------------------------------


def test_v1_baseline_uses_openai_reasoning_on():
    config = VersionConfigLoader("v1_baseline").load()
    assert config.model.name == "openai:gpt-5-mini"
    assert config.model.reasoning == "on"
    # OpenAI's Responses API uses reasoning={effort, summary} (set in
    # _init_model), not thinking_budget, so the field is null.
    assert config.model.thinking_budget is None


@pytest.mark.parametrize(
    "version",
    ["v2_reader", "v3_quant", "v4_graph", "v5_analyst"],
)
def test_other_shipped_versions_use_gemini_with_reasoning_on(version):
    config = VersionConfigLoader(version).load()
    assert config.model.name == "google_genai:gemini-2.5-flash"
    assert config.model.reasoning == "on"
    assert config.model.thinking_budget is None
