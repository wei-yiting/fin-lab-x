# Code Review Improvement Report

> **Task:** PR #65 — feat(frontend): wire reasoning chips end-to-end, enable reasoning（segment 6/8, DEV-110 / DEV-169, branch `feat/enable-reasoning-e2e`）
> **Date:** 2026-08-19
> **Rounds:** 3（2 輪 review+fix、1 輪確認）
> **Reviewer model:** gpt-5.6-sol（Codex CLI，Quality 軸 + Spec 軸，read-only sandbox，`codex:codex-rescue` 轉發）
> **Fixer model:** claude-sonnet-5（general-purpose subagent）

## 架構影響摘要

- **Accessibility 宣告權責重新劃分**：原本 `ErrorBlock`（`role="alert"`）與 `LiveStatusAnnouncer`（`role="status"`）會在錯誤時重複宣告；現在錯誤只由 `ErrorBlock` 負責，announcer 收斂為「完成通知」單一職責。已用真實瀏覽器驗證：觸發一次錯誤後，`role="status"` 區塊維持空字串，`role="alert"` 獨自帶著錯誤訊息（見下方 Runtime 驗證）。
- **`LiveStatusAnnouncer` 元件從獨立 atom 收斂為 `ChatPanel` 內的 inline region**：拿掉錯誤分支後，這個元件只剩一個呼叫點、一個可達事件（`{type: "finish"}`，已經不是真正的 union），違反本 repo 自己的「第二次出現才抽取」規則（`docs/frontend_chat_architecture.md` L91）。已刪除 `LiveStatusAnnouncer.tsx`、`live-status-text.ts` 與其測試檔，架構文件的 atoms 分類表與 composition graph 同步更新。
- **`ToolCard` 的 `aria-hidden` 被 revert**：原 PR 對整個 tool card 加上 `aria-hidden="true"`，理由是「announcer 會用文字宣告 tool transitions」——但這個宣告從未實作（announcer 自己的文件明確寫著 tool transitions 延後處理）。這是本輪發現最嚴重的問題：一個會把焦點帶進 `aria-hidden` 子樹的可聚焦元素，且承諾的替代方案不存在。已 revert，恢復到本 PR 之前的可存取行為。
- `CONTEXT.md` 新增的 `Reasoning transcript` glossary 詞條原本描述了 segment 7（Langfuse root-span persistence）才會實作的行為，已在本 segment 移除；等 segment 7 落地時再補。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 3 |
| Quality 軸 issues 總數 | 12（跨 3 輪，含 1 個殘留項延續） |
| Blocking | 0/0 |
| Major | 8/8 fixed |
| Minor | 4/4 fixed |
| Suggestion | 0/0 |
| Spec findings (SP-) | 3/3 fixed |
| 文件修正 | 4 檔（`CONTEXT.md`、`docs/frontend_chat_architecture.md`、`frontend/src/components/atoms/README.md`、`frontend/src/components/pages/README.md`） |

## Spec Conformance（Spec 軸）

> 與 Quality 軸並列呈現，不合併排序。三筆 Spec 發現與 Quality 軸的 M-1.2、M-1.1、M-1.5 分別指向同一個底層缺陷——兩個以不同問題角度（「程式碼好嗎」vs「符合 spec 嗎」）獨立運作的 reviewer 收斂到同一組檔案，是本輪發現最強的信心訊號，不是重複。

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Misimplemented | DEV-169 review question：「are the AssistantMessage/ChatPanel wiring...the LiveStatusAnnouncer accessibility surface...correct?」——`handleRegenerate` 未清除 `lastSSEEvent`，違反 review question 本身 | Fixed（Round 2 確認）——與 M-1.2 同一缺陷 |
| SP-1.2 | Scope creep | DEV-110 segment 6 定義：「wire up the chips, a11y announcer」——`ToolCard` 的 `aria-hidden` 不是 wiring 所需的 plumbing | Fixed（Round 2 確認）——與 M-1.1 同一缺陷 |
| SP-1.3 | Scope creep | DEV-169 scope note：「Not in scope: the reasoning-transcript/Langfuse root-span persistence (segment 7)...untouched by this diff」——`CONTEXT.md` 卻描述了這個行為 | Fixed（Round 2 確認）——與 M-1.5 同一缺陷 |

