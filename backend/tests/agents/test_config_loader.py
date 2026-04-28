"""Tests for VersionConfigLoader strict-schema behavior."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from backend.agent_engine.agents.config_loader import VersionConfigLoader


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
