# Code Review Improvement Report

> **Task:** DEV-141 — 資料路徑集中 + retry 與錯誤 hierarchy 收斂
> **Date:** 2026-08-07
> **Rounds:** 3 輪 review + 3 輪 fix
> **Reviewer model:** gpt-5.6-sol（Quality 軸,Codex）/ claude-sonnet-5、claude-fable-5（Spec 軸）
> **Fixer model:** claude(subagent × 2 輪 + orchestrator-applied × 1 輪)

## 架構影響摘要

- **design-envelope §2 修訂**(owner 核准,§11 explicit-PR 管道):rate-limit honoring 從單一「bounded backoff」改為 **per-source 語意**——短窗口型(Finnhub 60/min)做一次 bounded `Retry-After` backoff;block 型(EDGAR 429 ≈ 10 分鐘 IP 封鎖,到期前重試會延長封鎖)由 client 層預防性 throttle 承擔,429 落地即 legible fail-fast。這是治理文件層級的變更,未來所有 retry 設計都引用新語意。
- **retry 政策收斂為 2 total attempts**(single retry,§2 合規):`retry_transient` 從 spec 原定的 3 次改為 2 次——趁零 production caller 時修正,DEV-137/DEV-69 將直接繼承合規政策。凍結樹自有的 3 次維持到 DEV-139 sunset。
- **三份 ADR(0011/0012/0013)全面重寫為 forward-looking decision records**:規則 + rejected alternatives,移除所有 diff 敘事——這同時消滅了兩處不實的變更範圍描述(m-2.1)與一個錯誤的 vendor 行為宣稱(M-2.1)。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 3 review + 3 fix |
| 發現 issues 總數 | 20(Quality 18 + Spec 2)|
| Blocking | 1/1 fixed |
| Major | 3/7 fixed;3 owner-dismissed(M-1.1/1.2/1.3);1 deferred to DEV-137(M-1.5)|
| Minor | 9/9 fixed |
| Suggestion | 1/1 adopted |
| Spec findings (SP-) | 2/2 fixed |
| 文件修正 | 10 檔(3 ADR、envelope、2 README、sec_core.md、agent_architecture.md、2 docstring)|

## Spec Conformance(Spec 軸)

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Missing | User Story 9「失敗的 ticker 在總結報表標示為 `failed` 而非 `skipped`」+ Testing Decisions 的 `main()` seam | fixed(round 1)|
| SP-1.2 | Misimplemented | Testing Decisions「唯一新 seam:config 模組的公開常數」 | fixed(round 1;以 spec 修正案收斂——DEV-141 補 dated correction 授權 `test_retry.py` 為第二個新 seam)|

