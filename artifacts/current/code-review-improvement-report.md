# Code Review Improvement Report — DEV-134 Inspect view + CLI

> Loop: 2 rounds × 2 axes(quality / spec conformance,Codex gpt-5.6-sol)| Date: 2026-08-12
> Scope: `git diff origin/main...HEAD`,branch `feat/sec-filing-inspect-cli`(`046e047` 實作 + `1ec26d1` fix round 1)

## 收斂結果

| Round | Quality 軸 | Spec 軸 | 處置 |
|---|---|---|---|
| 1 | 1 Major + 3 Minor | 1 Blocking + 1 Major | 4 accepted(1 範圍收斂)、2 user 裁決不修 |
| 2 | 1 Minor(新) | 0 findings | round 1 fixes 4/4 驗證 resolved;新 Minor 經 user dismiss |

## Round 1 → fixes(commit `1ec26d1`)

- **M-1.1 CLI 無行為測試**(accepted,範圍收斂至 envelope §5 字面標準):新增 `test_main.py` — 三 mode 各一條 happy path + 壞 ticker legible-failure;`test_data_paths.py` 補新 resolver default/override。不重測 render 層已覆蓋的 case-insensitivity。
- **m-1.1 ticker `ValueError` traceback**:CLI boundary 改 catch `(FinLabError, ValueError)` → 一行 stderr + exit 1;壞 ticker 測試為回歸保護。
- **m-1.2 `_item_chars` 不可達分支**:簽名收斂為 `StructuredItem`(envelope §0 reachability)。
- **m-1.3 `filing_store.py` docstring 過時**:兩處 de-stale(inspect view 已落地;speculative listing 舉例移除)。

## User 裁決不修(記錄於 Linear DEV-134「Review 裁決紀錄」)

- **SP-1.1 absent prelude 未附 chars 數 — dismissed**:spec Render 規則明文僅 valid/reclassified 帶 chars 數,absent 定義即「無 prelude」;AC 縮寫措辭已改為「prelude 判定(valid/reclassified 附 chars 數)」消除歧義。
- **SP-1.2 CLI `--force` scope creep — declined,ratified 進 spec**:屬「比照 `_html` CLI 慣例」;抽查活躍變動中 detection(DEV-136)的必要 workflow。
- **m-2.1 新測試缺 type annotations — dismissed**:repo 906 test functions 僅 ~18% 標註,同 package 既有測試皆無標註慣例;收斂需 repo-wide sweep + lint rule 的獨立 chore,非本 slice 範圍。

## 最終驗證

- `ruff check backend/` ✅、`ruff format` 無變更 ✅
- `pytest backend/tests/`(fix round 後受影響套件 130 passed;full suite 於 ship 前再跑一次)
- 真實 filing 煙霧測試(AAPL FY2025):三入口 + cache hit/miss + 錯誤路徑皆人工驗證(見 session 紀錄)

## Learning Notes

- **Prelude 判定是 render 時推斷**:schema 凍結後,reclassified 狀態僅以 `prelude==""` + `blocks[0].heading==""` 表現 — `heading==""` 是 reclassify 唯一 marker(anchored heading 一律非空)。此 implicit contract 現已明文於 spec 與 `inspect_view.py` docstring。
- **Spec 軸的字面讀法 vs. 規範層級**:SP-1.1 顯示 AC 縮寫轉述會被 reviewer 當獨立要求;規範性條文(Render 規則)與 AC 縮寫需措辭一致,否則每輪 review 都會再撞一次。
- **測試標註的 case law**:§3.1 字面涵蓋測試,但 repo 實務(~82% 未標註、歷輪 review 放行)構成既成例外;要改變需 legislation(lint rule),不是單票 fix。