Round 3 額外請 Spec reviewer 針對 M-2.1（inline 掉 `LiveStatusAnnouncer` 元件）給出獨立判斷：是否違反 DEV-169 review question 逐字提到「the `LiveStatusAnnouncer` accessibility surface」。結論：不算 Misimplemented——具名元件邊界是實作細節，spec 真正要的（完整的 lifecycle 宣告行為）並未流失。Spec 軸全程 0 個新發現在 Round 2、Round 3。

## Reading Guide

> 給人類 reviewer 的建議閱讀順序，依 contracts/types → core logic → wiring → docs → tests。`⚠️` 標記本輪 review 有實質修正、或觸及 accessibility/domain-SSOT 的檔案。

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/agent_engine/agents/profiles/*/orchestrator_config.yaml`（5 檔） | `reasoning: "off"` → `"on"`，本 segment 的行為開關；review 全程無發現 | |
| 2 | `frontend/src/lib/reasoning-chips.ts` | reasoning/tool part 判斷式與 chip 狀態衍生邏輯，`AssistantMessage` 依賴的共用型別/predicate | |
| 3 | `frontend/src/components/organisms/ToolCard.tsx` | Tool 呼叫卡片；`aria-hidden` 被加上又被 revert，是本輪最重的 accessibility 發現（M-1.1/SP-1.2） | ⚠️ |
| 4 | `frontend/src/components/organisms/ErrorBlock.tsx` | 加上 `role="alert"`，成為錯誤宣告的唯一負責者（M-1.3/M-1.4 的解法核心） | ⚠️ |
| 5 | `frontend/src/components/organisms/AssistantMessage.tsx` | 本 PR 的主要功能：把 `reasoning` message part 映射成 `ReasoningChip` | |
| 6 | `frontend/src/components/pages/ChatPanel.tsx` | 中樞：`useChat` 生命週期、chip 計時/展開狀態、inline 化後的 completion announcer region、Regenerate 重設修正 | ⚠️ |
| 7 | `frontend/src/components/templates/MessageList.tsx` | 把 chip 相關 props 往下傳遞的 layout shell | |
| 8 | `frontend/src/index.css` | 拿掉重複的 `.sr-only`（M-2.2），改用 Tailwind 內建 utility | |
| 9 | `CONTEXT.md` | Domain glossary（SSOT）；`Reasoning transcript` 詞條的越界宣告已移除（M-1.5/SP-1.3） | ⚠️ |
| 10 | `docs/frontend_chat_architecture.md`、`frontend/src/components/atoms/README.md`、`frontend/src/components/pages/README.md` | 架構文件與元件文件；因 `LiveStatusAnnouncer` inline 化（M-2.1）同步更新分類表、composition graph、檔案清單 | |
| 11 | `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx`、其餘 `__tests__/*`、`frontend/tests/e2e/critical/stop-during-reasoning-then-resend.spec.ts` | 涵蓋 chip 生命週期、announcer 行為、interrupted-turn regression、真實瀏覽器 abort→resend | |

## 所有修正問題詳解

### M-1.1 / SP-1.2（Major，兩軸互證）
- **問題：** `ToolCard` 整張卡片（含可聚焦的展開觸發鈕）被加上 `aria-hidden="true"`，理由寫著「`LiveStatusAnnouncer` 會用文字宣告 tool transitions」——但這個宣告從未實作，`LiveStatusAnnouncer` 自己的文件明講 tool transitions 延後處理。等於拿掉螢幕報讀器對 tool 名稱、狀態、結果的存取，且沒有真的替代方案。
- **修法：** Revert `aria-hidden`，移除失實的理由註解，移除斷言 `aria-hidden` 存在的測試，修正 README 對應敘述。
- **影響：** 恢復本 PR 之前的可存取行為；tool card 重新可被螢幕報讀器讀到。
- **驗證：** `pnpm -C frontend test`（263/263）；Round 2/3 兩位 reviewer 各自確認 `aria-hidden` 已消失、無孤兒引用。

### M-1.2 / SP-1.1（Major / **Blocking**，兩軸互證）
- **問題：** `handleSend`、`handleRetry`、`handleClearSession` 都會清除 `lastSSEEvent`，唯獨 `handleRegenerate` 沒有——第一次完成後，live region 卡在 `"Response complete"`，Regenerate 期間第二次完成可能不會再被螢幕報讀器偵測到（同一段文字，沒有真的 DOM mutation）。
- **修法：** 在 `handleRegenerate` 觸發 request 前呼叫 `setLastSSEEvent(null)`（後續 M-2.1 改名為 `setResponseComplete(false)`），與其他三個 handler 一致。新增 integration test：完成一次 → Regenerate → live region 清空 → 第二次完成 → 再次宣告。
- **影響：** Regenerate 流程下 accessibility 宣告恢復正確。
- **驗證：** 新測試通過；Round 2/3 confirm。

### M-1.3 + M-1.4（Major，合併修正）
- **問題：** 錯誤發生時，`ErrorBlock`（`role="alert"`）與 `LiveStatusAnnouncer`（`role="status"`，文字改成 `"Error: stream interrupted"`）同時宣告，螢幕報讀器可能聽到兩次。這之所以可能，是因為 `AnnouncedEvent.errorText` 是一個沒有任何 producer 會真的填值的欄位（design-envelope §0 reachability 違規），只在測試裡被人工塞值。
- **修法：** `ErrorBlock` 的 `role="alert"` 成為錯誤宣告的唯一負責者；`live-status-text.ts` 移除 `errorText` 欄位與 `status === "error"` 分支，`AnnouncedEvent` 收斂成 `{ type: "finish" }`；`LiveStatusAnnouncer` 拿掉不再需要的 `status` prop；相關文件註解與測試同步更新。
- **影響：** 消除雙重宣告；順帶清掉一個不可達的死分支。這個修正本身在 Round 2 觸發了 M-2.1（見下）。
- **驗證：** `pnpm -C frontend test`；**真實瀏覽器驗證**——用 e2e-preview 觸發一次真的錯誤（MSW 502），確認 `role="status"` 區塊維持空字串、`role="alert"` 獨自帶著錯誤訊息（詳見 Runtime 驗證）。

### M-1.5 / SP-1.3（Major，兩軸互證）
- **問題：** `CONTEXT.md` 新增的 `Reasoning transcript` glossary 詞條描述「reasoning 會在 turn 結束時寫入 root trace」——這是 segment 7（Langfuse root-span persistence）的行為，本 PR 沒有實作，且 DEV-169 明確排除在範圍外。
- **修法：** 移除該詞條與 `Chat turn` 詞條對它的引用；保留這個 diff 真的實作的 `Chat turn`、`Activity indicator`、`Stream stall` 等詞條。
- **影響：** Domain SSOT 恢復準確；不會誤導下一個讀 `CONTEXT.md` 的人以為 persistence 已經存在。
- **驗證：** Round 2/3 reviewer 確認詞條已移除，其餘詞條未受影響。

### M-1.6（Major，含 Round 2 殘留一筆）
- **問題：** `D22`、`S-chip-01/05/07`、`S-rsn-14`、`J-pres-01`、`DEV-109 ruling 11` 等 session-local 決策/情境代號散落在本 diff 新增的 8 處程式碼、測試、CSS 註解裡——這些代號離開產生它們的規劃 artifact 就毫無意義。Round 1 修正後，Round 2 reviewer 發現 Round 1 fixer 自己新寫的測試註解又混進了 `(M-1.2/SP-1.1)`（諷刺地是同一種模式的再犯）。
- **修法：** 全部替換為描述性文字或直接刪除；Round 2 額外清掉那筆自我指涉的殘留。
- **影響：** 出貨程式碼不再依賴只有這次 review session 才看得懂的代號。
- **驗證：** Round 1/2 兩輪各自用 grep 交叉核對所有已知位置；Round 3 確認 cumulative diff 無殘留。

### M-2.1（Major，Round 2 新發現，設計層級修正）
- **問題：** M-1.3/M-1.4 拿掉錯誤處理後，`LiveStatusAnnouncer` 只剩一個呼叫點、一個可達事件——違反 `docs/frontend_chat_architecture.md` L91 的「第二次出現才抽取到 atoms/」規則。為一個「顯示一個字串」的行為維護兩個生產檔案、兩個獨立測試檔、README/架構圖詞條，超過了現在的行為所值得的重量。
- **修法：** Inline 進 `ChatPanel`：`AnnouncedEvent | null` state 改成 `useState<boolean>`，`<LiveStatusAnnouncer>` 換成 inline 的 `<div role="status" aria-live="polite" className="sr-only">`；刪除三個檔案；更新兩份 README 與架構文件的分類表/Mermaid 圖。保留既有 integration test 對同一行為的覆蓋（未新增重複測試）。
- **影響：** 移除一個現在的行為不值得的抽象層；架構文件與實際程式碼重新一致。Spec reviewer 在 Round 3 獨立確認：具名元件邊界是實作細節，不算違反 spec。
- **驗證：** `tsc -b`、`pnpm build`（確認無孤兒 import）、16/16 相關 integration tests、Round 3 兩軸 reviewer 確認無殘留引用；**真實瀏覽器驗證**確認 inline 後的 `role="status"` 區塊行為與修正前規格一致。

### M-2.2（Major，Round 2 新發現）
- **問題：** `index.css` 新增的自訂 `.sr-only` CSS block 與 Tailwind v4（已透過 `@import "tailwindcss"` 引入）內建的 `sr-only` utility 幾乎逐位元組相同（同樣的 `clip: rect(0,0,0,0)` 技法）。
- **修法：** 刪除自訂 block，改吃 Tailwind 自動產生的 utility。
- **影響：** 減少一份會漂移的重複實作。
- **驗證：** `pnpm build` 後確認產出的 CSS 仍含 Tailwind 版 `.sr-only{clip-path:inset(50%);...}`，行為等價。

### m-1.1（Minor）
- **問題：** `atoms/README.md` 指向 `molecules/ReasoningChip.tsx`，實際位置是 `organisms/ReasoningChip.tsx`（依 `AssistantMessage.tsx` 的 import 路徑核實）。
- **修法：** 修正兩處路徑引用與「往上一層」→「往上兩層」的敘述。
- **驗證：** 人工核對 import 路徑與檔案系統實際位置一致。

### m-1.2（Minor）
- **問題：** 本 diff 刪除了「interrupted turn 隱藏 Regenerate」的既有回歸測試，新的 reasoning-chip 測試沒有涵蓋這個情境；`ChatPanel.integration.test.tsx` 也沒有補上。
- **修法：** 在 `AssistantMessage.test.tsx` 的既有 `RegenerateButton visibility` describe 區塊內補回一個精簡測試。
- **驗證：** 新測試通過；grep 確認全套測試中不再有這個情境的覆蓋缺口。

### m-1.3（Minor）
- **問題：** 測試註解裡的 `"(DEV-106 review fix)"` 是流程中繼資料，拿掉後周圍說明本身已經完整。
- **修法：** 移除該引用，直接描述測試在防什麼（新的 send 清掉已凍結的 chip 時長）。

### m-2.1（Minor，Round 2 新發現）
- **問題：** `ChatPanel.tsx` 與 integration test 裡還留著描述「錯誤透過 `status === "error"` in `LiveStatusAnnouncer`」的舊註解——但這個分支在 M-1.3/M-1.4 就被拿掉了。
- **修法：** 改成正確敘述：disconnect/error 由 `ErrorBlock` 的 `role="alert"` 負責。`ChatPanel.tsx` 的部分隨 M-2.1 的 inline 化自然重寫；測試檔另外單獨修正。Orchestrator 事後又在測試檔 L889 抓到一處同類但沒被 reviewer 點名、且不構成失實宣稱的舊名稱殘留，判斷風險極低後直接修正，未另開一輪。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `CONTEXT.md` | 移除越界的 `Reasoning transcript` glossary 詞條與其交叉引用（M-1.5/SP-1.3） |
| `docs/frontend_chat_architecture.md` | 移除 `LiveStatusAnnouncer` 的 atoms 分類表項目、composition graph 節點與邊（M-2.1） |
| `frontend/src/components/atoms/README.md` | 修正 `ReasoningChip` 路徑（m-1.1）；移除 `LiveStatusAnnouncer`/`live-status-text.ts` 相關表列與測試提及（M-2.1）；ARIA surfaces 段落改為描述 inline region |
| `frontend/src/components/pages/README.md` | 移除對已刪除 `LiveStatusAnnouncer` 元件的引用（M-2.1） |

## 未處理項目

無——9 + 3（新發現）= 12 個 Quality 軸 issue、3 個 Spec 軸 finding 全數修正並通過確認。

## Final Verification Results

### Code Level

- [x] Unit Tests（frontend）: `pnpm -C frontend test -- --run` → **263/263 passed, 25/25 files**
- [x] Integration Tests（backend，觸及檔案）: `pytest backend/tests/integration/test_baseline_integration.py` → **12/12 passed**
- [x] Lint（frontend）: `pnpm -C frontend lint` → **0 errors**（1 個既有、與本次無關的 `mockServiceWorker.js` warning）
- [x] Lint（backend）: `uv run ruff check backend/` → **All checks passed**
- [x] Type Check（frontend）: `cd frontend && npx tsc -b` → **0 errors**
- [x] Format（frontend）: `pnpm -C frontend format:check` → **All matched files use Prettier code style**
- [x] Format（backend）: `uv run ruff format --check backend/` → **207 files already formatted**
- [x] Build: `pnpm -C frontend build` → **succeeds**（既有、與本次無關的 chunk-size warning）

### Behavior Level

> 本 segment 沒有 `bdd-scenarios.md`/`verification-plan.md`（未曾為此 slice 產出，且 PR 已開，artifacts 依慣例於 PR 前 untrack）。依 self-derived 流程：向使用者說明缺口後，聚焦本輪 review 實際修正的三個行為面（announcer/error 宣告權責、ToolCard 可見性、Regenerate 重設），並沿用 PR 描述裡既有的驗收基準。

- [x] Reasoning chip 全生命週期（串流 → 收合 → abort → resend）：既有 Playwright spec **真實 chromium 瀏覽器執行** → PASS（`stop-during-reasoning-then-resend.spec.ts`，6.8s）
- [x] Error 只被 `role="alert"` 宣告一次，`role="status"` 維持空字串：**真實瀏覽器手動觸發**（見下方 Runtime 驗證）→ 確認

### Runtime / Observable Level

- [x] Live browser check（e2e-preview，MSW-backed build）：觸發一次真實錯誤路徑（後端 502），DOM 檢查確認 `[role="status"]` = `{ariaLive: "polite", className: "sr-only", textContent: ""}`，`[role="alert"]` 帶著完整錯誤訊息與 Retry 按鈕；點擊 Retry 正常重試、無 console 例外（除預期中的 502）
- [x] App 冷啟動無 server/console 錯誤；`status` region 在初始（未送出訊息）狀態下即存在於 DOM

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `CONTEXT.md` | M-1.5/SP-1.3：移除越界的 Reasoning transcript 詞條 |
| `backend/agent_engine/agents/profiles/{analyst,baseline,graph,quant,reader}/orchestrator_config.yaml` | 無修正（`reasoning: "on"` 原樣通過兩軸三輪 review） |
| `backend/tests/integration/test_baseline_integration.py` | 無修正 |
| `docs/frontend_chat_architecture.md` | M-2.1：移除 `LiveStatusAnnouncer` 相關分類表項目與 composition graph 節點/邊 |
| `docs/frontend_dom_contract.md` | 無修正 |
| `frontend/src/__tests__/msw/fixtures/{index.ts,long-reasoning-then-text.ts,types.ts}` | M-1.6：`long-reasoning-then-text.ts` 的 session-local scenario id 清空 |
| `frontend/src/components/atoms/LiveStatusAnnouncer.tsx` | M-2.1：**已刪除**（inline 進 `ChatPanel`） |
| `frontend/src/components/atoms/live-status-text.ts` | M-2.1：**已刪除** |
| `frontend/src/components/atoms/__tests__/LiveStatusAnnouncer.test.tsx` | M-2.1：**已刪除**（行為由既有 integration test 覆蓋） |
| `frontend/src/components/atoms/README.md` | m-1.1、M-2.1：路徑修正 + 移除已刪除元件的表列 |
| `frontend/src/components/organisms/AssistantMessage.tsx` | 無修正 |
| `frontend/src/components/organisms/ErrorBlock.tsx` | M-1.3/M-1.4：確認為錯誤宣告唯一負責者（本身無需改動） |
| `frontend/src/components/organisms/ToolCard.tsx` | M-1.1/SP-1.2：revert `aria-hidden`，移除失實註解 |
| `frontend/src/components/organisms/__tests__/{AssistantMessage,ErrorBlock,ToolCard}.test.tsx` | m-1.2：補回 interrupted-turn regression test；其餘同步 M-1.1/M-1.6 的程式碼修正 |
| `frontend/src/components/pages/ChatPanel.tsx` | M-1.2/SP-1.1、M-1.3/M-1.4、M-2.1、m-2.1：Regenerate 重設、announcer inline 化、註解修正 |
| `frontend/src/components/pages/README.md` | M-2.1：移除已刪除元件引用 |
| `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` | M-1.2/SP-1.1（新測試）、M-1.6、m-1.3、m-2.1：新增/修正測試與註解 |
| `frontend/src/components/templates/{MessageList.tsx,__tests__/MessageList.test.tsx}` | 無修正 |
| `frontend/src/hooks/README.md` | 無修正 |
| `frontend/src/index.css` | M-1.6、M-2.2：codename 清理 + 刪除重複 `.sr-only` |
| `frontend/src/lib/reasoning-chips.ts` | 無修正 |
| `frontend/tests/e2e/TAGS.md` | 無修正 |
| `frontend/tests/e2e/critical/stop-during-reasoning-then-resend.spec.ts` | 無修正（真實瀏覽器執行通過） |

## Learning Notes

### 採用的工程策略

- **雙軸 review 的獨立收斂是真正的訊號，不是雜訊**：Quality 軸與 Spec 軸從「這段程式碼好嗎」與「這符合 spec 嗎」兩個完全不同的問題出發，各自獨立作業（互不可見對方輸出），卻精準收斂到同一組三個檔案（M-1.1/SP-1.2、M-1.2/SP-1.1、M-1.5/SP-1.3）。這比單一 reviewer 給出高信心分數更有說服力——下次遇到「這個 finding 到底該不該修」的猶豫，跨軸互證是比 reviewer 自報信心更硬的證據。
- **修正一個 finding 可能讓下一輪冒出新 finding，這是預期內的良性行為，不是 review 品質問題**：M-1.3/M-1.4 拿掉了 announcer 的錯誤分支，副作用是讓元件的正當抽象範圍縮小到「不值得抽取」的程度，Round 2 因此冒出 M-2.1。三輪 review-fix-confirm 的結構本來就是設計來抓這種「修正改變了程式碼形狀，讓原本合理的設計決策變得不合理」的連鎖效應。

### 權衡取捨

- **預期 vs 實際（`LiveStatusAnnouncer` 的抽象邊界）**：PR 原始設計把 announcer 抽成獨立 atom 是合理的——當時它要處理兩種事件（finish/error）並仲裁優先序，這是值得抽取的邏輯。M-1.3/M-1.4 修正之後，剩下的行為（「顯示一個固定字串」）不再撐得起獨立檔案。這裡的取捨不是「一開始設計錯了」，而是「fix 改變了計算，原本的判斷要跟著重算」——沒有把「我剛抽出來的元件」當作既定事實，而是重新用同一把尺（是否值得為單一呼叫點/單一事件抽取）衡量它。
- **考慮過「留著以防未來 tool-transition 宣告會用到」的說法，但判斷是 speculative generality 後拒絕了**：這個專案自己的 review 標準明講「an abstraction used in exactly one place is indirection, not abstraction」——為將來可能的需求預留結構，跟這條原則直接衝突，即使對象是 accessibility 這種「感覺應該要謹慎」的領域也一樣適用。

### 關鍵收穫

- **註解裡宣稱的理由要對照「被指名的對象」自己怎麼說，不能只信任註解本身**：`ToolCard.tsx` 的註解說「`LiveStatusAnnouncer` 會宣告 tool transitions」，但只要去讀 `LiveStatusAnnouncer` 自己的文件就會看到「tool-call transitions are deferred」——兩份文字互相矛盾，而矛盾本身就是訊號。這個檢查方式（不只讀當下這一行在說什麼，還去核對它引用的對象是否真的這麼做）抓到了本輪最嚴重的 accessibility 迴歸（M-1.1/SP-1.2）。
- **process/decision codename 的清理需要一次獨立的最終掃描，不能只靠「修每個 finding 時順手注意」**：M-1.6 在 Round 1 被系統性修正後，Round 1 fixer 自己新寫的測試註解又混進了一個新的自我指涉代號（`M-1.2/SP-1.1`）。連正在積極清理這個模式的人，都會在寫新程式碼時無意識地重犯——這代表這類規則最後要靠一次涵蓋全 diff 的 grep 掃描收尾，不能假設「這一輪修過了就不會再出現」。
- **靜態讀 diff 證明程式碼變了，不能證明 assistive tech 的實際行為是對的**：M-1.3/M-1.4 的修正在程式碼層面看起來直觀正確，但真正的驗證是在真實瀏覽器裡觸發一次錯誤、直接讀 DOM 上 `role="status"` 與 `role="alert"` 兩個節點的實際內容——這才確認了「不會重複宣告」不是我們讀 code 讀出來的推論，而是瀏覽器裡真的發生的事。
