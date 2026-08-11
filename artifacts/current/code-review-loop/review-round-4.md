# Review Round 4

Reviewers: Codex (Quality axis, Spec axis) | Date: 2026-08-11
Scope: `git diff 906d5b6..HEAD` at the time of dispatch (HEAD `9a927ca`)

## Spec axis (Codex) — findings

| ID | Severity | Summary |
|----|----------|---------|
| M-4.1 | Major | Round 3's M-3.1 fix (`kwargs["model_provider"] = "openai"`) introduced a regression: `langchain.chat_models.base._parse_model()` only strips a `provider:` prefix off the model name when `model_provider` is *not* explicitly given. Since the OpenAI branch now sets `model_provider="openai"` explicitly, all 5 profiles' `name: "openai:gpt-5-nano"` pass through **unstripped** as the literal positional arg to `init_chat_model`, so `ChatOpenAI` would be constructed with `model="openai:gpt-5-nano"` — an invalid model id the real OpenAI API rejects. Confirmed independently by tracing `_parse_model` source (`_parse_model('openai:gpt-5-nano', 'openai') == ('openai:gpt-5-nano', 'openai')`, i.e. unstripped) and by a direct mocked call to `_init_model` before the fix. The existing Round 3 regression test (`test_openai_branch_passes_model_provider_explicitly`) only asserted the `model_provider` kwarg, never the positional model-name arg, so it did not catch this. `test_bare_default_model_config_is_valid` additionally locked in the wrong expected value (`args[0] == "openai:gpt-5-nano"`). |

No Minor or Nit findings; no scope-creep findings. All prior rounds' fixes (dependencies, OpenAI reasoning="off", unrecognized-provider handling, Gemini budget validation, profile model-tier unification, default model, m-3.1 registry-script prefix stripping, tier-consistency doc/registry updates) were independently re-verified against DEV-110 and confirmed conformant.

## Quality axis (Codex)

First dispatch (`aa5100526c0402462`) detached internally waiting on its own background Codex job (same known Bash-tool-timeout failure mode as Round 2) and returned without a real result. Re-dispatched fresh (`ab9fb6751ad592cc5`); see `fix-round-4.md` for outcome once merged into the fix report.

## Fix

M-4.1 fixed directly by the orchestrator (not a separate fixer dispatch) given how narrowly scoped and mechanically verifiable the fix was — see `fix-round-4.md`.
