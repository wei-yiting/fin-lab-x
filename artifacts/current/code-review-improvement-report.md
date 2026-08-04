# Code Review Improvement Report

> **Task:** DEV-117 — Scenario 層 gate 契約（regression 區塊 schema + expected_tool_called + on_target_company 拆分）
> **Date:** 2026-08-04
> **Rounds:** 2
> **Reviewer model:** gpt-5.6-sol（Codex，兩軸皆是——本 loop 依使用者指示 Spec 軸也由 Codex 執行）
> **Fixer model:** claude-fable-5

## 架構影響摘要

- **`rubric` / `rubric_file` 的互斥從 model invariant 降級為 input-boundary 規則**（M-1.2）：載入後的 `ScorerConfig` 合法地同時持有兩者（`rubric_file` = provenance、`rubric` = 引擎消費的字串），spec 檔的 file-only 契約由 `_reject_inline_rubrics` 在 YAML 邊界獨力把守。載入結果現在可以 round-trip 過自己的 schema。
- **`rubric_file` 路徑契約收緊**（SP-1.1）：絕對路徑在載入時直接報錯，rubric 只可能存在於 scenario 目錄底下。
- **ADR 改號 0006 → 0008**：與 main 上 DEV-102 的 ADR 撞號（orchestrator 發現，兩位 reviewer 均未抓到）；內文 901 → 249 字。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 2 |
| 發現 issues 總數 | 6（quality 5 + spec 1） |
| Blocking | 1/1 fixed（SP-1.1） |
| Major | 3/4 fixed、1 declined（M-1.1） |
| Minor | 1/1 fixed |
| Suggestion | 0/0 |
| Spec findings (SP-) | 1/1 fixed |
| 文件修正 | 2（ADR 縮寫改號、backend/evals/README schema 範例同步） |

## Spec Conformance（Spec 軸）

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Misimplemented | "rubric_file required (path relative to scenario dir)"（DEV-117 §1 Schema） | Fixed（round 2 確認） |

其餘 22 項 requirements 於 round 1 全數確認 covered；round 2 確認修復未破壞任何已覆蓋項（regression 必填、預設值、引擎零改動均維持）。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `docs/adr/0008-explicit-regression-gate-declaration.md` | Gate 契約的決策記錄——先讀它，後面的 schema 都是它的實作 | ⚠️ |
| 2 | `CONTEXT.md` | Metric floor 詞條 + Regression Suite 改 metric 語彙 | |
| 3 | `backend/evals/eval_spec_schema.py` | 契約本體：RegressionConfig 必填、gate/metric_floor fail-safe 預設、rubric file-only 的兩層執法（YAML boundary + 載入解析） | ⚠️ |
| 4 | `backend/evals/scenarios/on_target_company/eval_spec.yaml` | 新 scenario 的 gate 宣告（enabled: true + 未校準注記）與 judge 定義 | ⚠️ |
| 5 | `backend/evals/scenarios/on_target_company/rubric.md` | 功能性判準的 rubric 本文 | |
| 6 | `backend/evals/scenarios/language_policy/scorer.py` | `expected_tool_called` 效度守衛（三徑純函式） | |
| 7 | `backend/evals/scenarios/language_policy/eval_spec.yaml`、`sec_retrieval/eval_spec.yaml` | 兩份既有 spec 的 gate 宣告 | |
| 8 | `backend/evals/scenarios/on_target_company/{dataset.csv,README.md}` | 種子 dataset（OTC-01…08）+ provenance/校準債記錄 | |
| 9 | `backend/evals/README.md` | Schema 範例同步（m-1.1 最小修正） | |
| 10 | `backend/tests/evals/*` | 三個 seam 的測試（載入函式 / scorer 簽名 / 真實資產 parametrize） | |

## 所有修正問題詳解

### SP-1.1（Blocking, Spec 軸）
- **問題：** `config_path.parent / scorer.rubric_file` 在 `rubric_file` 為絕對路徑時，pathlib 直接丟棄左運算元——rubric 可指向 scenario 目錄外的任意檔案，違反「相對於 scenario 目錄」的 spec 契約。
- **修法：** join 前先檢查 `Path(scorer.rubric_file).is_absolute()` → `ValueError`（訊息沿用 `Invalid scenario config in {path}:` 前綴）。
- **影響：** rubric 資產保證與 scenario 同居一處，diff review 與 DEV-96 汰換不會漏看外部檔案。
- **驗證：** 新測試 `test_llm_judge_absolute_rubric_file_fails`；`uv run pytest backend/tests/evals/ -q` 162 passed。

