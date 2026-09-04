# Code Review Round 3 (Quality axis — INCOMPLETE, see note)

> Reviewer: gpt-5.6-sol | Date: 2026-09-04

**Note on this round's process:** The Codex quality-axis run for round 3 hit a series of
infrastructure failures — a 10-minute internal timeout killed the underlying process
without letting the companion script mark itself finished, leaving a stale job lock that
rejected every resume/fresh-start attempt for the next two tries. On the third attempt
the job (`task-mtm8djza-l9k8hd`, Codex session `01a069df-19f5-7cd3-a94a-440ee834fddc`)
was confirmed genuinely running via `/codex:status` (37m23s elapsed, phase "verifying"),
so the orchestrator switched to reading its live log file directly
(`.../jobs/task-mtm8djza-l9k8hd.log`, readable on local disk) rather than continuing to
relay through the subagent. The log showed steady progress (a new command every 10-40s)
through 2026-09-04T00:53:05Z, then went silent for 99 minutes with no further activity —
inconsistent with the established cadence, indicating a genuine hang rather than continued
work. The user cancelled the job via `/codex:cancel`. No final formatted report was ever
produced. The three findings below are real, individually verified by the orchestrator —
extracted directly from the job's log before cancellation, not reconstructed or guessed.
This round's quality axis should be considered a partial pass; a supplementary pass can be
run later if the user wants fuller coverage.

## Findings (extracted from the interrupted run, each independently verified)

### [Minor] M-3.1: Round-2 process-identifier labels leaked into a permanent test docstring
- **File:** `backend/tests/evals/test_language_policy_scorer.py` L204-208
- **Problem:** `test_other_dual_status_characters_score_one`'s docstring reads "Round-2
  counter-examples: the round-1 fix hardcoded only 台, but ... false-positived under the
  round-1 fix. The systematically-derived 170-character dual-status set (Part A) must
  cover all of these..." — "Round-2"/"round-1"/"Part A" are labels from this review loop's
  own internal round-numbering and the orchestrator's round-2 fixer prompt structure (which
  literally named the two halves of that issue "Part A"/"Part B"). Same category of issue
  as round 1's m-1.1 and round 2's M-2.2, reintroduced by the round-2 fixer while it was
  fixing other instances of exactly this pattern.
- **Fix:** Reword without round numbers or "Part A" — describe what the test verifies
  directly (e.g. "the systematically-derived dual-status set, not just 台, must cover
  characters like 干/布/占/范").
- **Orchestrator verification:** confirmed via direct `grep` — text is present exactly as
  quoted.

### [Major] M-3.2: A wholly-Simplified response can still score 1.0 under the 15% ratio threshold
- **File:** `backend/evals/scenarios/language_policy/scorer.py`, `response_no_simplified_chars`
- **Problem:** Codex's log: "一段自然、完整使用簡體的金融分析句子，因可區分字形只占 10.8%，
  目前 scorer 仍回傳 `1.0`。這不是「偶爾夾兩個簡體字」的容忍案例，而是整句語言判斷失敗" (a
  natural, wholly-Simplified financial-analysis sentence, because its distinguishable
  glyphs are only 10.8%, still returns 1.0 — not the "occasional mistake" tolerance case,
  a genuine whole-sentence language-judgment failure). The exact sentence wasn't captured
  before the job was cancelled, but the underlying structural risk is real and independently
  reproduced: many common financial/casual Chinese multi-character words (股票, 成交量, 信心,
  昨天, 不少, etc.) are identical in Simplified and Traditional — a genuinely-Simplified
  response that happens to lean on this vocabulary can have a low measured ratio despite
  being unambiguously written in the wrong script. Orchestrator reproduced a related case
  (a 29-CJK-character wholly-Simplified sentence measuring 17.2% under the *correct*
  CJK-scoped calculation — still above 15%, so not itself a counter-example, but confirms
  the ratio can get uncomfortably close with ordinary vocabulary choices, not just
  contrived ones).
- **Fix (discussed and agreed with the user, not yet implemented):** add an absolute-count
  floor alongside the ratio: fail if `genuine_changes > 3`, **regardless of ratio**, in
  addition to the existing `ratio > 0.15` condition (i.e. fail if either condition is met).
  Orchestrator verified this hybrid rule against every test case accumulated across all
  three rounds (legitimate dual-status-heavy Traditional text, the single-diluted-mistake
  case, several wholly-Simplified samples) — all classify correctly.
- **Orchestrator verification:** structural risk independently confirmed via direct
  testing; exact 10.8% sentence not recovered (job cancelled before it could be extracted
  from the log), but Codex's own log states it tested this against the live scorer logic,
  not a hand estimate.

### [Major] M-3.3: The dual-status derivation doesn't actually fail loud on malformed data
- **File:** `backend/evals/scenarios/language_policy/scorer.py`, `_load_dual_status_traditional_chars`
- **Problem:** Codex's log: "私有 dictionary 路徑本身在 pinned 0.1.7 wheel 中可用，但其
  parser 對空檔／格式漂移會靜默回傳空集合，沒有修正報告所稱的 fail-loud" (the private
  dictionary path works under the pinned 0.1.7 wheel, but its parser silently returns an
  empty set on an empty file or format drift — not the fail-loud behavior the fix report
  claimed). Orchestrator confirmed by re-reading the function: if `STCharacters.txt` exists
  but is empty (or every line fails the self-referential check), the `for line in f` loop
  simply never adds anything, and the function returns `frozenset()` with no exception —
  contradicting the round-2 fixer instruction to "fail loudly at import time" if the
  derivation is broken. The round-2 fix report's "verify `len() == 170`" step was a
  one-time manual check during that fix session, not a standing runtime guarantee — nothing
  in the shipped code re-checks this on every import.
