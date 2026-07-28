# Code Review Round 1

> Reviewer: gpt-5.5 | Date: 2026-07-28

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 0 |
| Blocking | 0 |
| Major | 0 |
| Minor | 0 |
| Suggestion | 0 |
| Library checks | 1 |

## Issues

No issues found.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| pytest | `>=8.0.0` | `pytest.raises(match=...)`; marker/addopts behavior referenced by unchanged config/tests | Pass | Regex match strings escape dotted module paths correctly. No deprecated pytest API introduced. |

---

# Spec Conformance Round 1

> Reviewer: claude-fable-5 | Date: 2026-07-28

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Findings

None. The changeset is a faithful, mechanical implementation of DEV-116 with no missing requirements, no scope creep, and no twisted behaviour. All four acceptance criteria were verified empirically (details below).

Two borderline items examined and cleared:

- `backend/tests/evals/test_scorer_registry.py` L32–38 changes an assertion regex (`pytest.raises(match=...)`) in `test_resolve_scorers_raises_import_error_for_missing_module`, and `backend/tests/evals/test_eval_spec_schema.py` rewrites fictional dotpath fixture strings — neither is a plain import swap. Both are forced by the acceptance criterion "grep 無 `backend.evals.scorers` … 殘留引用" (the old fixture strings contained `backend.evals.scorers`), and the "只改 import、不改斷言" clause applies to scorer unit tests, all of which changed imports only. Not findings.
- `backend/evals/README.md` L211–215 still documents the "Add a new regression guardrail" pattern (`backend/evals/test_*.py` with `@pytest.mark.eval`) even though the last instance was deleted. DEV-116 only mandates deleting `test_language_policy.py` (done), and the parent constraint assigns `regression/` to a later ticket; the commit message explicitly defers this section to the regression ticket. Consistent with ticket boundaries — not a finding.

## Covered Requirements

- ✅ 兩支 scorer 搬入各自 scenario 目錄，函式內容一行不動 — `backend/evals/scenarios/language_policy/scorer.py`, `backend/evals/scenarios/sec_retrieval/scorer.py` (both R100 renames from `scorers/`, byte-identical)
- ✅ eval_spec 的 scorer dotted path 同步，完整 dotted path（無相對引用） — `backend/evals/scenarios/language_policy/eval_spec.yaml` L18/L20, `backend/evals/scenarios/sec_retrieval/eval_spec.yaml` L21–L27
- ✅ `scorers/` 目錄刪除 — `backend/evals/scorers/README.md`, `backend/evals/scorers/__init__.py` deleted; `git ls-tree 5670ba6` confirms no `scorers/` remains
- ✅ scenarios package 化（regular package，決策 10） — `backend/evals/scenarios/__init__.py`, `backend/evals/scenarios/language_policy/__init__.py`, `backend/evals/scenarios/sec_retrieval/__init__.py` (all three added)
- ✅ 刪除 dataclass 版題目集 — `backend/evals/datasets/` fully deleted (README.md, `__init__.py`, `language_policy.py`)
- ✅ 刪除舊 pytest gate — `backend/evals/test_language_policy.py` deleted
- ✅ 刪除 eval conftest 的 sync orchestrator fixture（決策 6） — `backend/evals/conftest.py` (fixture `orchestrator` + its Orchestrator/ProfileConfigLoader/SqliteSaver imports removed; unrelated braintrust fixture untouched)
- ✅ `backend/tests` 的 scorer import 同步 — `backend/tests/evals/test_eval_runner.py`, `test_eval_spec_schema.py`, `test_scorer_registry.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_scorers.py`
- ✅ AC: grep 無 `backend.evals.scorers` 與 `datasets.language_policy` 殘留 — `git grep` over the full `5670ba6` tree (both dotted and slash forms, plus `evals.datasets` and `test_language_policy`): zero hits
- ✅ AC: 舊 language_policy pytest gate 不再被 collect — `uv run pytest backend/evals --collect-only -q` → "no tests collected" (also proves the trimmed conftest doesn't break collection)
- ✅ AC: 兩份 eval_spec 的 scorer path 指向 scenario 內 scorer，Quality Track 載入驗證通過 — `load_scenario_config` + `resolve_scorers` executed for both scenarios; all 6 programmatic scorers + 1 llm_judge resolved successfully
- ✅ AC: 全 backend 測試綠 — accepted from orchestrator (833 passed); not re-run per instructions
- ✅ Parent constraint: engine layer 未動 — `eval_runner.py` / `scorer_registry.py` / `dataset_loader.py` absent from the 20-file changeset
- ✅ Parent constraint: 無 later-ticket 內容 — grep for `expected_tool_called` / `on_target_company` / `run_profile` / `regression/` in `5670ba6` backend tree: zero hits; README/ARCHITECTURE edits are strictly path-sync entailed by the move

---

## Orchestrator Notes (Round 1 dispatch record)

- REVIEWER_PROVIDER = codex (model `gpt-5.5`, resolved from `~/.codex/config.toml`); Spec axis = Claude read-only subagent (`claude-fable-5`). Cross-model + session isolation upheld; the two reviewers never saw each other's output.
- Diff range: `4ce4906` → `5670ba6` (20 files, +52/−305). Spec source: Linear DEV-116 description + DEV-89 parent constraints.
- Context7 pre-fetch for Codex: pytest (`/pytest-dev/pytest`) — `raises(match=...)` regex semantics, marker registration, addopts `-m` override behavior. No other external-library API usage added or modified in this diff.
- Loop state after Round 1: zero issues on both axes → per user instruction the loop STOPPED after review (no fixer dispatched, no final verification round). Fresh-session caveat: this orchestrator session also wrote the code; reviewer isolation (Codex sandbox + separate Claude subagent) was the mitigating control.