### M-1.2（Major, Quality 軸）
- **問題：** `model_copy(update={"rubric": ...})` 不觸發 validation（Pydantic v2 官方語義），loader 因此回傳同時設有 `rubric` 與 `rubric_file` 的物件——而 `validate_mode` 明文禁止該狀態。`model_validate(model_dump())` round-trip 會炸：loader 產出違反自身 schema 的物件。
- **修法：** 刪除 model 層的 both-set 禁令（連同其測試）；互斥只在 YAML 邊界執法（`_reject_inline_rubrics` 不變）；`model_copy` 呼叫點加 why-comment 說明繞過 validation 是刻意的；新增 round-trip 測試釘住契約。
- **影響：** 「載入態同時持有 provenance 與引擎字串」成為顯性契約而非 validator 漏洞；序列化/回放路徑（DEV-102 的 CSV 契約）不會踩雷。
- **驗證：** `test_loaded_config_round_trips_through_validation`；全 backend 882 passed。

### M-1.3（Major, Quality 軸——使用者裁定）
- **問題：** `on_target_company` 的 LLM judge 未經 human-labeled ground truth 校準（無 TPR/TNR），卻以 `enabled: true` + floor 1.0 進 gate（envelope §4 對 judge 的要求）。
- **修法（裁定）：** 維持 `enabled: true`；`regression` 區塊加顯性 YAML 注記「未量測 TPR/TNR、校準 labels 歸 DEV-96」。
- **影響：** 校準債在資產本體可見（不只在 README），DEV-96 開工時無需考古。
- **驗證：** Round 2 reviewer 確認注記存在且內容準確。

### M-1.4（Major, Quality 軸）
- **問題：** ADR 原文 901 字，envelope §4 規定 ≤100 字；另 orchestrator 發現編號 0006 與 main 上 DEV-102 的 ADR 撞號。
- **修法：** 改號 `0008`（code/test/文內引用同步），內文壓縮至 249 字（保留 Decision / Rejected / Why 骨架；ticket 程序性內容回歸 Linear）。100 字上限按 repo 案例法（0003–0007 均 223–636 字）未硬性執行——使用者裁定「concise 優先，可超過 100 字」。
- **影響：** ADR 編號序恢復唯一；決策文件密度對齊存量慣例。
- **驗證：** `ls docs/adr/` 無重號；`grep ADR-0006` 於本 branch 程式碼零殘留；162 eval 測試綠。

### m-1.1（Minor, Quality 軸）
- **問題：** `backend/evals/README.md` 的 "Full schema" 範例仍教 inline `rubric:`（新契約下直接 load error）、缺 `regression` 區塊與新欄位，structure map 無 on_target_company。
- **修法：** 最小同步：範例補 `regression.enabled`（含必填注記）、inline rubric 改 `rubric_file`、簡述 `gate`/`metric_floor` 預設、structure map 補 on_target_company。全面改寫仍歸 DEV-119。
- **影響：** 照主文件操作不再產生 load error。
- **驗證：** 人工比對範例與 schema；ruff format 通過。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `docs/adr/` | 0006 → 0008 改號 + 內文 901 → 249 字 |
| `backend/evals/README.md` | Schema 範例對齊新契約（最小 diff） |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Declined（M-1.1） | gate fields 在 merge 時無 consumer（envelope §0 Reachability） | 與 DEV-117/118 顯性拆票決策衝突；consumer 是被本票 block 的 DEV-118，ADR-0008 已載明 | DEV-118 實作 gate evaluator 時自然閉合 |
| Env 存量債 | ADR 0003–0007 均超過 envelope §4 的 100 字上限 | 存量 drift，非本 slice 範圍 | 若要執法：另開 docs issue 修訂條款或縮寫存量 |
| 校準債 | judge 無 TPR/TNR | 需 labeled dataset，歸 DEV-96 | DEV-96 產 labels 時一併量測 |

## Final Verification Results

### Code Level