Round 2 Spec 軸確認 2/2 resolved、0 新 findings、修訂後 spec(2 attempts、429 fail-fast、seam 授權)全項 ✅;round 3 起 Spec 軸無 open findings,依 dispatch criteria 停止。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/common/errors.py` | 新的共用錯誤 taxonomy contract(`FinLabError` + 四個唯一定義類別) | |
| 2 | `backend/common/config.py` | 新的 repo 錨定路徑 resolver contract(四個 env-可覆寫 resolver) | |
| 3 | `backend/common/retry.py` | 新的唯一 retry 政策(tenacity,2 attempts,`TransientError` only) | |
| 4 | `backend/common/sec_core.py` | 共用類別改自 errors.py 引入、`SECError(FinLabError)`、`RateLimitError` 呼叫端去 SEC 化 | ⚠️ |
| 5 | `docs/design-envelope.md` | §2 rate-limit 語意修訂(治理 SSOT) | ⚠️ |
| 6 | `docs/adr/0011-*.md` / `0012-*.md` / `0013-*.md` | 三個決策的 forward-looking records | |
| 7 | `backend/ingestion/fundamentals_pipeline/errors.py` | 只留 subsystem 特有錯誤(DataValidation/Schema) | |
| 8 | `backend/ingestion/sec_filing_pipeline_html/{filing_store,__main__,pipeline}.py` | 凍結樹內 spec 授權的最小變更:路徑預設改 config、4 處 handler 改寬 | |
| 9 | `backend/ingestion/sec_text_pipeline/filing_store.py`、`backend/agent_engine/tools/sec_filing.py`、`backend/api/main.py`、`.../duck_db/connection.py` | 其餘路徑消費端改 import config | |
| 10 | `backend/scripts/embed_sec_filings.py` | 刪外層手寫 retry;失敗誠實標 `failed` + exit 1 | ⚠️ |
| 11 | `backend/tests/common/{test_config,test_errors,test_retry,test_sec_core}.py` | 新 seam 測試(路徑 CWD 無關性/env 覆寫、跨 subsystem 同一物件斷言、2-attempt 行為) | |
| 12 | `backend/tests/ingestion/.../integration/test_ingest.py` | `"failed"` 斷言 + 單次嘗試證明(CI integration step 執行) | |

## 所有修正問題詳解

### B-1.1 / SP-1.1(Blocking)
- **問題:** embed script 失敗狀態 `"skipped"`→`"failed"` 改名後,既有 integration test(`test_ingest.py:248`)仍斷言舊字串。預設 pytest addopts 排除 `integration` marker,本地 981 passed 完全看不到;CI 的獨立 integration step 必掛。兩個不同 model reviewer 各自獨立發現。
- **修法:** 斷言改 `"failed"`;新增以 `call_args_list` 計數證明永久失敗 ticker 只被嘗試一次(外層 retry 確實移除);測試改名 `test_batch_cli_failure_isolation_and_summary`。
- **影響:** 消除 PR 上必然的 CI 失敗;測試從驗證舊行為轉為驗證 spec 要求的新行為。
- **驗證:** Spec 軸 round 2 逐行確認斷言與 script 行為一致、positional-arg 計數方式正確;repo-wide grep 無殘留相關 `"skipped"` 斷言。(Qdrant 不在本機,實際執行留給 CI。)

### M-1.4(Major)
- **問題:** retry 政策 `stop_after_attempt(3)` 與 envelope §2「single retry」直接衝突;429 fail-fast 的 §2 合規論述當時尚未成立。3 這個數字沿襲自兩套既有手寫實作,grill session 與 ADR 都沒對過 §2。
- **修法:** owner 裁定 A 案——改為 `stop_after_attempt(2)`,docstring 引 §2;`test_retry.py` 斷言同步改 2;DEV-141 spec 補 dated 修正。
- **影響:** 共用政策在有第一個 caller 之前就合規;避免把與 SSOT 衝突的數字寫進永久 ADR。
- **驗證:** `test_retry.py` 3 tests pass(成功於第 2 次/耗盡於第 2 次/非 transient 僅 1 次);repo grep 無殘留 3-attempt 斷言(凍結樹除外)。

### M-2.1(Major,M-1.4 的後續)
- **問題:** ADR-0013 用來關閉 429 爭議的前提——「edgartools 會在 429 到達前先跑 exponential backoff」——經比對 vendored 5.17.1 原始碼為**錯誤**(`TooManyRequestsError` 不在 retry predicate;vendor 明文「Do NOT retry immediately」)。錯誤宣稱源自 main 上既有的測試 docstring,被未經查證地寫進 ADR。
- **修法:** owner 裁定 A 案——(a) envelope §2 修訂為 per-source 語意;(b) 過時測試 docstring 依實際 vendor 行為重寫(測試邏輯不動);(c) ADR-0013 重寫,移除錯誤宣稱。Round 3 殘餘(`sec_core.py` docstring、`sec_core.md` 設計註記兩處同款舊說法 + 易漂移的「8 req/s」精確數字)於 fix round 3 清除。
- **影響:** 429 fail-fast 行為不變且論述變得更強(vendor 自己就是這樣設計的);envelope/ADR/code/測試四者一致且全部屬實。
- **驗證:** 我逐行讀了 vendored `httprequests.py` 確認 Codex 的指控;修正後 repo-wide grep 所有舊說法 + 「8 req/s」歸零;981 tests pass。

### M-1.6 + ADR 風格指令(Major + owner directive)
- **問題:** 原 ADR 一份 ~800 字融合三個決策(標題自己就列了三個),且通篇 PR 敘事——owner 點出「ADR 是給未來設計者的決策參考,不是歷史記錄」。
- **修法:** 拆成 0011(路徑)/0012(taxonomy)/0013(retry)三份;全部重寫為「規則 + rejected alternatives + 壓縮 context + re-evaluate triggers」,移除所有 diff 敘事。Round 3 再修三處措辭(絕對化的「All retry behavior」加上凍結樹例外、`FinLabError` 普遍性宣稱收窄、Context 殘留的刪除碼特徵)。
- **影響:** 未來 DEV-137/69/135 的設計者可直接引用可遵循的規則;風格指令已存入長期 memory,約束之後所有 ADR。
- **驗證:** 191w/251w/293w,皆有 house-style 四段結構;m-2.1 的不實範圍宣稱隨敘事移除而消滅。

### m-1.1 / m-1.2 / m-2.2(Minor,文件同步債)
- **問題:** 三份文件仍描述已刪除的 API(`--max-retries`、`with_retry`、`retry.py`);fundamentals README 更把 rate limit 歸類為 `TransientError` 並示範 `YFinanceRateLimitError(TransientError)`——照做會讓 retry 政策誤重試 rate limit。
- **修法:** `backend/scripts/README.md`、`fundamentals_pipeline/README.md`、`docs/agent_architecture.md` 全部改為現況;rate limit 移出 `TransientError` 描述、新增 `RateLimitError` row、範例改用共用 `RateLimitError("yfinance", ...)`。
- **影響:** 消除三個「照文件做就出錯」的陷阱,其中 m-2.2 是唯一會直接導致行為錯誤的文件債。
- **驗證:** grep 無殘留舊 API 引用;內容與 `errors.py` 逐項核對一致。

### S-1.1 + m-3.2(Suggestion + Minor,同款過度宣稱)
- **問題:** `FinLabError` 的 docstring(module 與 class)及 ADR-0012 規則都宣稱涵蓋「所有 domain errors」,但 JIT retriever 的本地錯誤家族仍直接繼承 `Exception`(本 slice 明確不動)。
- **修法:** 三處全部收窄為「shared SEC/fundamentals taxonomy」;ADR-0012 加註未涵蓋家族指向 Re-evaluate。
- **影響:** 未來 handler 設計者不會誤信 `except FinLabError` 是萬用網。
- **驗證:** round 3 確認 docstring 兩處 ✅;m-3.2 修正後 ADR 內部自洽。

### m-2.4(Minor,audit trail)
- **問題:** `review-round-1.md` summary 記 10 項但正文漏抄 S-1.1 原文(orchestrator 轉錄疏漏)。
- **修法:** 原文 verbatim 補回 + restoration note。
- **影響:** audit trail 可單獨還原全部 findings。
- **驗證:** summary 計數與正文一致。

### m-3.1 / m-3.3 / m-2.3 殘餘(Minor)
- **問題:** 修正後的 vendor 敘述仍含易漂移精確數字(「8 req/s」——實際 limiter 在 `httpclient.py`、預設 9)與過寬的「waiting-then-retrying extends」;ADR-0013 的絕對化規則與自身凍結樹例外矛盾;Context 仍殘留刪除碼特徵。
- **修法:** 「throttles below the SEC cap」(不寫死數字);「retrying **before the block expires** extends it」;Decision 收斂為「All **new repo-owned** transient-retry behavior」並內嵌凍結樹例外;Context 壓縮為一句無特徵敘述。
- **影響:** ADR 不再隨 vendor 版本漂移而變錯;規則自洽。
- **驗證:** grep「8 req/s」歸零;ADR 三段規則交叉讀無矛盾。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `docs/adr/` | 一拆三 + forward-looking 全面重寫(0011/0012/0013) |
| `docs/design-envelope.md` | §2 rate-limit 語意修訂(per-source) |
| `docs/agent_architecture.md` | fundamentals 模組描述更新至現況 |
| `backend/agent_engine/docs/sec_core.md` | 429 設計註記改為正確的 vendor 行為 |
| `backend/scripts/README.md` | 移除 `--max-retries`,記錄現行語意 |
| `backend/ingestion/fundamentals_pipeline/README.md` | API 表更新 + rate-limit 分類修正 |
| `backend/common/README.md` | 模組表 + 三個 ADR 連結 |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Owner-dismissed | M-1.1/M-1.2(AGENTS.md 凍結規則 vs 本 slice) | owner 裁定:本 slice 即是被授權的 refactor,凍結限制不適用 | DEV-139 sunset 時整節刪除 |
| Deferred | M-1.5(embed/Qdrant 步驟暫無 retry 保護) | vectorizer 屬 sunset-bound 樹;batch 改寫是 DEV-137 章程內工作;§2 容許 operator 工具 manual retry | 已寫入 DEV-137 description 的前置資產段 |
| 條件監控 | `retry_transient` 零 caller(§0 time-boxed 例外) | DEV-137 為指定首發使用者 | DEV-137/DEV-69 description 均有 ⚠️ 移除檢查條款 |

## Final Verification Results

### Code Level

- [x] Unit Tests: `uv run pytest backend/tests/ -q` → **981 passed, 49 deselected**
- [x] Lint: `uv run ruff check --fix backend/` → All checks passed
- [x] Format: `uv run ruff format --check backend/` → 175 files clean
- [x] Type Check: pyright 19 errors — **全部 pre-existing**(edgartools type-stub 缺口,base commit 上同樣 19 個,經 stash 對照確認,非本變更引入)

### Behavior Level

- [x] Config seam(spec Testing Decisions):CWD 無關性(`monkeypatch.chdir`)、四個 env 覆寫、寫讀兩端同目錄 → `test_config.py` 7 tests pass
- [x] Taxonomy import surface:跨 subsystem 同一物件(`is`)斷言、`except FinLabError` 接兩家、batch 失敗隔離 → `test_errors.py` + `test_main.py` pass
- [x] Retry 行為:2 attempts 成功/耗盡/非 transient 不重試 → `test_retry.py` 3 tests pass
- [ ] Integration(`test_batch_cli_failure_isolation_and_summary`):本機無 Qdrant 未執行,斷言經兩軸 review 逐行核對 — **由 CI integration step 把關**

### Runtime / Observable Level

- [ ] **Manual Validation(spec 保留的手動項,PR checklist 收錄):** 從 repo root 與 /tmp 各啟動一次 uvicorn 與 ingestion CLI,確認讀寫同一個 `data/` 目錄

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/common/{errors,config,retry}.py` | retry 3→2(M-1.4);docstring 收窄(S-1.1) |
| `backend/common/sec_core.py` | `fetch_filing_obj` docstring 429 說法修正(M-2.1 殘餘) |
| `backend/tests/common/test_retry.py` | 2-attempt 斷言(M-1.4) |
| `backend/tests/common/test_sec_core.py` | 429 測試 docstring 依 vendor 實況重寫(M-2.1/m-3.1) |
| `backend/tests/ingestion/.../integration/test_ingest.py` | `"failed"` + 單次嘗試斷言(B-1.1) |
| `docs/adr/0011/0012/0013` | 拆分 + forward-looking 重寫 + 三處措辭修正(M-1.6/M-2.1/m-2.x/m-3.x) |
| `docs/design-envelope.md` | §2 per-source 修訂(M-2.1-A) |
| `docs/agent_architecture.md`、`backend/agent_engine/docs/sec_core.md`、3 份 README | 文件同步(m-1.1/m-1.2/m-2.2、M-2.1 殘餘) |
| `artifacts/current/code-review-loop/*` | 3 輪 review + 3 輪 fix 完整 audit trail(含 m-2.4 補正) |

