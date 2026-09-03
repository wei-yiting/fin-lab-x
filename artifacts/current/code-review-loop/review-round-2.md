# Code Review Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-09-03
> (Copy verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total issues (new, this round) | 5 |
| Blocking | 0 |
| Major | 2 |
| Minor | 3 |
| Suggestion | 0 |
| Library checks | 2 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ⚠️ Partially Fixed | Character alignment is safe for OpenCC 0.1.7, and 台灣/台積電/平台 now pass. However, `{台}` is not a complete dual-status exclusion set. OpenCC contains ~73 (reviewer's count; orchestrator independently derived 170 via a broader criterion, see below) analogous characters whose preferred conversion differs; valid Taiwanese Traditional strings such as 公司公布財報, 市占率保持穩定, and 范先生 still score zero. This remains unreliable under design-envelope §4 and §5. |
| 2 | M-1.2 | Dismissed (user decision) | DEV-206 is the accepted run-path consumer. Not re-raised. |
| 3 | M-1.3 | Dismissed (user decision) | DEV-206 is the accepted benchmark-config consumer. Not re-raised. |
| 4 | M-1.4 | ⚠️ Partially Fixed | Real config directories, YAML identities, README references, and test parametrization now use descriptive names. However, `test_config_loader.py` L196–231 still contains seven literal `c1_luna_none` references across three generic `load_from_dir` loader tests. |
| 5 | m-1.1 | ✅ Fixed | DEV-200/DEV-205 references removed from reviewable source and benchmark data. |
| 6 | m-1.2 | ✅ Fixed | Loader validates JSON root, all three tier lists, and each element as a non-empty string. |
| 7 | m-1.3 | ✅ Fixed | Blank efforts now fail loudly; OpenAI default selected only when `reasoning_effort is None`. |
| 8 | S-1.1 | ✅ Fixed | `load()`/`load_from_dir()` now share `_parse_config()`. |

## Issues (new)

### [Major] M-2.1: Changed dataset content retains the old recorded version
- **File:** `backend/evals/scenarios/baseline_behavior_diagnostic_zh/dataset.csv` L20; `backend/evals/scenarios/baseline_behavior_diagnostic_zh/eval_spec.yaml` L10; `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/split.json` L3
- **Problem:** The Berkshire Hathaway curation text changed from yfinance to Finnhub, but both metadata locations still identify the dataset as `2026-04-24`. `eval_runner.py` writes this version into trace/experiment metadata, so pre-fix and post-fix data are indistinguishable by dataset version. Violates design-envelope §4 reproducibility; §7 under-engineering.
- **Fix:** Assign the corrected dataset a new version; update scenario and split metadata consistently.

### [Major] M-2.2: New process identifiers embedded in permanent artifacts
- **File:** `split.json` L27, L34–35; `scorer.py` L28–29; `test_language_policy_scorer.py` L158–162
- **Problem:** "Pass 1"/"Pass 2" numbered curation stages, and "row 19"/"row 4" scenario-row references in permanent data/comments/docstrings. The scorer is generic to `language_policy` (shared across scenarios), so referencing "this dataset's own row 4" creates misleading cross-scenario coupling.
- **Fix:** Use semantic descriptions ("categorical-column review," "free-text review," "the Berkshire Hathaway rationale," "a TSMC answer") instead of numbered stages/row references.

### [Minor] m-2.1: `apply_split()` does not validate dataset-side row identity
- **File:** `row_selection.py` L161
- **Problem:** Sidecar boundary now validated (round 1's m-1.2), but the dataset-row side isn't — a missing `id` raises incidental `KeyError`, non-string id raises `TypeError` in `join()`, duplicate ids pass through silently.
- **Fix:** Validate every row id as non-empty string, reject duplicates, before membership filtering. Add tests.

### [Minor] m-2.2: Eval-only OpenCC dependency ships in the production image
- **File:** `pyproject.toml` L26
- **Problem:** `opencc-python-reimplemented` is imported only by an eval scorer, but sits in the main `dependencies` list; `backend/Dockerfile` runs `uv sync --no-dev`, so it's unnecessarily shipped to production.
- **Fix:** Move to `[project.optional-dependencies].dev`, regenerate `uv.lock`.

### [Minor] m-2.3: External issue identifier retained in a source comment
- **File:** `scorer.py` L33–35
- **Problem:** "hanzidentifier issue #5" is a third-party tracker id in a source comment; the surrounding prose already explains the reasoning.
- **Fix:** Remove the issue number, keep the descriptive reasoning.

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| opencc-python-reimplemented | 0.1.7 | `OpenCC("s2t")`, reused `.convert()` | ⚠️ API current; interpretation incomplete | Construction/reuse correct; every STCharacters/STPhrases replacement preserves code-point length, so the aligned diff is safe. Incomplete dual-status classification is M-1.1. |
| langchain-google-genai | 4.3.3 | `thinking_level` | ✅ Current | Unchanged; installed source confirms alias. |

---

# Spec Conformance Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-09-03
> (Copy verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total findings (new, this round) | 1 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 1 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | SP-1.1 | Dismissed (user decision) | Not re-evaluated — see scope boundary note |
| 2 | SP-1.2 | ⚠️ Partially Fixed | 台灣/台積電 now score 1; existing full-Simplified/mixed-contamination cases still score 0. But the method still misjudges other legitimate Traditional Chinese — independently reproduced "政府干預市場" → 0 (OpenCC converts 干→幹; allowlist only has 台). |
| 3 | SP-1.3 | ✅ Fixed | Row 19 corrected Finnhub; `curation_pass` records the anomaly accurately. Independently confirmed all 30 rows' non-free-text columns match, and spot-checked rows 1/4/7/10/13/16/19/22/25/28/30's free-text columns — no other drift found. |
| 4 | SP-1.4 | ✅ Fixed | Three real-split-allocation tests and their constants removed; no equivalent assertions found elsewhere. |

## Findings (new)

### [Major] SP-2.1: 非 dev split 可在 frozen tag 前解鎖
- **Type:** Misimplemented
- **Spec:** "Row selection 預設只允許 dev rows；holdout/reserve 需明確 opt-in，且僅限凍結 tag 之後。" (DEV-200 frozen cross-ticket decisions)
- **File:** `row_selection.py` L134
- **Problem:** `load_split_sidecar()` discards `status` when parsing into `SplitSidecar`; `apply_split()` only checks `include_holdout`/`include_reserve` flags. Even with `split.json`'s `status: "proposed"` and no frozen git tag at HEAD, either flag would immediately return non-dev rows. Distinct from the dismissed SP-1.1 (run-path wiring) — this is a gap in the guard's own logic, independent of whether it's wired to a caller yet.
- **Fix:** Have the parsed sidecar retain freeze-state/tag identity; `apply_split()` should reject holdout/reserve opt-in when the split isn't frozen or has no matching frozen tag. DEV-205's proposed sidecar should stay locked; DEV-206's actual freeze/tag unlocks it. Test via synthetic sidecars, don't resurrect real-allocation assertions.

## Covered Requirements

✅ ModelConfig 可表達並正確映射四組 reasoning 強度 — `base.py`
✅ Profile config 可由指定目錄載入，shared prompt 由明確的 prompt_path 注入 — `config_loader.py`
✅ 四個 renamed benchmark configs 均可通過 schema 載入 — `benchmark/configs/`
✅ Shared prompt 與 baseline profile prompt 完全一致，未提前進行 DEV-206 的 prompt evolution — `benchmark/prompt/system_prompt.md`
✅ Split sidecar loader 與 apply_split() 提供 dev-only default 及分 tier opt-in；post-tag gate 仍受 SP-2.1 約束 — `row_selection.py`
✅ zh dataset row 19 已修正，30 rows categorical twins 一致，11-row free-text spot-check 未發現其他 drift — `dataset.csv`
✅ Split proposal 仍為 dev 8／holdout 16／reserve 6，完整涵蓋 30 ids — `split.json`
✅ Proposal 仍停在 human split-review gate（status: proposed，無新 frozen tag）— `split.json`
✅ 實際 split allocation 未放入 unit tests — `test_diagnostic_row_selection.py`
✅ ruff format/check 均通過 — `backend/`
⚠️ 本輪唯讀限制未重跑完整 pytest suite（orchestrator has independently run and confirmed this separately）

---

## Discussion Gate Resolution (Round 2)

Orchestrator independently investigated before discussion:
- Verified `政府干預市場`/`公司公布財報`/`市占率保持穩定`/`范先生` false positives directly (all real).
- Traced root cause: OpenCC's phrase table (`STPhrases.txt`) already correctly resolves common dual-status phrases (相干/若干/干燥→乾燥 all have explicit entries); the bug only surfaces for phrases *absent* from that table, which fall through to a character-level default that isn't always the intended reading.
- Systematically derived the full dual-status set from OpenCC's own `STCharacters.txt`: 170 characters where the key appears in its own candidate list (self-referential entries) — this is a data-driven, complete derivation, not one-at-a-time discovery. All of the round-2 reviewers' counter-examples (台/布/占/范/干) fall within this set.
- Confirmed `dataset_version` flows into `eval_runner.py`'s trace/experiment metadata (real reproducibility signal, not cosmetic).
- Confirmed `opencc-python-reimplemented` sits in the main `dependencies` list while `autoevals`/`braintrust` (the eval tooling it actually serves) are already in `[project.optional-dependencies].dev`; `backend/Dockerfile` runs `uv sync --no-dev` — m-2.2 is accurate.

### Resolution Table

| ID | Resolution |
|---|---|
| M-1.1 / SP-1.2 (still partial after round 1) | **Fix with modified direction, following an explicit user policy decision.** User decided this scorer's job is "is the response written in the wrong language overall," not "zero-tolerance character purity" — an occasional genuine mistake is tolerable, a wholesale-wrong-language response is not. Redesign: keep the per-character diff (length-preserving invariant check stays) + the dual-status exclusion set, but systematically derive it from OpenCC's own `STCharacters.txt` (170 self-referential entries — see below) instead of the round-1 hardcoded `{"台"}`. Change the pass/fail rule from "any remaining genuine change = fail" to "ratio of remaining (non-dual-status) changed CJK characters, over total CJK characters, > 15% = fail." Orchestrator verified empirically: legitimate dense-but-correct Traditional text tops out around 11.8% (a TSMC/Taiwan-heavy paragraph using 台/占 repeatedly with zero genuine errors), while genuinely-simplified samples ranged 21.4%–42.6% — comfortable margin either side of 15%. `test_partially_contaminated_response_scores_zero`'s expected result flips from 0.0 to 1.0 — this is the direct, intended consequence of the user's policy decision, not a regression; document it as such. Also verified: dropping the dual-status set entirely (relying on the ratio alone) is NOT safe — the same TSMC/Taiwan paragraph hits 11.8% from legitimate dual-status usage alone, too close to 15% to have real margin; keep both mechanisms, they're complementary. |
| M-1.4 (still partial) | **Fix as suggested.** Rename the 3 remaining `c1_luna_none` generic placeholder strings in `test_config_loader.py`'s `load_from_dir` tests to a clearly-generic name unrelated to any real candidate. |
| M-2.1 | **Fix as suggested.** Bump `dataset_version` in `baseline_behavior_diagnostic_zh/eval_spec.yaml`, `baseline_behavior_diagnostic/eval_spec.yaml` (en twin, kept in sync since `split.json.applies_to` treats them as one paired unit), and `split.json`'s own `dataset_version` field, together, to a new consistent value. |
| M-2.2 | **Resolved via a different path than either original proposal.** scorer.py's and the test file's "this dataset's own row 4" / "dataset row 4" references get reworded to not name an external dataset's row (agreed early). split.json's "Pass 1/Pass 2/row 19" wording dispute became moot — see the split.json restructuring below, which removes that content entirely rather than rewording it. |
| m-2.1 | **Fix as suggested.** Add dataset-side row validation (non-empty string ids, reject duplicates) in `apply_split()`, analogous to round 1's sidecar-side validation. |
| m-2.2 | **Fix as suggested.** Move `opencc-python-reimplemented` from the main `dependencies` list to `[project.optional-dependencies].dev` in `pyproject.toml`; regenerate `uv.lock`. |
| m-2.3 | **Fix as suggested.** Remove the "hanzidentifier issue #5" external tracker reference (folded into the scorer.py comment rewrite for M-1.1). |
| SP-2.1 | **Fix with modified direction.** User chose option (b) over querying git tags at runtime: add `status` to `SplitSidecar`, have `load_split_sidecar()` actually preserve it (currently silently dropped), have `apply_split()` reject `include_holdout=True`/`include_reserve=True` unless `status == "frozen"`. No git-tag introspection in code — matches DEV-205's own "guards against slips, not malice" framing for this guard. |
| (new, surfaced during discussion) split.json narrative fields | User asked why `curation_pass`/`stratification` exist at all if nothing reads them, and observed `curation_pass` should record final state, not process. Orchestrator verified via repo-wide grep: zero code anywhere reads `stratification`, `twin_rule`, `curation_pass`, `forced_overrides`, or `manual_adjustments` — `load_split_sidecar()` only ever reads `dev`/`holdout`/`reserve` (and now `status`). Resolution: remove `curation_pass` entirely (the row-19 fix history already lives durably in `fix-round-1.md`, no need to restate it in production data). Remove `stratification` entirely (the split *rule* — capability_band × expected_baseline_behavior, proportional — is already the frozen DEV-200 decision of record; the seed-search and rounding-math narrative is pure implementation process with no forward value). Move `twin_rule` and the "row 5 is intentionally pinned to holdout, being the sole beyond_boundary × should_fail_cleanly row" fact to `benchmark/README.md` as brief usage notes (these are standing rules a reader needs, not process narrative). split.json's final shape: `dataset_name`, `dataset_version`, `applies_to`, `split_date`, `status`, `counts`, `dev`, `holdout`, `reserve`. |

(User confirmed the full list with "ok" after the split.json restructuring proposal — see chat for the full discussion. Handed to fixer as fix-round-2.md's issue list.)
