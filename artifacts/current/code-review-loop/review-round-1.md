# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-04
> (Copy these values verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 5 |
| Blocking | 0 |
| Major | 4 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 2 |

## Issues

### [Major] M-1.1: Regression gate fields 在 merge 時沒有 consumer
- File: backend/evals/eval_spec_schema.py L24
- Problem: `gate`、`metric_floor` 與 `ScenarioConfig.regression` 新增了強制 config surface，但目前沒有 runtime code 讀取它們。`eval_runner.py` 仍將所有 scorers 送進 `resolve_scorers()`，不套用 gate membership、floor 或 verdict。ADR-0006 L11、L73 又明確把 consumer 延至 DEV-118。這違反 design-envelope §0 Reachability、§3 Speculative Generality，以及 §7 對 consumer-less schema fields 的 Major severity floor。
- Fix: 在 gate evaluator 能一起完成前移除這些 fields 與 YAML blocks；或在本 changeset 納入最小可用的 consumer 與 verdict path。記錄未來 consumer 不符合 reachability。

### [Major] M-1.2: Rubric resolution 繞過並破壞 ScorerConfig invariant
- File: backend/evals/eval_spec_schema.py L195
- Problem: `model_copy(update={"rubric": ...})` 不執行 validation，因此回傳同時具有 `rubric` 與 `rubric_file` 的 `ScorerConfig`，但 `validate_mode()` L75 明確拒絕這個狀態。將 loader 結果 dump 後重新 validation 會失敗；也就是 loader 回傳了不符合自身 schema 的 object。
- Fix: 讀取檔案後，以 `rubric` 建立新的、經 validation 的 runtime `ScorerConfig`，並移除 input-only 的 `rubric_file`；再重新 validation `ScenarioConfig`。不要使用 `model_copy` 保留兩個 mutually exclusive fields。
- Context7: Pydantic v2 官方文件指出 `model_copy(update=...)` 直接套用 update，不會 validation，不能當成 validated mutation API。

### [Major] M-1.3: 未校準的 LLM judge 被宣告為可信任 gate
- File: backend/evals/scenarios/on_target_company/eval_spec.yaml L15
- Problem: 本次修改實質改寫並重新命名 judge criterion，隨即將 scenario 設為 `regression.enabled: true`、使用預設 1.0 floor。Dataset 沒有 human labels 或正反 calibration examples；README L31 也明確承認尚未以 human-labeled ground truth 驗證。design-envelope §4 要求 LLM judge 上線時提供每個 dimension 的 TPR/TNR，§7 將此區的 shortcut 定為 Major。
- Fix: 先以 human-labeled on-target/off-target outputs 校準 rubric 並記錄 TPR/TNR。若本 slice 無法完成，應延後整個 judge/scenario，而不是把未校準 judge 納入可執行的 eval assets。

### [Major] M-1.4: ADR-0006 超出 ADR contract 約九倍
- File: docs/adr/0006-explicit-regression-gate-declaration.md L1
- Problem: 新 ADR 共 901 words；design-envelope §4 規定每個 ADR 僅記錄一項 decision，且不得超過 100 words。ADR 本身屬 Production-Grade Zone，因此依 §7 為 Major。大量 future-ticket procedure 與 lifecycle commentary 也掩蓋了 durable decision。
- Fix: 壓縮成不超過 100 words 的 decision、rejected alternatives 與 why。DEV ticket ownership、執行程序及詳細 consequences 應留在 Linear 或 planning/operator documentation。

### [Minor] m-1.1: 公開的 eval-spec schema 現在會產生無效 YAML
- File: backend/evals/README.md L138
- Problem: 標示為「Full schema」的範例仍在 L165 指示使用 inline `rubric:`，但新 loader 會拒絕它；文件也缺少必要的 `regression`、`rubric_file`、`gate`、`metric_floor`，scenario structure map 則沒有 `on_target_company`。照著主要 contributor 文件操作會直接得到 load error。
- Fix: 同步更新 schema example 與 scenario structure map，說明 file-only rubric contract、required regression declaration 及 scorer gate defaults。

## Documentation Gaps

| Folder | Missing |
|--------|---------|

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| pydantic | 2.12.5 | `Field`, `model_fields_set`, `@model_validator(mode="after")`, `model_copy(update=...)` | ❌ Wrong | Field constraints、validator ordering 與 explicit-field detection 均為 current API；rubric resolution 則以未驗證的 `model_copy` 建立自身 validator 禁止的狀態。 |
| autoevals | 0.1.0 | `Score(name=..., score=...)`; scorer returns `Score \| None` | ✅ Current | Scores 均在 0–1；未宣告 expected tool 時回傳 `None`，符合 framework 的 no-score contract。 |
---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-04

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 1 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 1 |

## Findings

### [Blocking] SP-1.1: rubric_file accepts absolute paths
- **Type:** Misimplemented
- **Spec:** "llm_judge rubric file-only: `rubric_file` required (path relative to scenario dir; missing file → load error); inline `rubric` in YAML → error with guidance to use rubric_file. Loader reads the file and populates the internal rubric field; engine still consumes config.rubric unchanged." (DEV-117 §1 Schema)
- **File:** `backend/evals/eval_spec_schema.py` L188
- **Problem:** `config_path.parent / scorer.rubric_file` accepts an absolute `rubric_file`; `pathlib` discards `config_path.parent` when the right operand is absolute. A scenario can therefore load a rubric that is not expressed relative to its scenario directory, contrary to the binding path contract.
- **Fix:** Reject absolute `rubric_file` values before joining them to `config_path.parent`, and add a `load_scenario_config` test proving an absolute path produces a load error.

## Covered Requirements

(22 requirements confirmed — full list in orchestrator transcript; all spec items verified present except SP-1.1 above. Notables: regression required incl. drafts; gate/metric_floor defaults and dead-config rejection; inline-rubric rejection with guidance; missing-file error and rubric hydration; engine untouched; expected_tool_called three paths bare-None; language_policy three defaulted scorers, response_relevance removed; sec_retrieval enabled:false + DEV-103 rationale, README untouched; on_target_company spec/rubric/dataset/README incl. provenance and calibration-debt note; schema/scorer/real-asset test coverage; no out-of-scope items.)
