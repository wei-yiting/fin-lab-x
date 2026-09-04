# Code Review Improvement Report

> **Task:** DEV-205 — Benchmark protocol infra + dataset split proposal
> **Date:** 2026-09-04
> **Rounds:** 4 (+1 orchestrator-direct fix outside the round structure, see below)
> **Reviewer model:** gpt-5.6-sol (Codex, both axes, all rounds)
> **Fixer model:** Claude Sonnet 5 (general-purpose subagent, all rounds)

## 架構影響摘要

- `response_no_simplified_chars`（`language_policy` scorer）從單純的字元完全比對，演變成「系統性推導的 170 字身份曖昧清單 + 15% 比例門檻 + 絕對錯誤字數門檻 3」三層機制——這是本次審查中變動最大、討論最深的部分，理由詳見下方 Learning Notes。
- `row_selection.py` 的 split guard 新增 `status` 欄位與凍結閘門（`apply_split()` 現在要求 `status == "frozen"` 才能開放 holdout/reserve），但仍維持「還沒有任何 caller」的狀態——這是刻意的：DEV-206（下一票）才是實際的呼叫端。
- `split.json` 從一份混合「機器要讀的資料」與「人要看的敘述」的檔案，收斂成只剩 9 個 key 的純資料 sidecar；敘述性內容依「是否仍是待審核決策的依據」拆分到 README（留存）或直接捨棄（已結案的 QA 記錄，移到 review-loop 自己的 artifact）。

如果沒有架構層級變更，寫：
`本次 review 無架構層面的變更，所有修正皆為 correctness / stability / documentation。`
（此次不適用——上述三項都是實質的架構/介面變更。）

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 4（另有 1 個 orchestrator 在 Final Verification 階段直接修正、未走完整輪次的 pyright 型別問題） |
| 發現 issues 總數 | 22（quality 軸 16、spec 軸 6） |
| Blocking | 0/0（quality 軸無 Blocking 分類；spec 軸的 Blocking 已併入下方 Spec findings 列） |
| Major | 6/8 fixed（2 個以使用者決策 dismiss，非未修復） |
| Minor | 7/7 fixed |
| Suggestion | 1/1 adopted |
| Spec findings (SP-) | 5/6 fixed（1 個 dismissed） |
| 文件修正 | 6（README ×3 處變更、scorer.py docstring 重寫 ×2 輪、config_loader.py/base.py docstring 更新、split.json 敘述性內容遷移） |

## Spec Conformance（Spec 軸）

> 與 Quality 軸並列呈現，不合併排序。每筆引用對應的 spec 來源行。

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Missing（split guard 未接入 run path） | "diagnostic row selection 讀取它" (DEV-205 AC) | dismissed — DEV-206 的 issue 文字明確列出需要這個 guard，是已排定的下一個 caller，非「可能有用」的臆測 |
| SP-1.2 | Misimplemented（簡繁 scorer 誤判合法繁中） | "繁中回答含簡體字 → 0" (DEV-205 AC) | fixed（歷經 round 1 單字元修補 → round 2 系統性 170 字重新設計 → round 3 補絕對值門檻，三輪才完全收斂） |
| SP-1.3 | Misimplemented（curation 漏掉 row 19 異常） | "curation 欄位一致性過查完成，異常記錄在案" (DEV-205 AC) | fixed |
| SP-1.4 | Scope creep（真實 split 分配進了 unit test） | "split 實際分配屬人審 gate 驗證，不進 unit test" (DEV-205 Testing decisions) | fixed |
| SP-2.1 | Misimplemented（split guard 缺凍結前置檢查） | "僅限凍結 tag 之後" (DEV-200 定案決策) | fixed — 採 `status` 欄位而非執行期查 git tag |
| SP-3.1 | Missing（人工微調理由从審核介面消失） | "人工微調理由記錄 — 交人 review" (DEV-205 AC) | fixed |

## Reading Guide

