# Fix Round 4

Fixer: Orchestrator (direct, no fixer subagent dispatch) | Date: 2026-08-11

Both Quality and Spec axes independently surfaced the same Major finding (M-4.1), which
is the strongest possible confirmation of a real defect — fixed first and verified via
direct source-tracing into the pinned LangChain version before touching anything else.

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|----------------|
| M-4.1 | Round 3's `kwargs["model_provider"] = "openai"` broke `init_chat_model`'s own prefix-stripping (`_parse_model()` only strips a `provider:` prefix when `model_provider` is *not* explicitly given), so all 5 profiles' `openai:gpt-5-nano` passed through unstripped as a literal, invalid model id. Fixed by moving `model_provider="openai"` + explicit prefix-stripping (reusing `model_context._strip_provider_prefix`) to run unconditionally for the openai branch, ahead of the `reasoning="unsupported"` short-circuit — see m-4.1 below for why that ordering also mattered. Verified via direct `_parse_model()` source trace and a mocked `_init_model` call before/after. | `backend/agent_engine/agents/base.py` |
| m-4.1 | Quality axis independently found the same defect plus a related gap: the `reasoning="unsupported"` short-circuit returns *before* the (now-fixed) openai routing normalization, so a bare or prefixed OpenAI name paired with `reasoning="unsupported"` skipped `model_provider="openai"` + prefix-stripping entirely, leaving it to `init_chat_model`'s own separate provider inference. Folded into the same fix as M-4.1 — the normalization now runs before the short-circuit, applying uniformly across all three reasoning states. Added `test_unsupported_still_forces_openai_routing`. | `backend/agent_engine/agents/base.py`, `backend/tests/agents/test_init_model.py` |
| m-4.2 (nit) | `test_config_loader.py` still had the stale "Task 5" implementation-phase banner comment (Round 1's m-1.4 report claimed this was fixed; it wasn't — this occurrence was missed). Replaced with a durable description. `_valid_payload()`'s default model (`gpt-4o-mini` + implicit `reasoning="off"`) silently encoded a combination this same PR's own docs/tests document as runtime-invalid (classic model + reasoning="off" fails against the real API — see m-2.1/M-2.1). Swapped to `openai:gpt-5-nano` to match the project's actual default and stop being a copy-paste trap. | `backend/tests/agents/test_config_loader.py` |

## Investigated, not changed

| Finding | Disposition |
|---------|-------------|
| Major (Quality axis) — "OpenAI `reasoning='off'` still doesn't guarantee zero reasoning tokens for non-trivial prompts, only verified for a trivial prompt" | Not a new code defect — this is the OpenAI API's actual behavior (no true off-switch exists for gpt-5-tier models; confirmed live in Round 1). Already accurately documented in both the `ModelConfig.reasoning` docstring's OpenAI-specific caveat and `_init_model`'s own docstring. Re-raised the same architectural constraint rather than finding new ground; not fixed here without an explicit human decision to invest in something like heavier per-request effort-tier probing, which would be over-engineering relative to design-envelope §1's scale envelope (1 operator, ≤50 users) for a BYOK-cost concern the admin already controls via `reasoning_effort`. |
| Minor (Quality axis) — "Gemini 3 should use `thinking_level`, not `thinking_budget`; `gemini-3.1-flash-lite` doesn't support full thinking-off" | Checked against Context7 (`langchain-google`'s own docs + test suite): found no support for either claim — `thinking_budget=0` is documented as still valid for "Gemini 2.5 series and later," and no per-model exception for Flash-Lite is documented. Treating as unconfirmed; not acted on. Low-stakes regardless since no shipped profile uses Gemini (illustrative doc example + test parametrize entry only). |
| Minor (Quality axis) — test:production ratio 2.05x (536 test / 262 production lines, excluding lockfile+docs) still exceeds design-envelope §5 rule 5's 2x threshold | Confirmed by recomputing from `git diff --numstat`. Design-envelope §5 rule 5 requires a one-sentence PR-body justification, not a code change — added to PR #46's body instead of trimming legitimate combinatorial provider/state/boundary coverage. |

## Tests Run

| Test Command | Result |
|--------------|--------|
| `.venv/bin/pytest backend/tests/agents/ -q` | 104 passed |
| `.venv/bin/python -m pytest backend/tests/ -q` | 1020 passed, 49 deselected (was 1018 before this round) |
| `.venv/bin/ruff check backend/` | All checks passed |
| `.venv/bin/ruff format backend/` | 179 files unchanged |
| Manual: all 5 profiles' `openai:gpt-5-nano` across all 3 reasoning states, mocked `init_chat_model` | `args[0] == "gpt-5-nano"`, `kwargs["model_provider"] == "openai"` in every case |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|-----------------|----------------|
| `backend/tests/agents/test_init_model.py` | Modified/Added | Strengthened `test_openai_branch_passes_model_provider_explicitly` and `test_bare_default_model_config_is_valid` to assert the positional model-name arg (not just the `model_provider` kwarg) — this is what M-4.1 slipped past. Added `test_unsupported_still_forces_openai_routing` (m-4.1). |
| `backend/tests/agents/test_config_loader.py` | Modified | Comment/fixture-value only (m-4.2) — no new test cases. |

Commit: `10a90fb fix(agents): force OpenAI routing ahead of the unsupported short-circuit, fix prefix-stripping regression` (pushed).