- **Fix:** Add a runtime sanity assertion immediately after computing
  `_DUAL_STATUS_TRADITIONAL_CHARS` (e.g. `assert len(_DUAL_STATUS_TRADITIONAL_CHARS) > 100,
  f"expected ~170 dual-status characters, derived only {len(...)} — STCharacters.txt may be
  empty or its format may have changed"`) so a broken derivation fails at import time
  instead of silently shipping an empty (or partial) exclusion set.
- **Orchestrator verification:** confirmed via direct code reading — the loop has no
  fallback/assertion path.

## Official Standards Check

Not completed — the run was cancelled before reaching this section.

---

# Spec Conformance Round 3

> Reviewer: gpt-5.6-sol | Date: 2026-09-04
> (Copy verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total findings (new, this round) | 1 |
| Missing | 1 |
| Scope creep | 0 |
| Misimplemented | 0 |

唯一新 finding 是 split 的人工微調理由已從目前 human-review surface 消失。其餘 Round 2 findings 均已修復。

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | SP-1.1 | Dismissed (user decision) | Not re-evaluated |
| 2 | SP-1.2 | ✅ Fixed | 實際呼叫 scorer：政府干預市場、公司公布財報、市占率保持穩定、范先生、台積電／台灣均為 1.0；一般簡體財務回答及既有全簡體 Tesla／TSMC cases 均為 0.0。derived exclusion set 為 170 characters，包含台/干/布/占/范。符合授權後的「偵測實質使用錯誤語言」政策。 |
| 3 | SP-1.3 | ✅ Fixed | zh row 19 仍為 Finnhub；30 個 en/zh IDs、所有 categorical fields 均一致，重新逐對檢視 30 rows 的四個 free-text fields 未發現其他語意漂移。移除 `curation_pass` 未造成新 gap：`fix-round-1.md` 明確記錄完整過查範圍、唯一 anomaly 及修正內容；此類歷史 audit record 不必與 runtime sidecar co-locate。 |
| 4 | SP-1.4 | ✅ Fixed | Repo search 未找到 `test_real_split_proposal*` 或等價的實際 proposal allocation assertions；僅保留 synthetic sidecar behavior tests。 |
| 5 | SP-2.1 | ✅ Fixed | `SplitSidecar.status` 已實作；實際 `split.json` 為 proposed。直接執行確認 default 只回傳 8 dev rows；holdout/reserve 三種 opt-in 均拋出 ValueError；改用 frozen sidecar 後才分別允許 24、14、30 rows。 |

## Findings (new)

### [Blocking] SP-3.1: Split proposal 缺少人工微調理由的現行 review record
- **Type:** Missing
- **Spec:** "Split 提案：...人工微調理由記錄 — 交人 review" (DEV-205 acceptance criterion)
- **File:** `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/README.md` L29
- **Problem:** 現行 `split.json` 只保留 counts 與 assignments；README 只保留 en/zh twin rule 及 row 5 強制進 holdout 的理由。原本 `boundary × may_pass_with_tuning` stratum 的 `dev +1 / reserve -1` 人工調整及 rounding 理由已完全離開目前的 split-review surface。與 curation audit 不同：manual adjustment rationale 是尚待進行之 split approval gate 的決策輸入，而非已結案的 QA 記錄。
- **Fix:** 維持精簡的 9-key JSON；在 README 的 split notes 補回簡潔、永久的 review rationale：指出 `boundary × may_pass_with_tuning` 從 reserve 移一列至 dev，以及獨立按 stratum rounding 會得到不足的 dev／過多的 reserve、此調整以最小 remainder distortion 達成 8/16/6。無須恢復 seed-search 等非決策性過程細節。

## Covered Requirements

✅ ModelConfig 能表達 OpenAI reasoning.effort 與 Gemini thinking_level — `base.py`, `config_loader.py`
✅ Config 可從指定目錄載入，shared prompt 由載入端明確注入 — `config_loader.py`
✅ 四個 benchmark configs 均通過 schema 載入 — `benchmark/configs/`
✅ 簡繁 scorer 為 deterministic pure scorer、已掛入 language_policy scenario，且能攔截實質簡體回答 — `scorer.py`, `eval_spec.yaml`（純度判斷的可靠性仍受 M-3.2 約束）
✅ Split sidecar 提供 dev-only default、per-tier explicit opt-in 與 frozen status gate — `row_selection.py`
✅ zh dataset 30 rows 一致性過查完成，row 19 anomaly 已修正且留有 committed audit record — `dataset.csv`, `fix-round-1.md`
✅ Split assignments 仍為 dev 8／holdout 16／reserve 6、完整涵蓋 IDs 1–30、row 5 在 holdout、en/zh twin rule 未變 — `split.json`, `README.md`
✅ ruff format/check 通過；相關 targeted tests 41 passed；full collection 1375/1436（61 deselected，符合 tracked round 2 verification）
