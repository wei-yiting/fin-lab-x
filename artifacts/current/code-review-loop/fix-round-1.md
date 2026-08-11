# Fix Round 1

Fixer: Claude subagent (general-purpose) | Date: 2026-08-11

Orchestrator note: the byte-identical-to-reference-branch constraint was explicitly
waived by the human for this fix round — all issues below were fixed on their merits,
even where the reference branch (`feat/multi-provider-streaming-reasoning`) carries the
same defect. See the Linear DEV-110 comment for the resulting divergence record.

The M-1.2 fix was informed by a live API call against the real OpenAI API (not
documentation alone) — see the DEV-110 comment for the raw numbers.

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 | Added `langchain-anthropic>=0.4.0` and `langchain-google-genai>=2.0.0` to `dependencies`; regenerated `uv.lock` | `pyproject.toml`, `uv.lock` |
| M-1.2 | OpenAI branch's `reasoning != "on"` path now sets `kwargs["reasoning_effort"] = "minimal"` (empirically verified — see below). Updated docstring and README reasoning matrix. Added regression test. | `backend/agent_engine/agents/base.py`, `backend/agent_engine/agents/README.md`, `backend/tests/agents/test_init_model.py` |
| M-1.3 | `else` → `elif provider == "openai":`; unrecognized providers now raise `ValueError` on `reasoning="on"`, no-op otherwise. Added regression + unrecognized-provider tests. | `backend/agent_engine/agents/base.py`, `backend/tests/agents/test_init_model.py` |
| m-1.2 | Gemini branch raises `ValueError` when `reasoning="on"` and `thinking_budget` is `0` or `< -1`. Added boundary tests. | `backend/agent_engine/agents/base.py`, `backend/tests/agents/test_init_model.py` |
| m-1.3 | Docstring's `openai` bullet rewritten to describe both the on/off kwarg shapes correctly. | `backend/agent_engine/agents/base.py` |
| m-1.4 | Replaced stale "Task 5"/gpt-5-mini banner comment with an accurate, durable description of the loader-contract invariant under test. | `backend/tests/agents/test_config_loader.py` |
| m-1.5 | Moved `Path`/`yaml` imports to module level, removed function-local copies. | `backend/tests/agents/test_utils_model_context.py` |
| SPX-1.2 | All 4 non-baseline profiles moved from `openai:gpt-5-mini` to `openai:gpt-5-nano` — all 5 shipped profiles now on the same model tier. | `backend/agent_engine/agents/profiles/{analyst,graph,quant,reader}/orchestrator_config.yaml` |

## Deferred (orchestrator decision, not the fixer's)

| Issue ID | Reason |
|----------|--------|
| m-1.1 (Anthropic adaptive thinking) | No current profile uses Anthropic reasoning at all; adding `{"type":"adaptive"}` support requires a `ModelConfig` schema decision (what does `thinking_budget=None` mean — error vs. adaptive?) with no real usage to validate against yet. Speculative, deferred per YAGNI. |
| S-1.1 (`use_responses_api=True` redundant) | Context7 confirms `reasoning={...}` alone routes to the Responses API, but keeping the flag explicit is a deliberate choice — avoids depending on that implicit-routing behavior staying unchanged upstream. |
| SP-1.1 (`common/` refactor unassigned in the 8-段拆法) | Train-planning-level gap, not a PR2 code fix. Recorded in the DEV-110 comment instead. |

## Live API Verification (M-1.2)

Run against the real OpenAI API using the project's own key, prompt `"Say OK."`,
`temperature: 1`:

| Model | `reasoning_effort` | `reasoning_tokens` | `completion_tokens` |
|-------|---------------------|---------------------|----------------------|
| `gpt-5-nano` | (omitted) | 128 | 139 |
| `gpt-5-nano` | `"none"` | rejected — `Unsupported value: 'reasoning_effort' does not support 'none' with this model` | — |
| `gpt-5-nano` | `"minimal"` | 0 | 11 |
| `gpt-5-mini` | (omitted) | 64 | 74 |
| `gpt-5-mini` | `"none"` | rejected (same error) | — |
| `gpt-5-mini` | `"minimal"` | 0 | 10 |

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `.venv/bin/pytest backend/tests/agents/test_init_model.py backend/tests/agents/test_config_loader.py backend/tests/agents/test_utils_model_context.py -q` | 53 passed | Targeted files |
| `.venv/bin/python -m pytest backend/tests/ -q` | 1014 passed, 49 deselected | Full backend suite — no regressions (was 1007 before this round) |
| `.venv/bin/ruff check backend/` | All checks passed | |
| `.venv/bin/ruff format backend/` | 177 files unchanged | No formatting drift |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/agents/test_init_model.py` | Added | `test_openai_reasoning_off_sets_reasoning_effort_minimal`, `test_explicit_openai_prefix_reasoning_on_regression`, `TestInitModelUnrecognizedProvider` (raises on `"on"`, no-op on `"off"`), `test_gemini_reasoning_on_with_dynamic_budget_negative_one_passes`, `test_gemini_reasoning_on_with_thinking_budget_zero_raises`, `test_gemini_reasoning_on_with_thinking_budget_below_negative_one_raises` |
| `backend/tests/agents/test_config_loader.py` | Modified | Comment-only |
| `backend/tests/agents/test_utils_model_context.py` | Modified | Import-location-only |

Commit: `c9a75dd fix(agents): dark-reasoning OpenAI default, provider dependency gaps, and Gemini budget validation` (local, not yet pushed).
