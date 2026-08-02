# Code Review Improvement Report

> **Task:** DEV-120 — LLM-judge scorer 全滅：judge client 顯式化（`fix/llm-judge-client-api-key`）
> **Date:** 2026-08-02
> **Rounds:** 3（Round 3 為 zero-issue 確認輪）
> **Reviewer model:** Quality 軸 gpt-5.5（Codex, read-only sandbox）／Spec 軸 claude-fable-5（read-only subagent）
> **Fixer model:** claude（code-fixer subagent，與 reviewer session 完全隔離）

## 架構影響摘要

- **Judge 的 endpoint 與憑證從「環境推斷」改為「程式碼顯式配置」。** `scorer_registry._build_judge_client()` 是全 repo 唯一建立 judge OpenAI client 的位置，endpoint 寫死、key 明確取自 `OPENAI_API_KEY`。往後要換 provider 或改走 gateway，只需動那一處的兩個值——決策與逃生門記於 ADR-0007。
- **`ScorerConfig` 的 scorer-mode 分界收緊為「有沒有寫」而非「值是不是預設」。** `temperature` 加入 programmatic／llm_judge 互斥驗證時，改用 `model_fields_set` 判斷欄位是否被提供，堵住「programmatic scorer 顯式寫 `temperature: 0` 也會通過」的漏洞（m-1.1）。
- **eval config 的錯誤偵測時機從 runtime 前移到 load time。** `temperature` 加上 `Field(ge=0.0, le=2.0, allow_inf_nan=False)`，超範圍值在 `load_scenario_config()` 就被擋下，而非等到該列 agent task 已花錢跑完、judge 呼叫 API 時才炸（M-2.1）。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 3 |
| 發現 issues 總數 | 5 |
| Blocking | 0/0 fixed |
| Major | 1/2 fixed（1 筆經人工裁決 accepted deviation） |
| Minor | 3/3 fixed |
| Suggestion | 0/0 adopted |
| Spec findings (SP-) | 0/0 — 零 findings |
| 文件修正 | 2 |

## Spec Conformance（Spec 軸）

Spec 軸無 findings — 需求覆蓋完整、無 scope creep。

Round 1 對照 DEV-120 spec 全文（D1–D6、四個測試案例、六條 AC、四項 out-of-scope）逐條查核，確認 D1–D6 全數落地、`eval_runner` 未被觸碰、out-of-scope 四項皆未滲入。兩個 judgement call 經檢視後判定非 creep：第五個測試（programmatic temperature 守衛）源自 D4 的「沿用既有互斥驗證」、`_JUDGE_BASE_URL` 常數是 D2 寫死 endpoint 的封裝。

Round 2、3 依 dispatch criteria 跳過 Spec 軸：既無 SP- findings 待確認，且後續修正只觸及 schema 驗證嚴格度、一個新增測試與 README 文字，皆無法改變 spec 符合度。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `docs/adr/0007-llm-judge-bypasses-braintrust-gateway.md` | 決策本體：為何 judge 刻意繞過 Braintrust gateway、否決了什麼、逃生門在哪。先讀這份才看得懂後面的寫死 endpoint | |
| 2 | `backend/evals/eval_spec_schema.py` | Config contract：`ScorerConfig` 新增 `temperature`（含範圍約束與 programmatic 互斥守衛） | ⚠️ scenario 設定檔的 schema contract，改動影響所有 eval spec 的解析 |
| 3 | `backend/evals/scorer_registry.py` | Core logic：judge client 的唯一建構點，endpoint／key／temperature 三者在此匯流 | ⚠️ 外部 API 憑證與 endpoint 路徑 |
| 4 | `backend/evals/scenarios/language_policy/eval_spec.yaml` | Wiring：唯一消費 `temperature` 欄位的 scenario 設定 | |
| 5 | `backend/tests/evals/test_scorer_registry.py` | 防復發合約：兩把 key 並存、`OPENAI_BASE_URL` 改道、缺 key fail fast、temperature 邊界 | |
| 6 | `backend/evals/README.md` | 文件同步：schema 補 `temperature`、quickstart 的 key 需求更正 | |

## 所有修正問題詳解

### m-1.1（Minor）— programmatic scorer 顯式寫 `temperature: 0` 仍會通過驗證

