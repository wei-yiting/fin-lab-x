from backend.api.main import DEFAULT_WORKFLOW_PROFILE, _workflow_profile


def test_profile_defaults_to_baseline(monkeypatch):
    monkeypatch.delenv("WORKFLOW_PROFILE", raising=False)
    assert _workflow_profile() == DEFAULT_WORKFLOW_PROFILE == "baseline"


def test_profile_is_selected_by_env_var(monkeypatch):
    monkeypatch.setenv("WORKFLOW_PROFILE", "quant")
    assert _workflow_profile() == "quant"
