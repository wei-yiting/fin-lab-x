# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-09-03
>
> (`gpt-5.6-sol` and `2026-09-03` are already substituted by the orchestrator with the
> actual model slug and date. Copy them into your output verbatim — do not
> replace them with your own self-identification such as "GPT-5" or "Claude".)

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 8 |
| Blocking | 0 |
| Major | 4 |
| Minor | 3 |
| Suggestion | 1 |
| Library checks | 2 |

## Issues

### [Major] M-1.1: OpenCC conversion is not a valid Simplified-character classifier
- **File:** `backend/evals/scenarios/language_policy/scorer.py` L110
- **Problem:** Comparing `OpenCC("s2t").convert(response)` with the original response produces false failures for valid Taiwanese Traditional Chinese. For example, OpenCC converts `台灣`, `台積電`, and `平台` to `臺灣`, `臺積電`, and `平臺`. These are variant normalizations, not evidence that the input contains Simplified Chinese. The docstring's claim that this "never flags valid Traditional text" is therefore false. A normal TSMC answer can score zero, undermining measurement trust in the production-grade eval zone (`docs/design-envelope.md` §4 and §5).
- **Fix:** Replace conversion equality with a detector for unambiguously Simplified-only forms, calibrated against representative Taiwanese Traditional text. Add regression cases for `台灣`, `台積電`, `平台`, and other accepted variants alongside genuine Simplified contamination cases.
- **Context7:** Constructing one `OpenCC("s2t")` instance and reusing `convert()` is the recommended API pattern. The API usage is current; the defect is treating conversion output as a purity classification.

### [Major] M-1.2: The dev-only split guard is not wired into the eval run path
- **File:** `backend/evals/diagnostic/row_selection.py` L15
- **Problem:** The module explicitly admits that nothing in the run path calls `load_split_sidecar()` or `apply_split()`. `eval_runner.run_scenario()` still calls `select_diagnostic_rows()`, whose default returns the complete diagnostic dataset. Consequently, the advertised dev-only default does not exist operationally, and a normal benchmark invocation can expose holdout and reserve rows. This violates the eval measurement-rigor requirement in §4 and the reachability rule in §0.
- **Fix:** Wire the benchmark sidecar into the diagnostic runner before permitting benchmark execution. Default to `dev`; require explicit holdout/reserve options. If that wiring belongs to a later change, defer these guard APIs rather than shipping unreachable protection that callers can incorrectly assume is active.

### [Major] M-1.3: Benchmark configurations have no executable consumer
- **File:** `backend/agent_engine/agents/config_loader.py` L147
- **Problem:** `load_from_dir()` is referenced only by tests and documentation. The actual eval task still calls `ProfileConfigLoader(profile).load()`, which only resolves product profiles under `profiles/`. None of the four benchmark configurations can be selected through the runner. This is dead infrastructure and speculative generality under `docs/design-envelope.md` §0; being intended for the next ticket is explicitly insufficient under the reachability rule.
- **Fix:** Add the narrow execution seam that loads a benchmark config directory together with its canonical prompt, or postpone `load_from_dir()` and the candidate configs until that consumer ships. Do not retain a "reachable soon" exception in source comments.

### [Major] M-1.4: Session-local candidate identifiers are embedded throughout permanent artifacts
- **File:** `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/README.md` L11
- **Problem:** `C1`–`C4` appear in directory names, config names, descriptions, tests, and documentation. These ordinal identifiers carry no meaning beyond the plan that produced them; the descriptive suffixes already contain the durable identity. This is the prohibited process-identifier pattern and adds needless rename pressure if the matrix changes.
- **Fix:** Rename the configurations to descriptive identities such as `luna_none`, `luna_medium`, `gemini_minimal`, and `gemini_medium`. Remove `C1`–`C4` from config names, descriptions, tests, and documentation.

### [Minor] m-1.1: Issue IDs are retained in code and benchmark data
- **File:** `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/split.json` L20
- **Problem:** `DEV-200` and `DEV-200/205` are embedded in the split rationale, configuration descriptions, and test comments. The surrounding text already states the actual rule, so the ticket references add no durable explanation.
- **Fix:** Remove the issue IDs and retain the descriptive rationale. Keep issue references in commit, PR, and Linear metadata.

### [Minor] m-1.2: Split sidecar validation stops at the outer list shape
- **File:** `backend/evals/diagnostic/row_selection.py` L108
- **Problem:** The loader verifies that each tier is a list but does not verify that every row ID is a non-empty string. Integers are accepted until a later mismatch, empty strings pass silently, and unhashable entries fail with an incidental `TypeError` in `_find_duplicates()`. This is weak boundary validation for data controlling an eval split (`docs/design-envelope.md` §4).
- **Fix:** Validate that the JSON root is a mapping and every tier contains only non-empty, trimmed strings before duplicate detection. Raise an actionable `ValueError` identifying the tier and invalid value. Add malformed-element tests.