- **問題：** 守衛寫成 `if self.temperature != 0.0`，只能擋掉「值不等於預設」的情況。programmatic scorer 只要顯式寫 `temperature: 0`，就會通過驗證——但錯誤訊息宣稱的是「must not set temperature」。schema 的承諾與實際行為不一致，scorer-mode 的嚴格二分被削弱。
- **修法：** 改用 Pydantic v2 的 `if "temperature" in self.model_fields_set`，判斷「欄位有沒有被提供」而非「值是多少」。
- **影響：** programmatic 與 llm_judge 兩種 scorer 的欄位分界回到真正互斥。這也是 `use_cot`／`model`／`choice_scores` 既有守衛的同類語意——只是那些欄位的預設值（`False`／`None`）恰好不會與合法輸入撞號，所以舊寫法沒暴露問題；`temperature` 的預設 `0.0` 正好是最常見的合法值，才讓漏洞浮現。
- **驗證：** 新增 `test_scorer_config_rejects_explicit_zero_temperature_on_programmatic_scorer`（顯式 `0.0` 被拒）與 `test_scorer_config_allows_programmatic_scorer_without_temperature`（省略時仍取得預設值、不誤傷正常設定）。`uv run pytest backend/tests/evals/ -q` → 133 passed。

### m-1.2（Minor）— `backend/evals/README.md` 的 schema 段落漏了 `temperature`

- **問題：** README 的 `Eval Spec YAML Schema` 宣稱是完整 schema，但新增的 `temperature` 欄位沒有列入，公開的設定介面與 `ScorerConfig`、`language_policy/eval_spec.yaml` 不一致。
- **修法：** 在 llm_judge scorer 區塊補上 `temperature: float # (optional) Judge sampling temperature, default 0.0; llm_judge only`，格式沿用相鄰 `model:`／`use_cot:` 的註解風格。
- **影響：** 下一個寫 scenario 的人能從 README 直接看到這個旋鈕存在，不必去讀 Pydantic model。
- **驗證：** 人工比對 README schema 區塊與 `ScorerConfig` 欄位清單，逐欄對齊。

### M-2.1（Major）— `temperature` 是無邊界的 provider 參數

- **問題：** schema 接受任意 float 後直接轉交 `LLMClassifier`／OpenAI。負值、超過 provider 範圍、`nan`、`inf` 都能通過 repo 驗證，只在 provider 呼叫時才失敗。關鍵在失敗的時機：`resolve_scorers()` 在 `eval_runner.py:405` 執行、`Eval()` 在 `:427`，但 temperature 要到 judge 實際被呼叫才送出——也就是**該列的 agent task 已經完成付費的 LLM 呼叫之後**才炸。
- **修法：** `temperature: float = Field(default=0.0, ge=0.0, le=2.0, allow_inf_nan=False)`，範圍取自 OpenAI 官方文件記載的 0–2。使用 Pydantic 官方的 `Field` 約束 API，不手刻 validator。
- **影響：** 打錯的 temperature 在 `load_scenario_config()` 當下就被擋下，不會浪費整輪 agent 呼叫的成本。**經人工裁決縮減範圍**：reviewer 原要求負值／超範圍／非有限值三個 regression test，裁定只保留一個超範圍案例——另外兩個測的是 Pydantic 自己的 `ge`／`allow_inf_nan` 實作，不是 repo 程式碼；真正產生保護作用的 `Field` 約束已完整落地。
- **驗證：** 新增 `test_scorer_config_rejects_out_of_range_temperature_on_llm_judge`（`temperature=2.5` 於 load 時拋錯）。另以 ad-hoc 確認 `Field(default=...)` 不會污染 `model_fields_set`——`ScorerConfig(name=..., function=...)` 省略 temperature 時 `model_fields_set == {'function', 'name'}`，證明 m-1.1 的守衛未被此改動破壞。`uv run pytest backend/tests/ -q` → 854 passed。

### m-2.1（Minor）— README quickstart 註解與實際的 key 需求矛盾

