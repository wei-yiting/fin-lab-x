# Fix Round 2

> Fixer: Claude (general-purpose subagent) | Date: 2026-09-03

## Fixed

| Issue | How Fixed | Files Changed |
|-------|-----------|----------------|
| 1 (Major) — redesign `response_no_simplified_chars` | **Part A:** replaced the hardcoded `{"台"}` frozenset with `_load_dual_status_traditional_chars()`, parsing OpenCC's bundled `STCharacters.txt` at import time, keeping every character that appears in its own candidate list. Derives exactly 170 characters for the pinned `opencc-python-reimplemented==0.1.7`, including 干/布/占/范 (round-2 counter-examples). No try/except — fails loudly at import if the file is missing/malformed. **Part B:** replaced the zero-tolerance check with a CJK-scoped ratio: `genuine_changes / total_cjk <= _MAX_SIMPLIFIED_RATIO` (0.15, named module constant with rationale comment). Rewrote the module comment (no longer claims "hardcoded"), reworded the TSMC example to drop dataset/row ownership, dropped the "hanzidentifier issue #5" reference. Updated the function docstring. | `backend/evals/scenarios/language_policy/scorer.py`, `backend/tests/evals/test_language_policy_scorer.py` |
| 2 (Major) — rename remaining placeholders | Renamed all 7 occurrences of `"c1_luna_none"` to `"sample_config"` across the 3 `load_from_dir` tests. | `backend/tests/agents/test_config_loader.py` |
| 3 (Major) — bump `dataset_version` | Bumped all three occurrences from `"2026-04-24"` to `"2026-09-03"`. | zh + en `eval_spec.yaml`, `split.json` |
| 4 (Minor) — dataset-side row validation | Added validation raising `ValueError` for missing/non-string/empty `id`, and duplicate-id detection via `_find_duplicates`, both firing before the "not present in sidecar" check. | `row_selection.py`, `test_diagnostic_row_selection.py` |
| 5 (Minor) — move opencc to dev deps | Moved `opencc-python-reimplemented>=0.1.7` to `[project.optional-dependencies].dev`; ran `uv lock` (4-line diff). | `pyproject.toml`, `uv.lock` |
| 6 (Major) — freeze-state gate | Added `status: str` to `SplitSidecar`; `load_split_sidecar()` requires/preserves it; `apply_split()` raises `ValueError` if `include_holdout`/`include_reserve` requested while `status != "frozen"`. Real `split.json`'s `status` left as `"proposed"`. | `row_selection.py`, `test_diagnostic_row_selection.py` |
| 7 | No-op, folded into Issue 1. | — |
| 8 (new) — restructure `split.json` | Removed `curation_pass`, `stratification`, `twin_rule` (JSON field) entirely. Final keys: `dataset_name, dataset_version, applies_to, split_date, status, counts, dev, holdout, reserve`. Added two prose notes to README (twin-tier rule, row 5 pinning). | `split.json`, `benchmark/README.md` |

## Not Fixed

None — all 8 items addressed, no design deviations from what was discussed.

## Reverted

None.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pytest backend/tests/evals/test_language_policy_scorer.py -v` | 20 passed | Issue 1 |
| `pytest backend/tests/agents/test_config_loader.py -v` | 30 passed | Issue 2 |
| `pytest backend/tests/evals/test_diagnostic_row_selection.py -v` | 34 passed | Issues 4 + 6 |
| `pytest backend/tests/` (full suite) | 1375 passed, 61 deselected | |
| `ruff format backend/` | 3 files reformatted (cosmetic) | |
| `ruff check backend/` | All checks passed | |

**Orchestrator independently re-verified**: ran the full suite (`1375 passed, 61 deselected` — confirmed identical) and `ruff format --check`/`ruff check` (both clean); read `scorer.py` in full and confirmed the derivation logic, ratio logic, and docstrings match the agreed design; directly imported `_DUAL_STATUS_TRADITIONAL_CHARS` and confirmed `len() == 170` and it includes 台/干/布/占/范; ran all 4 round-2 counter-example phrases (干預, 公司公布財報, 市占率保持穩定, 范先生) through the live scorer and confirmed all score 1.0; read `row_selection.py` in full and confirmed the freeze-gate and dataset-side validation logic; confirmed `pyproject.toml` has `opencc-python-reimplemented` under `[project.optional-dependencies].dev`, alphabetically placed, and gone from the main `dependencies` list; read `split.json` and confirmed its final key set is exactly the agreed 9 keys with no stratification/curation_pass/twin_rule remaining; read `README.md` and confirmed the two new prose notes are present and no curation_pass/seed-search narrative was added.

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|-----------------|----------------|
| `test_language_policy_scorer.py` | Renamed `test_partially_contaminated_response_scores_zero` → `test_response_with_occasional_genuine_mistake_still_scores_one`, flipped assertion to 1.0 | New tolerant-by-design policy (user's explicit decision) |
| same | Added parametrized `test_other_dual_status_characters_score_one` (干預, 公司公布財報, 市占率保持穩定, 范先生) | Round-2 counter-examples |
| same | `test_fully_simplified_response_scores_zero` kept unmodified, verified passing (ratio 0.3929) | "Wholesale wrong language" must still be caught |
| `test_config_loader.py` | Modified (rename only) | Issue 2 |
| `test_diagnostic_row_selection.py` | `_write_sidecar` helper gained `status` kwarg; added `test_rejects_missing_status`, `test_rejects_empty_status`, 6 freeze-gate tests (holdout/reserve × proposed/frozen, plus dev-only-ignores-status ×2), `test_rejects_row_missing_id`, `test_rejects_row_with_non_string_id`, `test_rejects_duplicate_ids_in_rows` | Issues 4 + 6's explicitly required test matrix |

Fixer's note (not a deviation): raised two separate `ValueError`s in `apply_split()` (one per flag) rather than one combined message — gives a more specific error when only one flag is set; the task specified the logical condition, not exact wording.