### [Minor] m-1.3: Empty reasoning effort silently becomes OpenAI medium
- **File:** `backend/agent_engine/agents/base.py` L217
- **Problem:** `reasoning_effort=""` passes `ModelConfig` validation but `config.reasoning_effort or "medium"` silently converts it to `medium`. A malformed benchmark configuration can therefore run a different arm than declared instead of failing. That weakens reproducibility in the §4 eval zone.
- **Fix:** Validate `reasoning_effort` as a non-empty, trimmed string and distinguish `None` explicitly: use the default only when the value is `None`.

### [Suggestion] S-1.1: Configuration parsing logic is duplicated
- **File:** `backend/agent_engine/agents/config_loader.py` L172
- **Suggestion:** `load()` and `load_from_dir()` independently open the same YAML file, optionally inject prompt text, and instantiate `WorkflowProfileConfig`. This is possible Duplicated Code. Move the shared parsing into one small private function while leaving sibling-prompt discovery versus explicit injection at the public entry points.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None. The benchmark folder has an adequate scope and structure README. |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| opencc-python-reimplemented | 0.1.7 | `OpenCC("s2t")`, cached instance, `convert()` | ✅ Current | Construction and reuse match the documented pattern. Conversion equality is semantically unsuitable as a purity classifier; see M-1.1. |
| langchain-google-genai | 4.3.3 | `thinking_level` through `init_chat_model()` | ✅ Current | Installed source confirms `thinking_level` is the alias for `reasoning_effort`. With the current `thinking_budget=None`, no both-set warning is produced; if both are non-null, `thinking_level` wins and the budget is discarded. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-09-03
> (Copy `gpt-5.6-sol` and `2026-09-03` verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 4 |
| Missing | 1 |
| Scope creep | 1 |
| Misimplemented | 2 |

## Findings

### [Blocking] SP-1.1: Split guard 未接入 diagnostic row-selection seam
- **Type:** Missing
- **Spec:** "Split sidecar 格式定案，diagnostic row selection 讀取它且預設只允許 dev rows；holdout/reserve 需明確 opt-in（unit test 於 row selection seam）" (DEV-205 acceptance criteria)
- **File:** `backend/evals/diagnostic/row_selection.py` L51
- **Problem:** `select_diagnostic_rows()` 未讀取或套用 sidecar，沒有指定 `row_ids` 時仍直接回傳完整 dataset。實際 `eval_runner` 只呼叫這個函式，因此目前執行 owning diagnostic scenario 會包含 dev、holdout、reserve 全部 rows。新增的 `load_split_sidecar()` 與 `apply_split()` 沒有任何 run-path caller；模組 docstring 也明確承認尚未 wiring，故防洩漏 guard 並未生效。
- **Fix:** 將 sidecar 納入實際 diagnostic selection seam：benchmark scenario 預設載入 sidecar 並只選 dev，holdout/reserve 必須透過各自明確 opt-in 才能加入；測試應走與 `eval_runner` 相同的公開 selection path，證明預設 run 不會碰到 holdout/reserve。

### [Blocking] SP-1.2: Scorer 將合法台灣繁中誤判為簡體
- **Type:** Misimplemented
- **Spec:** "簡繁純度 scorer（純函式）掛進 language_policy scenario：繁中回答含簡體字 → 0（unit test 於 scorer seam）" (DEV-205 acceptance criteria)
- **File:** `backend/evals/scenarios/language_policy/scorer.py` L110
- **Problem:** 以 `OpenCC("s2t").convert(response) == response` 判定純度，會把 OpenCC 的字形／地區用字正規化也當成簡體污染。例如完全合法且常見的台灣繁中「台灣市場目前仍有不確定性」會因 `台 → 臺` 得到 0。這不是「含簡體字」，造成 deterministic scorer false positive。
- **Fix:** 改用能區分「簡體專屬字」與合法繁中字形／台灣慣用字的判定方式；至少加入「台灣」等合法繁中 regression case，並保留全簡體及局部簡體污染得 0 的測試。

### [Blocking] SP-1.3: zh curation 漏掉已存在的翻譯／指涉異常
- **Type:** Misimplemented
- **Spec:** "zh dataset 30 rows 的 curation 欄位一致性過查完成，異常記錄在案" (DEV-205 acceptance criteria)
- **File:** `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/split.json` L32
- **Problem:** `curation_pass` 宣稱 `0 anomalies`，但 row 19 的英文 rationale 指定「current Finnhub indicators」，zh rationale 卻改為「現有 yfinance 指標」，而同 row 的 `expected_best_source` 仍是 `Finnhub`。這改變了 source 指涉，且證明目前只比對 categorical columns、未實際完成 spec 要求的翻譯語意過查。
- **Fix:** 將 row 19 zh rationale 修正為 Finnhub，記錄此 anomaly；重新逐 row 檢查四個翻譯欄位是否改變題目難度、source 或公司指涉，再更新 `curation_pass` 的 method/result。

### [Minor] SP-1.4: Split 實際提案驗證被放進 unit tests
- **Type:** Scope creep
- **Spec:** "split 實際分配屬人審 gate 驗證，不進 unit test。" (DEV-205 Testing decisions)
- **File:** `backend/tests/evals/test_diagnostic_row_selection.py` L201
- **Problem:** `test_real_split_proposal_*` 直接載入實際 `split.json`，並對 proposal 的 counts、完整涵蓋及 row 5 tier 歸屬做 unit-test assertions，與明訂由 human split-review gate 驗證、不進 unit test 的邊界相反。
- **Fix:** 移除針對實際 proposal allocation 的 unit tests；保留以 synthetic sidecar 驗證 loader、dev-only default、opt-in 與 integrity guard 的 row-selection seam tests，實際 split 分配留給 human gate。

## Covered Requirements

✅ `ModelConfig` 可表達 OpenAI `reasoning.effort` 與 Gemini `thinking_level`，四組實際 mapping 分別為 Luna `none`/`medium`、Gemini `minimal`/`medium` — `backend/agent_engine/agents/base.py`

✅ Profile config 可由指定目錄載入，shared prompt 由 `prompt_path` 明確注入，config 子目錄沒有 prompt 複本 — `backend/agent_engine/agents/config_loader.py`

✅ 四個 benchmark configs 位於 owning scenario，皆可通過既有 profile schema 載入 — `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/configs/`

✅ Shared prompt 是 baseline profile prompt 的 byte-identical seed，符合 DEV-205/DEV-206 scope boundary — `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/prompt/system_prompt.md`

✅ Split proposal 為 dev 8 / holdout 16 / reserve 6，主分層比例、次要 category/time_sensitivity 平衡、row 5 holdout、en/zh twin rule 與人工微調理由均有記錄 — `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/split.json`

✅ Backend files 通過 `ruff format --check --no-cache backend/` — `backend/`

---

## Discussion Gate Resolution (Round 1)

Orchestrator vetted every finding against actual code/data before this discussion (grep for
callers, direct OpenCC testing, direct CSV inspection, fetched DEV-206's full description).
Resolutions below are the user's decisions.

| ID | Resolution | Notes |
|---|---|---|
| M-1.1 / SP-1.2 (same bug) | **Fix as suggested** | Undisputed. Orchestrator independently reproduced: OpenCC `s2t` conversion touches `台灣`→`臺灣`, `台積電`→`臺積電`, `平台`→`平臺` — all legitimate, common Taiwan-standard Traditional Chinese. Scorer needs a real Simplified-only detector, not conversion-equality. |
| M-1.2 / SP-1.1 / M-1.3 (same root cause: split guard, `load_from_dir()`, and the 4 configs have zero production callers) | **Dismissed (user decision) — no fix, keep as-is** | User asked whether DEV-206 actually consumes these. Orchestrator fetched DEV-206's full description: its "Blocked by" line literally reads "DEV-205 — 需要 config 載入、scorers、split guard 與已核准的 split" (needs config loading, scorers, split guard, and the approved split), and DEV-206's own work (dev-set × 4-config validation cycles) structurally requires exactly this code. This is a concrete, already-ticketed next consumer via a real `Blocked by` relation — not the "might be useful someday" pattern design-envelope §0 targets. Also: since `load_from_dir()` has no execution entry point either, there is no way to accidentally run a benchmark against holdout/reserve today — the "leakage risk" the guard exists for cannot yet occur. Reviewer/spec findings were accurate on the fact (zero callers); disposition is: build now, DEV-206 wires and exercises it. |
| M-1.4 (C1–C4 process identifiers) | **Fix with modified direction** | User overrode orchestrator's partial defense and sided with the reviewer: rename using actual model identity. Renaming `c1_luna_none`/`c2_luna_medium`/`c3_gemini_minimal`/`c4_gemini_medium` → `luna_none`/`luna_medium`/`gemini_minimal`/`gemini_medium` everywhere (directories, YAML `name:` + `description:` fields, test parametrize strings, README), dropping the `C1`–`C4` ordinal prefix entirely. |
| SP-1.3 | **Fix as suggested, scope (b)** | User chose the fuller option: re-check all 30 rows' free-text columns (question, expected_answer_type, why_baseline_might_fail_or_pass, draft_pass_signals), not just row 19. Orchestrator performed this check directly — row 19 (Finnhub→yfinance) is the only anomaly found across all 30 rows; everything else is faithful, idiomatic translation. Fix: correct row 19's zh rationale to Finnhub, record the anomaly, update `curation_pass.method`/`result` to reflect that free-text columns were manually reviewed (1 anomaly, now fixed) in addition to the existing categorical-column pass. |
| SP-1.4 | **Fix as suggested** | Undisputed — diff's own testing decision text explicitly excludes this. |
| m-1.1 | **Fix as suggested** | Undisputed, matches existing tolerated-Minor convention. |
| m-1.2 | **Fix as suggested** | Undisputed. |
| m-1.3 | **Fix as suggested** | Undisputed. |
| S-1.1 | **Fix as suggested** | User confirmed — low cost, do it now. |

**Final fix list for round 1 fixer:** M-1.1/SP-1.2, M-1.4, SP-1.3, SP-1.4, m-1.1, m-1.2, m-1.3, S-1.1.
**Excluded (dismissed):** M-1.2, SP-1.1, M-1.3.
