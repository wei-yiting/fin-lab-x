"""Tests for backend/scripts/refresh_model_context_registry.py.

``litellm.get_model_info()`` only resolves bare model names, while profile
YAMLs store LangChain-style ``provider:model`` identifiers (e.g.
``openai:gpt-5-nano``). ``_collect_model_names`` must strip the provider
prefix before returning names for lookup, or every shipped profile would
fail to resolve when the script is run.
"""

from backend.scripts import refresh_model_context_registry as refresh


def test_collect_model_names_strips_provider_prefix(tmp_path, monkeypatch):
    profile_dir = tmp_path / "fake_profile"
    profile_dir.mkdir()
    (profile_dir / "orchestrator_config.yaml").write_text(
        'model:\n  name: "openai:gpt-5-nano"\n'
    )
    monkeypatch.setattr(refresh, "_PROFILES_DIR", tmp_path)

    names = refresh._collect_model_names()

    assert names == ["gpt-5-nano"]


def test_collect_model_names_strips_prefix_for_multiple_providers(
    tmp_path, monkeypatch
):
    for profile_name, model_name in [
        ("profile_a", "openai:gpt-5-nano"),
        ("profile_b", "google_genai:gemini-3.1-flash-lite"),
        ("profile_c", "anthropic:claude-haiku-4-5"),
        ("profile_d", "gpt-5-mini"),  # bare name, no prefix to strip
    ]:
        profile_dir = tmp_path / profile_name
        profile_dir.mkdir()
        (profile_dir / "orchestrator_config.yaml").write_text(
            f'model:\n  name: "{model_name}"\n'
        )
    monkeypatch.setattr(refresh, "_PROFILES_DIR", tmp_path)

    names = refresh._collect_model_names()

    assert names == sorted(
        ["gpt-5-nano", "gemini-3.1-flash-lite", "claude-haiku-4-5", "gpt-5-mini"]
    )
    assert not any(":" in name for name in names)