- **問題：** `README.md:26` 的 `# Local mode (default — no upload, no API key needed)` 與同檔 `:64` prerequisites 表格（Quality Track default 需要 `OPENAI_API_KEY`）自相矛盾。該註解原意是 ADR-0006 語境下的「不需要 Braintrust key」，但字面讀作「不需要任何 key」。judge 修好之後缺 key 會立即 fail fast，這個誤導變得更有代價。
- **修法：** 改為 `# Local mode (default — needs OPENAI_API_KEY, but no BRAINTRUST_API_KEY)`，維持單行、與相鄰 `# Upload mode (...)` 同形。
- **影響：** 新進者照 quickstart 執行時不會因為「文件說不用 key」而誤判 fail-fast 錯誤是 bug。
- **驗證：** 人工比對 quickstart 註解與 prerequisites 表格，兩處語意一致。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `backend/evals/README.md` | schema 區塊補上 `temperature` 欄位（m-1.2）；quickstart 的 local mode 註解更正 key 需求（m-2.1） |
| `docs/adr/` | 新增 ADR-0007，記錄 judge 繞過 Braintrust gateway 的決策、否決方案與逃生門（隨實作交付，非 review 產出） |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Major（M-1.1） | ADR-0007 長度 69 行，超出 `design-envelope.md` §4 的「≤100 words」規定 | 人工裁決維持現狀（2026-08-02）。DEV-120 的 D6 明列 ADR 須涵蓋六個主題，100 字內無法容納；且 `docs/adr/` 現有 0001–0006 無一符合該字數限制 | envelope §4 的字數規定與實務全面脫節，屬 SSOT 本身該修的條文——建議另開 issue 討論是改條文還是改全部 ADR，不搭本票便車 |
| Major（M-2.1 部分） | 負值／`nan`／`inf` 的 regression test | 人工裁決：測的是 Pydantic 自身實作而非 repo 程式碼。真正的保護（`Field` 約束）已落地 | 無須後續 |
| 觀察（非 issue） | 最終 E2E run 中 `response_language` 為 75%（8 列中 2 列失分），前一次 run 為 100% | 與本 changeset 無關——diff 未觸及 agent、task function 或該 programmatic scorer。屬 agent 非決定性輸出：LP-07 對中文提問回了英文（真實的 language-policy 違規），LP-01 回覆雖為中文但數字佔比過高、CJK ratio 落在門檻下 | 這正是該 scenario 存在的目的所測到的訊號。建議另開 issue 追 agent 的語言遵循，或併入既有的 agent 品質票 |

## Final Verification Results

### Code Level

- [x] Unit Tests: `uv run pytest backend/tests/ -q` → **854 passed**, 49 deselected（deselected 為既有的 `-m 'not eval'` 排除）
- [x] Lint: `uv run ruff check backend/` → **All checks passed**
- [x] Format: `uv run ruff format --check backend/` → **156 files already formatted**
- [x] Type Check: `uv run pyright` 於三個變更的 Python 檔 → **0 errors, 0 warnings**

### Behavior Level

> 本 changeset 無 `bdd-scenarios.md` / `verification-plan.md` / `implementation.md`；以下行為驗證由 DEV-120 的 acceptance criteria 直接導出。

- [x] **兩把 key 並存時 judge 仍走 OpenAI**（本次事故的前置條件）：`test_llm_judge_uses_openai_key_when_braintrust_key_is_present` → PASS
- [x] **設了 `OPENAI_BASE_URL` 也不改道**：`test_llm_judge_ignores_openai_base_url_env` → PASS
- [x] **缺 `OPENAI_API_KEY` 於建構當下失敗、訊息點名變數與 endpoint**：`test_llm_judge_fails_fast_without_openai_api_key` → PASS
- [x] **`temperature` 顯式為 0 並傳抵 autoevals**：`test_resolve_scorers_builds_llm_classifier` 攔截建構參數斷言 `temperature == 0.0` → PASS
- [x] **production scenario 設定仍可載入**：`load_scenario_config()` 對 `language_policy/eval_spec.yaml` → 三個 scorer 全數解析、`temperature=0.0`

### Runtime / Observable Level

