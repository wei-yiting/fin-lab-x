# Fix Round 1

> Fixer: Claude (general-purpose subagent) | Date: 2026-09-03

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 / SP-1.2 | Replaced whole-string `convert() == response` equality with a length-preserving per-character diff (`s2t` conversion verified length-preserving against OpenCC's own dictionaries). Added `_DUAL_STATUS_TRADITIONAL_CHARS = frozenset({"台"})`, excluded from contamination counting, with a comment explaining the dual-status ambiguity (OpenCC's own `STCharacters.txt` entry for 台 lists itself as a valid Traditional candidate). Researched `zhon`/`hanzidentifier` as alternatives first — same ambiguity class, would add 2 deps for a ~30-row eval — and rejected them. Added a defensive check that raises if the length-preserving invariant ever breaks. Corrected the docstring's false "never flags valid Traditional text" claim. | `backend/evals/scenarios/language_policy/scorer.py`, `backend/tests/evals/test_language_policy_scorer.py` |
| M-1.4 | Renamed all 4 config dirs via `git mv` (`c1_luna_none`→`luna_none`, `c2_luna_medium`→`luna_medium`, `c3_gemini_minimal`→`gemini_minimal`, `c4_gemini_medium`→`gemini_medium`). Updated each YAML's `name:`/`description:` fields (dropped `DEV-200`/`candidate C1` labels, reworded cross-references like "vs C2's" → "vs luna_medium's"). Updated README.md's layout reference and `test_config_loader.py`'s parametrize lists + section header. | 4 renamed config dirs + YAMLs, `benchmark/README.md`, `backend/tests/agents/test_config_loader.py` |
| SP-1.3 (scope b — orchestrator manually re-checked all 30 rows' free-text columns before this fix; row 19 was the only anomaly) | Fixed zh `dataset.csv` row 19: `現有 yfinance 指標` → `現有 Finnhub 指標`. Rewrote `split.json`'s `curation_pass` to describe both passes (categorical: 0 anomalies; free-text follow-up: 1 anomaly found and corrected). | `backend/evals/scenarios/baseline_behavior_diagnostic_zh/dataset.csv`, `benchmark/split.json` |
| SP-1.4 | Removed `test_real_split_proposal_has_the_frozen_counts`, `test_real_split_proposal_covers_every_zh_dataset_row_exactly_once`, `test_real_split_proposal_pins_the_sole_beyond_boundary_fail_row_to_holdout`, plus the now-unused `REAL_SPLIT_PATH`/`ZH_DATASET_PATH` constants and section header. `TestLoadSplitSidecar`/`TestApplySplit` (synthetic-sidecar tests) untouched. | `backend/tests/evals/test_diagnostic_row_selection.py` |
| m-1.1 | Removed `(frozen decision, DEV-200)` parenthetical from `split.json`'s `forced_overrides[0].reason`. | `benchmark/split.json` |
| m-1.2 | `load_split_sidecar` now validates the parsed root is a `dict` and every tier element is a non-empty post-`.strip()` string, raising an actionable `ValueError`. Added `test_rejects_non_object_root` and a parametrized malformed-row-id test (empty/whitespace/non-string/`None`). | `backend/evals/diagnostic/row_selection.py`, `backend/tests/evals/test_diagnostic_row_selection.py` |
| m-1.3 | Added a sibling check next to the existing `reasoning_effort`/`reasoning="on"` guard: raises `ValueError` if `reasoning_effort` is non-`None` but empty/blank after `.strip()`. Changed `effort = config.reasoning_effort or "medium"` to an explicit `is not None` check. Added a parametrized regression test. | `backend/agent_engine/agents/base.py`, `backend/tests/agents/test_init_model.py` |
| S-1.1 | Extracted `ProfileConfigLoader._parse_config(config_path, prompt_path)` (staticmethod) with the shared "read YAML → optionally inject prompt → construct `WorkflowProfileConfig`" logic. `load()`'s auto-discovery semantics (only pass the sibling path if `.exists()`) and `load_from_dir()`'s pass-through-whatever-was-given semantics are both preserved. | `backend/agent_engine/agents/config_loader.py` |

## Not Fixed

None — all 8 agreed issues addressed.

## Dismissed (not part of this round — resolved at the Round 1 discussion gate, not sent to fixer)

M-1.2, SP-1.1, M-1.3 — split guard / `load_from_dir()` / benchmark configs having no production caller yet. User decision: DEV-206 is the confirmed, already-ticketed consumer (its "Blocked by" text explicitly requires this code); no fix needed this round. See `review-round-1.md`'s Discussion Gate Resolution section.

## Reverted

None — no fix broke tests.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pytest backend/tests/evals/test_language_policy_scorer.py -v` | 16 passed | Includes 2 new regression tests (台灣/台積電 pass; mixed legitimate+genuine-Simplified still fails) |
| `pytest backend/tests/agents/test_config_loader.py -v` | 30 passed | Confirms rename and helper extraction are both behavior-preserving |
| `pytest backend/tests/evals/test_diagnostic_row_selection.py -v` | 23 passed | 3 removed (SP-1.4), 5 added (m-1.2) net from round 1's 21 |
| `pytest backend/tests/agents/test_init_model.py -v` | 43 passed | Includes 2 new parametrized cases (empty/whitespace `reasoning_effort` raises) |
| `ruff format backend/` | Reformatted 2 files (both edited test files; whitespace/line-wrap only) | |
| `ruff check backend/` | All checks passed | |
| `pytest backend/tests/` (full suite) | 1360 passed, 61 deselected | Deselected = `-m eval` regression suite (manual/pre-merge only per AGENTS.md), correctly excluded |

**Orchestrator independently re-ran** the full suite (`1360 passed, 61 deselected` — confirmed identical), `ruff format --check backend/` and `ruff check backend/` (both clean), read the scorer fix in full, confirmed row 19 + `curation_pass` in the actual files, and confirmed the 3 remaining `c1_luna_none` strings in `test_config_loader.py` are unrelated generic `load_from_dir()` placeholder-directory-name tests (not missed benchmark-config references) before accepting this round's report.

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|-----------------|----------------|
| `backend/tests/evals/test_language_policy_scorer.py` | Added 2 tests | `台灣`/`台積電` responses score 1.0 (the concrete false-positive regression); a response mixing legitimate 台 with genuine Simplified characters still scores 0.0 (allowlist doesn't over-mask) |
| `backend/tests/agents/test_init_model.py` | Added 1 parametrized test (2 cases) | Empty-string and whitespace-only `reasoning_effort` both raise `ValueError` |
| `backend/tests/evals/test_diagnostic_row_selection.py` | Removed 3 tests + 2 constants + header; added 2 tests (one parametrized, 4 cases) | Removed: real-split-proposal allocation assertions (belongs at the human review gate). Added: non-object JSON root rejected; malformed row-id elements rejected |
| `backend/tests/agents/test_config_loader.py` | Modified (identifiers only) | Parametrize lists and section header updated to the renamed configs |