## Learning Notes

### 採用的工程策略

- **Import-identity 測試作為「單一定義點」的可執行驗收**:`assert ClassA is ClassB`(跨 subsystem import 路徑)把 grep 人肉檢查變成機械斷言,round 2 的 regression sweep 直接複用它確認 taxonomy 未被 fixer 弄壞。
- **宣告式 retry 政策的修正成本**:M-1.4 的 3→2 修正只改一個數字加兩行測試——因為政策是宣告式的、且趁零 caller 時修。對照組:若三套手寫 loop 還在,同樣的修正要改三處。

### 權衡取捨

- **凍結樹 carve-out 如預期存活**:spec 預期「凍結樹只做最小 handler 改寬」,Spec 軸 round 2 byte-diff 證實 `pipeline.py` 僅 6 行、retry 內部零變更——但 ADR 描述這件事時兩度失真(m-2.1 低估範圍、m-3.3 絕對化規則),教訓是**範圍事實交給 diff 與 review 記錄,ADR 只寫規則**。
- **Expected-vs-actual:429 論述**:預期「引用既有測試 docstring 即可關閉 §2 衝突」,實際上該 docstring 本身是錯的(M-2.1)——省下的查證成本以一整輪 review 償還。

### 關鍵收穫

- **依賴行為的宣稱必須對 pinned 版本原始碼查證,docstring 不是證據**(M-2.1):錯誤說法在 main 的測試 docstring 裡存活了數週,被我未經查證寫進 ADR,直到 reviewer 讀 vendored source 才現形。寫進 durable 文件前,vendor 行為一律讀 `.venv` 內的實際版本。
- **改可觀察輸出時,grep 測試要跨所有 marker**(B-1.1):預設 addopts 排除的 marker 是盲區——本地全綠 ≠ CI 全綠。輸出字串/exit code/報表格式變更時,`grep -rn` 全 `backend/tests/`,不分 marker。
- **ADR 寫給未來的設計者,不寫給本次 PR 的 reviewer**(owner feedback + m-2.1/m-3.3):diff 敘事不只無用,還會製造不實宣稱(範圍描述隨後續 round 過時)。判準:「六個月後做設計的人需要這句嗎?」——此判準同時自動消滅了兩類事實錯誤。
- **治理衝突要在寫入前 stop-and-surface,不是寫入後揭露**(M-1.3/M-1.4):§11 的字面要求是先停下來問;自行在 ADR 裡 ratify 例外即使事後揭露,程序上仍是瑕疵。本次 envelope §2 修訂走了正確管道(owner 明示核准、同 PR 落地),對照出差異。
