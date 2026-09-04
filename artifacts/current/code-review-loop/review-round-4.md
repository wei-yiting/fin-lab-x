# Code Review Round 4

> Reviewer: gpt-5.6-sol | Date: 2026-09-04

## Summary

| Metric | Count |
|--------|-------|
| Total issues (new, this round) | 0 |
| Blocking | 0 |
| Major | 0 |
| Minor | 0 |
| Suggestion | 0 |
| Library checks | 2 |

Round 3's three fixes all confirmed effective. No regressions found in rounds 1-2's fixes.
Satisfies design-envelope §4 eval measurement rigor and §5 scorer-testing requirements.

Verification performed (actually executed, not just read):
- `test_language_policy_scorer.py`: 21 passed
- Ruff lint / format check: both pass
- Dual-status derivation: actually 170 characters
- 台灣/台積電/干預/公司公布財報: all score 1.0
- Fully-Simplified case: 11/28 genuine changes, 39.29% ratio → 0.0
- Absolute-floor case: 4/57 genuine changes, 7.02% ratio (below the 15% threshold) → still 0.0, confirming the floor works independently of ratio
- All 4 benchmark configs, shared-prompt injection, and proposed-split gates actually loaded and exercised
- Process-identifier scan across all scoped files: zero hits

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ✅ Fixed | `load_from_dir()` redesign holds; 4 benchmark configs load outside `profiles/` with explicit shared-prompt injection. |
| 2 | M-1.2 | Dismissed (user decision) | DEV-206 consumer exception boundary still clear; no new change expands it beyond §3's excluded selection-framework territory. |
| 3 | M-1.3 | Dismissed (user decision) | No new change in the cumulative diff that would overturn the original dismissal. |
| 4 | M-1.4, m-1.1, m-1.2, m-1.3, S-1.1 | ✅ Fixed | Light re-check against code/tests/docs; fixes hold, no regression. |
| 5 | M-2.1 | ✅ Fixed | en/zh `dataset_version` both stay `2026-09-03`, split metadata consistent. |
| 6 | M-2.2 | ✅ Fixed | Rescanned all scoped files — no round numbers, Part A/B, or internal finding ids found. |
| 7 | m-2.1 | ✅ Fixed | `apply_split()` still rejects malformed/duplicate/unknown dataset row ids. |
| 8 | m-2.2 | ✅ Fixed | `opencc-python-reimplemented>=0.1.7` still in dev dependencies, lockfile at 0.1.7. |
| 9 | m-2.3 | ✅ Fixed | `hanzidentifier` appears only as an evaluated-and-rejected alternative, no false dependency/API claim. |
| 10 | M-3.1 | ✅ Fixed | Test docstring's "Round-2"/"Part A" removed; full-scope process-identifier scan returns nothing. |
| 11 | M-3.2 | ✅ Fixed | Scorer now requires both `genuine_changes <= 3` and ratio `<= 0.15`; the 4/57 case actually runs to 0.0. |
| 12 | M-3.3 | ✅ Fixed | Import-time sanity check present; real dictionary derivation is 170, assertion doesn't false-fire. |

## Issues (new findings only)

None.

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| opencc-python-reimplemented | 0.1.7 | `OpenCC("s2t")`, `convert()`, bundled `STCharacters.txt` | ✅ Pass | Call sites unchanged this round, carrying forward rounds 1-3's official verification. New sanity assertion passes against the real 170-character derivation. |
| langchain-google-genai | 4.3.3 | `thinking_level` alias via `init_chat_model` | ✅ Pass | Call site unchanged this round, carrying forward rounds 1-3's official verification. |

---

# Spec Conformance Round 4

> Reviewer: gpt-5.6-sol | Date: 2026-09-04

## Summary

| Metric | Count |
|--------|-------|
| Total findings (new, this round) | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | SP-1.1 | Dismissed (user decision) | Not re-evaluated; DEV-206 run-path-caller scope boundary still valid. |
| 2 | SP-1.2 | ✅ Fixed | 170-character dual-status set, 15% ratio, and absolute floor of 3 all still present; legitimate Taiwan-Traditional cases pass, substantially-Simplified responses fail — matches the authorized tolerant language policy. |
| 3 | SP-1.3 | ✅ Fixed | zh row 19 still points to Finnhub; en/zh ids 1-30 and categorical fields consistent; full curation + the one anomaly's record still preserved in `fix-round-1.md`. |
| 4 | SP-1.4 | ✅ Fixed | No `test_real_split_proposal*` or equivalent real-allocation assertions found; unit tests still only use synthetic sidecars. |
| 5 | SP-2.1 | ✅ Fixed | `SplitSidecar.status` still gates holdout/reserve opt-in; `"proposed"` cannot unlock, only `"frozen"` can. |
| 6 | SP-3.1 | ✅ Fixed | `README.md` L39-44 explicitly records the `boundary` × `may_pass_with_tuning` dev+1/reserve-1 adjustment, the per-stratum rounding shortfall, and the reasoning for choosing that stratum to absorb it — content matches the actual allocation. |

## Findings (new only)

None.

## Covered Requirements

✅ `ModelConfig` reasoning strength correctly maps to OpenAI `reasoning.effort` and Gemini `thinking_level`.
✅ `ProfileConfigLoader.load_from_dir()` loads from an arbitrary directory; shared prompt only injects via explicit `prompt_path`.
✅ All 4 benchmark configs (Luna none/medium, Gemini minimal/medium) load successfully via the current schema with correct provider, effort, and canonical prompt.
✅ `response_no_simplified_chars` is a deterministic pure scorer, wired into `language_policy`, judging substantially-wrong-language per the authorized policy rather than character-perfect purity.
✅ Split sidecar defaults to dev-only; holdout/reserve are independent explicit opt-ins gated by `status: "frozen"`.
✅ zh dataset curation complete; row 19 anomaly corrected with a committed audit record.
✅ Split proposal still dev 8/holdout 16/reserve 6; 30 unique ids fully covering 1-30; row 5 in holdout; en/zh twin rule unchanged.
✅ `split.json` still holds round 2's approved 9-key shape; round 3's delta didn't touch this file.
✅ Manual-adjustment reasoning is back on the current human split-review surface, matching the actual band × behavior stratification data.
✅ DEV-205 still stops at the human split-review gate; prompt evolution, cross-model checking, and the actual freeze remain DEV-206 scope, not pulled forward.
✅ `ruff check`/`ruff format --check` both pass; full test record at this HEAD is 1376 passed, 61 deselected.

---

Both axes: zero new findings, all prior-round items confirmed still holding with no
regressions. Per the skill's decision tree (Step 2), this ends the review-fix cycle —
proceeding to Step 4 Final Verification.