- [x] **AC 第一條（judge 實跑產出分數）**：`uv run python -m backend.evals.eval_runner language_policy`（2026-08-02，review 修正全數套用後重跑）
  - Expected：`response_relevance` 每列有分數、無 `AuthenticationError`
  - Actual：`response_relevance` **8/8 列皆有分數（100.00%）**，全程無 authentication 錯誤
  - Result：**PASS**
  - 附帶觀察：同一 run 的 `response_language` 為 75%，屬 agent 非決定性輸出，與本 changeset 無關（見「未處理項目」）

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/evals/scorer_registry.py` | 無 review 修正——三輪 review 未對此檔提出任何 issue |
| `backend/evals/eval_spec_schema.py` | m-1.1：守衛改用 `model_fields_set`；M-2.1：`temperature` 加上 `Field(ge=0.0, le=2.0, allow_inf_nan=False)` |
| `backend/evals/scenarios/language_policy/eval_spec.yaml` | 無 review 修正 |
| `backend/evals/README.md` | m-1.2：schema 補 `temperature` 欄位；m-2.1：quickstart 註解更正 key 需求 |
| `backend/tests/evals/test_scorer_registry.py` | 新增 3 個測試：顯式 `0.0` 被拒、省略時仍取預設、`llm_judge` 超範圍 temperature 於 load 時被拒 |
| `docs/adr/0007-llm-judge-bypasses-braintrust-gateway.md` | 無修正——M-1.1（字數）經人工裁決維持現狀 |

## Learning Notes

### 採用的工程策略

- **「單一建構點」讓可逆決定變便宜。** D3 選擇 per-evaluator 注入而非全域 `init()`，理由是 reachability；實作後浮現第二個好處——因為 client 只在一處被建出來，ADR-0007 才寫得出「改走 gateway 只需動兩個值」這個具體的逃生門。抽象的價值不只在當下的正確性，也在於它讓未來的反悔有明確的價格標籤。三輪 review 對 `scorer_registry.py` 零 issue，佐證這個收斂是站得住的。
- **顯式配置換掉環境推斷，同時換掉了「無法測試」。** 本 bug 的根因是兩個環境變數的隱性組合；D1 選擇程式碼顯式化之後，才有可能寫出 case 2／case 3 那種「兩把 key 並存仍走 OpenAI」「設了 `OPENAI_BASE_URL` 也不改道」的防復發測試。可測性不是修法的副產品，而是選擇該修法的理由之一。

### 權衡取捨

- **預期「沿用既有驗證模式」是零風險的，實際上模式本身有隱藏前提（m-1.1）。** D4 說「沿用既有的 programmatic／llm_judge 互斥驗證」，照抄 `use_cot` 的 `if self.use_cot:` 寫法看似安全。但那些既有欄位的預設值（`False`／`None`）恰好不會與合法輸入撞號，而 `temperature` 的預設 `0.0` 正是最常見的合法值——同一個模式套到不同型別的欄位上，語意就從「有沒有設」偷偷變成「值是不是預設」。**照抄模式時要問的不是「這個模式對嗎」，而是「這個模式成立的前提在新脈絡下還在嗎」。**
- **envelope 的條文與實務脫節時，該修的是條文（M-1.1）。** reviewer 引用 `design-envelope.md` §4 的「ADR ≤100 words」判 Major，引用屬實；但現有 0001–0006 無一符合，而 DEV-120 的 D6 又明列六個必寫主題。裁決維持 ADR 現狀，代價是留下一條已知的 SSOT 不一致——這是刻意的選擇，不是遺漏，且已記入未處理項目待另案處理。
- **fail-fast 的價值取決於「fast 到什麼時候」（M-2.1）。** 原本以為 temperature 打錯反正 API 會擋，屬可接受的 runtime 失敗；查了 `eval_runner.py:405` 與 `:427` 的執行順序才發現，judge 是在該列 agent task 已經付費跑完之後才呼叫——失敗的成本不是「一個錯誤訊息」而是「整輪 agent 呼叫的錢」。**判斷 validation 值不值得，要先算出失敗發生的實際位置與代價，不能停在「反正會失敗」。**

### 關鍵收穫

- **預設值等於合法值的欄位，驗證必須問「有沒有被提供」而不是「值是多少」**（m-1.1）。Pydantic v2 的 `model_fields_set` 是這件事的正解；而 `Field(default=...)` 不會污染該集合，兩者可以並存——這個交互作用在 M-2.1 的修正中被特意驗證過，因為它正是兩條規則會互相踩到的地方。
- **文件與程式碼的不一致，會在「錯誤變得有意義」的那一刻才顯形**（m-2.1）。README 那句「no API key needed」在 judge 壞掉、缺 key 只是靜默 401 的年代不痛不癢；judge 修好、缺 key 變成 fail fast 之後，同一句話就會讓人把正確的錯誤訊息誤判成 bug。**改動讓某個失敗路徑變得清晰時，要回頭檢查文件有沒有在教人忽略它。**
- **跨 model 的 review 隔離換到的是不同的盲點，不是更多的挑剔**（M-2.1 / m-2.1）。這兩條都不是風格問題，而是本 session 自己做的 two-axis review 完全沒看到的東西——因為寫 code 的人「知道 temperature 只有自己會填」「知道那句註解的原意是 Braintrust key」。Codex 沒有這些前提，才問得出「誰保證這個 float 在範圍內」。**epistemic isolation 的產出品質，取決於 reviewer 缺少多少作者才有的脈絡。**