> 給人類 reviewer 的建議閱讀順序。這是 slice PR 的導覽表——不必從上到下讀整個 diff，依此表逐檔查看即可。
> 排序原則：先讀 contracts/types，再讀 core logic，接著 wiring/整合，最後才是 tests。
> **風險標記：** `⚠️` 表示該檔案觸及不可逆操作、對外 contract（API / schema / wire format / migration）或 security 路徑，應優先且仔細檢視；其餘留白。

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/agent_engine/agents/config_loader.py` | `ModelConfig.reasoning_effort` 欄位、`ProfileConfigLoader.load_from_dir()` | |
| 2 | `backend/agent_engine/agents/base.py` | `_init_model()` 把 `reasoning_effort` 映射到各 provider 的實際 kwarg | |
| 3 | `backend/evals/diagnostic/row_selection.py` | `SplitSidecar`／`load_split_sidecar`／`apply_split`——洩漏防護的凍結閘門邏輯 | ⚠️（eval 洩漏防護，行為錯誤會讓 holdout/reserve 提前曝光） |
| 4 | `backend/evals/scenarios/language_policy/scorer.py` | `response_no_simplified_chars` 全新三層判定機制，本次變更中最複雜的邏輯 | ⚠️（決定「語言正確」判準的核心邏輯，經三輪才收斂） |
| 5 | `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/split.json` + `README.md` | 實際 split 提案資料 + 現在停留的人審 rationale——這就是 DEV-205 要交出去給人看的東西 | ⚠️（這是人審 gate 的直接輸入，請仔細看） |
| 6 | `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/configs/*/orchestrator_config.yaml` + `prompt/system_prompt.md` | 4 個候選 config + 共用 prompt | |
| 7 | `backend/tests/agents/test_config_loader.py`, `test_init_model.py` | config loading／reasoning kwarg 對映測試 | |
| 8 | `backend/tests/evals/test_diagnostic_row_selection.py`, `test_language_policy_scorer.py` | split guard／scorer 測試 | |
| 9 | `CONTEXT.md`, `backend/agent_engine/agents/README.md` | 術語修正、文件更新 | |

## 所有修正問題詳解

> 必填。每個 issue 都要用同一格式，避免 reviewer 需要回頭看 round artifacts。

### M-1.1 / SP-1.2（Major / Blocking，橫跨 round 1-3）
- **問題：** `response_no_simplified_chars` 用「OpenCC 轉換前後是否完全相同」判斷簡繁純度，會把合法的繁體用字（台灣、台積電、干預、公司公布財報、市占率、范先生⋯）誤判成簡體污染。
- **修法：** 分三輪收斂——round 1 先發現「台」這個字有問題，寫死排除；round 2 發現這不是單一字元問題（干、布、占、范都有同樣的雙重身份），改成系統性從 OpenCC 自己的 `STCharacters.txt` 字典檔推導出完整的 170 字清單，同時因為使用者決定這個 scorer 的職責是「判斷整體語言對不對」而非「零容忍任何錯字」，改用比例門檻（真正錯誤字元 / 中文字元總數 ≤ 15%）；round 3 發現比例門檻本身有漏洞（常見財經詞彙如股票、成交量在簡繁體完全相同，真正整段簡體但詞彙「幸運」的回答比例可以壓到 15% 以下），加上絕對值門檻（真正錯誤字元數 ≤ 3）作為第二道防線，兩個條件都要成立才算純淨。
- **影響：** 這是 benchmark 用來判斷 4 個候選 config 語言紀律優劣的關鍵指標；如果誤判合法繁中，會讓所有 4 個 config 的分數都被雜訊污染，破壞比較的意義。
- **驗證：** 三輪各自的獨立驗證：round 2 直接測試台灣/台積電/平台等詞彙、round 3 的兩個 Codex reviewer 各自用不同反例（政府干預市場 / 公司公布財報等）驗證，最終 round 4 兩軸都確認 170 字衍生正確、比例與絕對值門檻都正確觸發，且既有的「全簡體必須判 0」與「偶爾一兩個錯字容忍」測試都通過。

### M-1.4（Major，round 1 → round 2 才完全修復）
- **問題：** 4 個候選 config 用 `C1`/`C2`/`C3`/`C4` 這種序數代稱貫穿目錄名、config 名、描述文字、測試——這些代號離開產生它們的規劃情境就沒有意義。
- **修法：** Round 1 先改了目錄名跟描述（`c1_luna_none` → 描述性名稱），但漏了 3 個測試裡把 `c1_luna_none` 當泛用 placeholder 目錄名使用的地方；round 2 全部改成明確不像真實候選名稱的字串（`sample_config`）。
- **影響：** 純可讀性/可維護性，不影響行為。
- **驗證：** `grep` 全域搜尋確認無殘留。

### m-1.1（Minor，round 1）
- **問題：** `split.json` 與程式碼裡留了 `DEV-200`/`DEV-205` 這種內部 issue id。
- **修法：** 移除，保留描述性文字本身（規則已經講清楚，不需要 ticket 編號佐證）。
- **影響：** 可讀性。
- **驗證：** grep 確認移除。

### m-1.2（Minor，round 1）
- **問題：** `load_split_sidecar()` 只驗證 tier 是不是 list，沒驗證裡面每個 id 是非空字串。
- **修法：** 加上逐一元素驗證，錯誤訊息點名是哪個 tier、哪個壞值。
- **影響：** 邊界驗證完整性。
- **驗證：** 新增 malformed-element 測試。

### m-1.3（Minor，round 1）
- **問題：** `config.reasoning_effort or "medium"` 是 falsy trap，空字串會被吃成預設值而不是報錯。
- **修法：** 改成明確的 `is not None` 檢查，並在建構時額外驗證空字串直接報錯。
- **影響：** 防止設定錯誤被靜默吞掉。
- **驗證：** 新增 empty-string 測試。

### S-1.1（Suggestion，round 1）
- **問題：** `load()` 跟 `load_from_dir()` 內部邏輯幾乎重複。
- **修法：** 抽出共用的 `_parse_config()` helper，兩個公開方法各自的 auto-discovery 語意不變。
- **影響：** 減少重複，不影響行為。
- **驗證：** 既有測試全數不變且通過。

### M-2.1（Major，round 2）
- **問題：** row 19 內容修正後（見 SP-1.3），`dataset_version` 沒有跟著變動，導致修正前後的資料在 trace metadata 裡無法區分。
- **修法：** zh/en 兩邊 `eval_spec.yaml` 與 `split.json` 的 `dataset_version` 一起 bump 到同一個新日期。
- **影響：** 維持 design-envelope §4 要求的 reproducibility（每次 run 都要能追溯到確切的資料版本）。
- **驗證：** 確認 `eval_runner.py` 真的把這個欄位寫進 trace metadata；三處版本號一致。

### m-2.1（Minor，round 2）
- **問題：** `apply_split()` 驗證了 sidecar 那側的 row id，但沒驗證實際傳入的 dataset rows 那側，缺 id 或重複 id 會產生不好懂的錯誤或靜默通過。
- **修法：** 對稱地加上 dataset 側驗證。
- **影響：** 邊界驗證完整性。
- **驗證：** 新增 missing/non-string/duplicate id 測試。

### m-2.2（Minor，round 2）
- **問題：** `opencc-python-reimplemented` 放在主要 `dependencies`，但只有 eval-only 的 scorer 會用到；`Dockerfile` 是 `uv sync --no-dev`，正式環境的 image 會多裝一個用不到的套件。
- **修法：** 搬到 `[project.optional-dependencies].dev`。
- **影響：** 減少正式環境 image 的不必要依賴。
- **驗證：** 確認 `uv export --no-dev` 不再包含它，`--extra dev` 才會包含。

### m-2.3（Minor，round 2）
- **問題：** scorer.py 註解留了第三方套件（`hanzidentifier`）的 GitHub issue 編號。
- **修法：** 移除編號，保留旁邊已經寫清楚的理由文字。
- **影響：** 可讀性；避免依賴一個外部、可能失效的參照。
- **驗證：** grep 確認移除。

### SP-1.3（Blocking → Fixed，round 1-2）
- **問題：** zh dataset row 19 的翻譯把「Finnhub」誤植成「yfinance」，跟英文版與 `expected_best_source` 欄位不一致；curation 記錄宣稱 0 anomalies，實際上漏掉這筆。
- **修法：** 修正 row 19 內容；orchestrator 手動重新逐列核對全部 30 列的 4 個自由文字欄位（question / expected_answer_type / rationale / draft_pass_signals），確認這是唯一的異常；round 2 討論後決定整個查核過程的記錄不留在 `split.json`（那是給機器讀的 sidecar），改放進 review loop 自己的 `fix-round-1.md`。
- **影響：** 資料正確性；影響任何以此欄位作為判斷依據的下游分析。
- **驗證：** Round 3、round 4 的 spec reviewer 各自獨立重新核對 zh/en 30 列資料一致性，均確認無其他異常。

### SP-1.4（Minor → Fixed，round 1）
- **問題：** 新增的 3 個測試直接斷言 `split.json` 實際分配結果（counts、完整涵蓋、row 5 歸屬），違反 DEV-205 自己「split 實際分配屬人審 gate 驗證，不進 unit test」的既定原則。
- **修法：** 移除這 3 個測試與相關常數，保留使用 synthetic sidecar 的 guard 行為測試。
- **影響：** 符合既定的測試邊界；避免每次調整 split 都要連帶改一批脆弱的斷言。
- **驗證：** grep 確認無殘留，後續各輪重新掃描亦未發現等價替代品。

### M-2.2 / m-1.1 延伸議題（Major，round 2，經討論後改變處理方向）
- **問題：** `split.json` 混雜了機器要讀的資料（dev/holdout/reserve）跟人要看的敘述（分層方法、seed 搜尋過程、人工微調理由、curation 查核過程）。
- **修法：** 這不是單純的用字問題（原本 reviewer 建議改寫用詞），而是位置問題——經與使用者討論後，確認 `stratification`／`curation_pass`／`twin_rule` 這幾個欄位完全沒有任何程式碼會讀取（`grep` 全 repo 驗證），於是：`curation_pass` 整段刪除（歷史已存在 `fix-round-1.md`）；`stratification` 的 seed 搜尋與湊整數過程整段刪除（純粹一次性衍生過程，無前瞻價值）；`twin_rule` 與「row 5 強制進 holdout」這兩條**仍在生效的規則**搬進 README。
- **影響：** `split.json` 從 40 行的資料+敘述混合檔，收斂成 9 個 key 的純資料 sidecar；README 成為人類唯一需要閱讀、理解這份 split 提案的地方。
- **驗證：** `load_split_sidecar()`／`apply_split()` 的既有測試全數通過（它們從一開始就只讀 dev/holdout/reserve，這個重構對它們是 no-op）。

### SP-2.1（Major → Fixed，round 2）
- **問題：** DEV-200 定案決策要求「holdout/reserve 需明確 opt-in，且僅限凍結 tag 之後」，但 `apply_split()` 只檢查 opt-in flag，完全沒檢查是否已凍結——即使 `split.json` 的 `status` 還是 `proposed`，理論上呼叫端一樣可以拿到 holdout 資料。
- **修法：** 討論了「執行期查 git tag」與「用 sidecar 自己的 `status` 欄位」兩個方案，選擇後者：`SplitSidecar` 新增 `status` 欄位，`apply_split()` 要求 `status == "frozen"` 才放行 holdout/reserve。前者被否決的理由：會讓一個純資料處理函式背上 git 依賴，還要把一次性的實驗 tag 名稱寫進可重用程式碼。
- **影響：** 補上 DEV-200 決策裡「僅限凍結後」這個字面要求；凍結儀式（DEV-206 執行）之後才需要同步把 `status` 改成 `frozen`。
- **驗證：** Round 3、round 4 均直接執行 `apply_split()`，確認 `status: "proposed"` 時 3 種 opt-in 組合皆拋出 `ValueError`，換成 `status: "frozen"` 後正確放行。

### M-3.1（Minor，round 3）
- **問題：** Round 2 的 fixer 在新增的 test docstring 裡寫了「Round-2」「round-1 fix」「(Part A)」——這正是這一整輪 review 在抓的同一種問題（process identifier），諷刺地被修別的問題時重新引入。
- **修法：** 改寫成直接描述測試在驗證什麼，不提輪次。
- **影響：** 可讀性；避免未來的讀者需要考古「Part A」是什麼。
- **驗證：** grep 全 scope 檔案確認無殘留。

### M-3.3（Major，round 3）
- **問題：** 170 字衍生邏輯如果碰到空檔案或格式跑掉，不會報錯，只會安靜產生空集合——跟原本要求的「壞掉要大聲失敗」不符，之前只有 fixer 手動驗證過一次「長度是 170」，程式碼裡沒有留下永久的檢查。
- **修法：** 在計算完 `_DUAL_STATUS_TRADITIONAL_CHARS` 後立刻加上 `assert len(...) > 100`，載入時就會失敗，而不是悄悄用一個壞掉的清單繼續跑。
- **影響：** 防止未來 `opencc-python-reimplemented` 版本更新、字典檔格式改變時，這個 scorer 悄悄退化回 round 1 的誤判狀態卻沒人發現。
- **驗證：** Round 4 確認真實推導出 170 個字元時 assertion 不會誤觸發。

### SP-3.1（Blocking，round 3）
- **問題：** `split.json` 重構時，`manual_adjustments`（`boundary × may_pass_with_tuning` 這個 stratum 從 reserve 移一列到 dev 的理由）跟著 seed 搜尋過程一起被當成「純過程細節」刪掉了；但 DEV-205 的驗收標準明確要求「人工微調理由記錄——交人 review」，而這個決定所屬的 split 提案**現在還在等人審**，跟已經結案的 curation 查核不是同一類東西。
- **修法：** 在 README 補回一段簡短說明：為什麼這個 stratum 有 +1/-1 的調整（獨立按 stratum 湊整數留下缺口，選這個 stratum 吸收是因為它列數最多），但不恢復 seed 值或搜尋過程細節。
- **影響：** 讓人審者能真正評估這個決定是否合理，而不是只能相信一個沒有理由的數字。
- **驗證：** Round 4 spec reviewer 直接讀取 README 內容，確認與 `split.json` 實際的 4/7/2 分配一致。

### M-3.2（Major，round 3，見上方 M-1.1 合併說明）

### 型別安全微調（orchestrator 直接修正，未走完整 round）
- **問題：** Final Verification 階段執行 `pyright` 時發現 `Path(_opencc_pkg.__file__)` 型別不安全——`__file__` 在 typeshed 裡是 `str | None`。
- **修法：** 加上 `assert _opencc_pkg.__file__ is not None`，與檔案既有的 fail-loud 風格一致。
- **影響：** 極低機率的邊界情況（正常 pip 安裝的套件幾乎不會有這個問題），純屬型別健全性強化。
- **驗證：** `pytest`、`ruff`、`pyright` 三者皆確認乾淨。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `backend/agent_engine/agents/README.md` | 記錄 `reasoning_effort` 欄位語意與 `load_from_dir()` 用途 |
| `backend/agent_engine/agents/config_loader.py` | `ModelConfig`/`WorkflowProfileConfig` docstring 補充 `reasoning_effort`、`load_from_dir()` 語意 |
| `backend/agent_engine/agents/base.py` | `_init_model()` docstring 反映新的 `reasoning_effort` 支援 |
| `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/README.md` | 三輪累積：C1-C4 改名反映在目錄結構描述、twin rule 與 row 5 規則說明、manual adjustment 理由 |
| `CONTEXT.md` | `beyond_boundary` 術語修正，與資料集實際欄位對齊 |
| `backend/evals/scenarios/language_policy/scorer.py` | `response_no_simplified_chars` docstring 因應設計演變重寫兩次 |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Env-blocked | Codex round 3 的 quality axis review 因基礎設施問題（10 分鐘逾時砍掉底層 process、留下卡住的 job lock）未能產出完整格式化報告 | 三次重試後改直接讀取 job log 檔案取得部分結果；使用者最終手動 `/codex:cancel` | Round 4 已重新完整跑過同樣範圍並確認乾淨，這個 gap 已被後續輪次覆蓋，不需要再處理 |

若全部處理完成，寫：`無`。
（除上表外，其餘全部處理完成。）

## Final Verification Results

### Code Level

- [x] Unit Tests: `pytest backend/tests/` → 1376 passed, 61 deselected（`-m eval` regression suite，依 AGENTS.md 慣例排除，不燒真實 LLM/API 額度）
- [x] Lint: `ruff check backend/` → All checks passed
- [x] Format: `ruff format --check backend/` → 216 files already formatted
- [x] Type Check: `pyright`（scoped 到本次變更的核心檔案）→ 找到 1 個真實、極低風險的型別窄化缺口，已直接修正；其餘錯誤為環境未設定 venv path 導致的 `reportMissingImports` 假警報（repo 未設定 `[tool.pyright]`，非本次變更引入的問題，AGENTS.md 本身也將型別檢查列為 "if configured"）

### Behavior Level

本票為後端 eval 基礎設施（無 UI、無 API endpoint），沒有走過 `behavior-validation-plan` 產出 BDD 文件；四輪 review 過程中已對核心行為做過大量實機驗證，等同於 behavior-level 驗證：

- [x] Scorer 正確分類：合法繁中（台灣/台積電/干預/公司公布財報/市占率保持穩定/范先生等）→ 1.0；完整簡體回答 → 0.0；比例低但絕對錯誤數超標的回答 → 0.0；偶爾 1-2 個真錯字 → 1.0
- [x] 4 個 benchmark config 皆可透過 `ProfileConfigLoader.load_from_dir()` 正確載入，correctly 綁定 provider 與 reasoning 參數，且共用同一份 shared prompt（byte-identical，未提前進行 DEV-206 的 prompt 演進）
- [x] Split guard 正確執行：`status: "proposed"` 時 dev-only 可用、holdout/reserve 三種 opt-in 組合皆正確拒絕；`status: "frozen"` 時正確放行
- [x] Split 提案資料完整性：dev 8／holdout 16／reserve 6，30 個 id 完整互斥涵蓋，row 5 在 holdout，en/zh twin 一致

### Runtime / Observable Level

不適用——無 API endpoint 或使用者可觀察的執行路徑；本票交付的是 eval 基礎設施，供 DEV-206 消費。

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `CONTEXT.md` | 術語修正（`beyond_boundary`） |
| `backend/agent_engine/agents/README.md` | 記錄 `reasoning_effort`／`load_from_dir()` |
| `backend/agent_engine/agents/base.py` | `_init_model()` 支援 `reasoning_effort`；docstring 更新 |
| `backend/agent_engine/agents/config_loader.py` | `ModelConfig.reasoning_effort`、`ProfileConfigLoader.load_from_dir()`、共用 `_parse_config()` |
| `backend/evals/diagnostic/row_selection.py` | `SplitSidecar`／`load_split_sidecar`／`apply_split`：dev-only 預設、per-tier opt-in、凍結閘門、雙側（sidecar + dataset）id 驗證 |
| `backend/evals/scenarios/baseline_behavior_diagnostic/eval_spec.yaml` | `dataset_version` bump |
| `backend/evals/scenarios/baseline_behavior_diagnostic_zh/eval_spec.yaml` | `dataset_version` bump |
| `backend/evals/scenarios/baseline_behavior_diagnostic_zh/dataset.csv` | row 19 修正（yfinance → Finnhub） |
| `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/README.md` | C1-C4 改名反映、twin rule、row 5 規則、manual adjustment 理由 |
| `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/configs/{luna_none,luna_medium,gemini_minimal,gemini_medium}/orchestrator_config.yaml` | 4 個候選 config（原 c1-c4 改名） |
| `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/prompt/system_prompt.md` | 共用 shared prompt（未變更內容） |
| `backend/evals/scenarios/baseline_behavior_diagnostic_zh/benchmark/split.json` | 收斂至 9-key 純資料 shape；`dataset_version` bump |
| `backend/evals/scenarios/language_policy/eval_spec.yaml` | 註冊新 scorer |
| `backend/evals/scenarios/language_policy/scorer.py` | `response_no_simplified_chars` 三層機制全新設計（170 字衍生 + 比例 + 絕對值門檻 + fail-loud assertion + 型別窄化） |
| `backend/tests/agents/test_config_loader.py` | `load_from_dir()`／`reasoning_effort` 測試；placeholder 改名 |
| `backend/tests/agents/test_init_model.py` | `reasoning_effort` provider mapping 測試 |
| `backend/tests/evals/test_diagnostic_row_selection.py` | split guard 全測試矩陣（sidecar/dataset 雙側驗證、凍結閘門） |
| `backend/tests/evals/test_language_policy_scorer.py` | scorer 三層機制測試 |
| `pyproject.toml` | `opencc-python-reimplemented` 移至 dev dependencies |
| `uv.lock` | 對應 lockfile 更新 |

## Learning Notes

> 三個時間點視角的第三站——post-implementation、結果已知，回答「做完後實際學到什麼?」

### 採用的工程策略

- **系統性推導優於逐一發現的白名單**（M-1.1）：round 1 的「發現一個問題字元、加進 hardcode 清單」策略看起來合理，但本質上是打地鼠——round 2、round 3 各自又被不同的新反例打臉。真正收斂的做法是回頭看資料本身的結構（OpenCC 字典檔裡「這個字自己也出現在自己候選清單裡」這個模式），一次性推導出完整範圍，而不是持續累積個案。這個教訓也已經記在 `feedback_prefer_standard_libs.md` 的精神延伸：優先用資料/套件本身已有的結構，而不是手工維護一份可能不完整的清單。
- **兩個互補機制優於單一機制的極限拉扯**（M-3.2）：比例門檻在「偶爾錯字容忍」跟「整段語言錯誤」之間找一個切點，但這兩件事本質上是不同維度的訊號（用詞选擇的巧合 vs. 實際錯誤密度），單一比例永遠會在某個構造出的例子上失守。加上一個獨立的絕對值門檻，讓兩個機制各自守住自己最擅長的情境，而不是逼一個數字做兩件事。

### 權衡取捨

- **DEV-206 依賴關係的重新評估**（M-1.2/M-1.3/SP-1.1）：一開始這幾個「零 caller」的發現看起來像是違反 design-envelope §0 的 reachability rule（「unreachable generality is deleted, not documented」）；但實際去讀 DEV-206 的 issue 文字，發現它的 "Blocked by" 欄位明確寫著需要「config 載入、scorers、split guard 與已核准的 split」——這是一個已經排定、有明確驗收標準依賴的下一個 caller，不是「可能有用」的臆測。這推翻了我一開始的判斷，說明查驗「文件宣稱的理由」還不夠，要去查「真正的下一個消費者是否已經存在且明確需要它」。
- **敘述性內容該放資料檔還是文件**（M-2.2/SP-3.1，同一次重構裡的一體兩面）：拆分 `split.json` 敘述性欄位時，用「有沒有程式碼在讀」當唯一判準是不夠的——`curation_pass`（已結案的 QA 記錄）跟 `manual_adjustments`（還在等人審的決策依據）都符合「沒有程式碼讀取」，但一個可以整段刪除、一個必須保留在人看得到的地方。真正的判準是「這個資訊是不是某個還沒發生、需要人做判斷的事件的輸入」——這條線第一次拆分時沒抓對，被 round 3 的 spec reviewer 抓出來，也是這次 review 過程本身在示範「兩軸分開審查」的價值：quality 軸的「刪除死資料」判斷是對的，但 spec 軸額外看到了「這份資料是不是驗收標準明確要求交給人看的東西」。

### 關鍵收穫

- **同一種問題會在修別的問題時被重新引入**（m-1.1 → M-2.2 → M-3.1）：process identifier／session 專屬標籤這個問題，在三輪修正裡各自以不同形式重新出現——round 1 修完程式碼裡的 issue id，round 2 的 fixer 卻在改寫敘述時又寫進「Pass 1/Pass 2」（雖然最後判定那個不算，但同一批修正裡的「row 4」確實是同類問題），round 3 更直接：修 round 2 遺留的 C1-C4 問題時，自己的 test docstring 又寫了「Round-2」「Part A」。這代表這類問題不能只在被抓到的當下修掉，而要在每一輪的 fixer 指令本身留意——orchestrator 後續應該提醒 fixer 「不要把我這份指令裡的輪次/段落編號抄進程式碼」。
- **使用者中途修改 spec 的解讀是合法的，且會改變後續所有輪次的基準**（M-1.1/SP-1.2 的核心轉折）：「繁中回答含簡體字 → 0」這條驗收標準，字面上很容易讀成「零容忍任何簡體字」；但使用者在討論過程中明確決定這個 scorer 的職責其實是「判斷整體語言方向」。這不是在修 bug，是在重新定義「通過」的意義——一旦拍板，round 3、round 4 的 spec reviewer 都正確地把這個新定義當作權威版本，沒有拿舊的字面解讀去質疑「這是不是退步」。這說明 spec 軸的驗收標準不是一成不變的化石，人在過程中對模糊字面的釐清本身就是有效的 spec 更新，但這個更新必須明確被記錄（本次記在 review-round-2.md 的 Discussion Gate Resolution），否則下一輪 reviewer 無從分辨這是授權的改變還是真的漏洞。
- **驗證要跑真的程式碼，不能只信報告**（貫穿全部四輪）：這次每一輪的 fixer 報告本身寫得都相當仔細，但 orchestrator 每次仍然獨立重跑測試、直接 import 模組驗證推導結果、實際呼叫 scorer 測試具體字串——多次發現 fixer 報告「聲稱」的東西與實際狀態一致（值得信任的訊號），但也有像 M-3.3 這樣的案例：round 2 的 fixer 手動驗證過一次「170 字」就視為完成，卻沒把這個驗證變成程式碼裡的永久檢查，直到 round 3 才被抓到。一次性的人工驗證跟寫進程式碼的常態檢查是兩件不同的事，前者不能取代後者。