- [x] Unit Tests: `uv run pytest backend/tests/ -q` → **882 passed, 49 deselected**
- [x] Lint: `uv run ruff check backend/` → All checks passed
- [x] Format: `uv run ruff format --check backend/` → 158 files already formatted

### Behavior Level

- [x] 三份真實 scenario spec 經 `load_scenario_config` 全數載入（parametrize 測試，含 on_target_company 真 rubric.md 解析與 hydration）
- [x] `expected_tool_called` 三徑行為（1.0 / 0.0 / None）由 7 個純函式測試證明
- [x] 載入態 round-trip（`model_validate(model_dump())`）通過

### Runtime / Observable Level

- [x] 無 BDD artifacts（bdd-scenarios.md / verification-plan.md 不存在）——本 slice 為 schema/資產層變更，行為驗證即上述載入層測試；judge 的 E2E 實跑依 spec 明文屬 DEV-96/DEV-120 後續（校準前分數不具意義），不在本票驗證範圍

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/evals/eval_spec_schema.py` | SP-1.1 絕對路徑拒絕；M-1.2 both-set validator 移除 + why-comment；ADR 引用改 0008 |
| `backend/evals/scenarios/on_target_company/eval_spec.yaml` | M-1.3 未校準注記 |
| `backend/evals/README.md` | m-1.1 schema 範例同步 |
| `docs/adr/0008-explicit-regression-gate-declaration.md` | M-1.4 改號 + 縮寫 |
| `backend/tests/evals/test_eval_spec_schema.py` | +2 測試（絕對路徑、round-trip）；ADR 引用同步 |
| `backend/tests/evals/test_language_policy_scorer.py` | −1 測試（both-set，前提失效） |
| `CONTEXT.md`、`backend/evals/scenarios/{language_policy,sec_retrieval}/*`、`on_target_company/{rubric.md,dataset.csv,README.md,__init__.py}` | Review 無修正（round 1 即通過） |

## Learning Notes

### 採用的工程策略

- **「互斥在輸入邊界、寬鬆在載入態」存活下來並被迫講清楚**（M-1.2）：grilling 時定的「YAML 拒 inline、載入後填 `rubric`」策略本身正確，但實作把互斥也放進 model validator，造成 loader 產物違反自身 schema。修正後的分層——YAML boundary 管 spec 作者、model 只管載入態合法性——是原策略的更精確表述。
- **拆票的 out-of-scope 決策需要可引用的落點**（M-1.1）：reviewer 按 envelope §0 抓「無 consumer 的 schema」完全合理；decline 之所以站得住，是因為 ADR-0008 把「contract 歸 DEV-117、verdict 歸 DEV-118」寫成了可引用的一句話。沒有那句話，這個 decline 就只是口頭約定。

### 權衡取捨

- **Expected**：briefing 階段認為 judge `enabled: true` + README 記債即可。**Actual**：兩個獨立 reviewer（Claude round、Codex round）都抓同一點，最終裁定是「開燈但債務注記上移到資產本體（YAML comment）」——債的位置比債的存在更關鍵，README 會被略過、spec 檔不會（M-1.3）。
- **條文 vs 案例法**（M-1.4）：envelope 的 100 字 ADR 上限與五份存量 ADR 的實態早已分歧。本輪選擇對齊案例法（249 字）而非條文，並把存量 drift 記為顯性未處理項——規則失效時，先承認再議，不假裝合規。

### 關鍵收穫

- **`pathlib` 的 `/` 是靜默的絕對路徑陷阱**（SP-1.1）：`base / user_path` 在 user_path 為絕對路徑時整個丟棄 base——任何「相對於某目錄」的路徑契約都必須顯性檢查 `is_absolute()`，join 本身不提供這個保證。
- **`model_copy(update=)` 是無驗證通道，用它就要對產物負全責**（M-1.2）：繞過 validation 的每一次使用，都隱含「產物仍須合法於自身 schema」的義務——round-trip 測試（`model_validate(model_dump())`）是把這個義務變成可執行斷言的最便宜手段。
- **Reviewer 的脈絡邊界決定 finding 的性質**（M-1.1）：quality 軸刻意 spec-blind，所以它對「拆票造成的暫態」必然誤報——這不是 reviewer 的缺陷，而是設計；orchestrator 的職責就是拿著 ticket 脈絡做 adjudication，而不是把脈絡塞給 reviewer 讓它自我審查。
