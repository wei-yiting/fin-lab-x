# Code Review Improvement Report

> **Task:** PR #52 — dead-air placeholder（8 段 stacked train 的 segment 4，Linear DEV-110）
> **Date:** 2026-08-17
> **Rounds:** 3（2 個 fix round，第 3 輪兩軸皆零 findings 收斂）
> **Reviewer model:** `gpt-5.6-sol`（Codex，read-only，Quality 與 Spec 兩軸各自獨立 dispatch）
> **Fixer model:** Claude（general-purpose subagent，與 reviewer 無共享 context）

## 架構影響摘要

- **`ActivityPlaceholder` 的擁有權從 `MessageList` 移到 `ChatPanel`。** `MessageList` 現在收一個不透明的 `placeholder: ReactNode` slot，和它既有的 `emptyContent` / `errorContent` 同一個模式。舊的 `ReasoningIndicator` 是 `MessageList` 自己 import 並自己判斷要不要顯示的；現在可見性由 `ChatPanel` 透過 `useDeadAirPlaceholder` 推導後注入。架構文件的 composition graph 也跟著改正（m-2.2）。
- **Tool / reasoning part 的分類權交還給 AI SDK。** `reasoning-chips.ts` 原本手刻了 `isToolUIPart` 與 `isReasoningUIPart` 的邏輯，現在改為 delegate 給 `ai` 的官方 export。SDK 日後新增 part 形狀時，這裡不會再默默漂移（M-1.2）。
- **`REF_DEF_LINE_RE` 成為跨模組的單一定義，且行為被放寬。** 這條 regex 現在由 `markdown-sources.ts` 單獨持有，`AssistantMessage` 改為 import；同時放寬到 CommonMark 允許的最多三格縮排。這**改變了 `AssistantMessage` 的渲染行為** —— 縮排的 reference definition 現在也會被 strip（m-1.1、m-2.1）。
- **timing 常數不再可注入。** `useStallTimer` 的 `threshold` 與 `useDeadAirPlaceholder` 的 `graceMs` 參數移除，兩個 hook 直接讀 `@/lib/timing`。唯一的測試 seam 收斂成 F6 裁決指定的 module mock（M-1.4）。
- **捲動跟隨的觸發條件納入 placeholder 可見性。** `useFollowBottom` 的 scrollTrigger 從 `messages` 換成 memo-stable 的 `{ messages, hasPlaceholder }`（M-1.1）。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 3（Round 3 兩軸皆 0） |
| 發現 issues 總數 | 17（Quality 9、Spec 6、Orchestrator 2） |
| Blocking | 2/5 fixed（2 dismissed by user、1 closed as not-a-defect） |
| Major | 6/7 fixed（1 待人工裁決） |
| Minor | 5/5 fixed |
| Suggestion | 0/0 |
| Spec findings (SP-) | 2/6 fixed（2 dismissed、1 closed、1 待裁決） |
| 文件修正 | 6 |
| 測試數變化 | 169 → **211**（+42），檔案 21 → 23 |

## Spec Conformance（Spec 軸）

> 與 Quality 軸並列呈現，不合併排序。

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Misimplemented | 「文案（英文）：`Thinking…` / `Still working…`」 | **Dismissed（使用者裁定）** — 保留現行「文字 + `aria-hidden` CSS 點動畫」呈現 |
| SP-1.2 | Missing | 「其餘 3-state 與 chip 邏輯以 hook/component 單元測試覆蓋」 | **Fixed** |
| SP-1.3 | Missing | 「有且僅有 1 個 ChatPanel 整合測試 case…驗 wiring」 | **Fixed** |
| SP-2.1 | Misimplemented | 「全域單一 10s stall 碼表（**任何 stream part** 歸零）」 | **Dismissed（使用者裁定）** |
| SP-2.2 | Misimplemented | 「Train 疊完 tree 與 refactor 終態 byte-identical」 | **Closed** — 非本 PR 缺陷（見下方說明） |
| SP-2.3 | Misimplemented | 「300–800 行 gate…盡量遵守；兩段裁決超線」 | **待人工裁決** |

## Reading Guide

> 這是 slice PR 的導覽表 —— 不必從上到下讀整個 diff。
> 排序：contracts/types → core logic → wiring → tests。

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `frontend/src/lib/timing.ts` | 三個 timing 常數的唯一來源（10s stall、300ms grace、50ms throttle）；也是唯一的測試 seam | |
| 2 | `frontend/src/lib/reasoning-chips.ts` | 純推導層：什麼算「畫得出東西的 part」。四個 export，全部有消費者 | |
| 3 | `frontend/src/lib/markdown-sources.ts` | `hasVisibleReplyText` + 共用的 `REF_DEF_LINE_RE`。**改動會同時影響 placeholder 判斷與 `AssistantMessage` 的實際渲染** | ⚠️ |
| 4 | `frontend/src/hooks/useDeadAirPlaceholder.ts` | 三個 dead-air window 的可見性推導 + grace timer | |
| 5 | `frontend/src/hooks/useStallTimer.ts` | 全域 stall 碼表（wall-clock，防背景分頁節流） | |
| 6 | `frontend/src/components/atoms/ActivityPlaceholder.tsx` | 呈現層：兩種文案 + `aria-live="polite"` | |
| 7 | `frontend/src/components/pages/ChatPanel.tsx` | 接線：`useChat` → 兩個 hook → placeholder slot。含 `notifyActivityRef` 的順序處理 | |
| 8 | `frontend/src/components/templates/MessageList.tsx` | placeholder slot + 捲動跟隨觸發條件 | |
| 9 | `frontend/src/components/organisms/AssistantMessage.tsx` | 僅 2 行：改用共用 regex。**但這是本 PR 唯一改到既有渲染行為的地方** | ⚠️ |
| 10 | `frontend/src/index.css` | 點動畫 keyframes + `prefers-reduced-motion` 退化 | |
| 11 | `docs/frontend_chat_architecture.md`、三份 README | 文件同步 | |
| 12 | 各 `__tests__/` 與 `tests/e2e/` | 測試 | |

## 所有修正問題詳解

### M-1.1 — placeholder 可能掛在視窗外（Major）
- **問題：** `useFollowBottom(viewportRef, messages)` 只以 `messages` 為捲動觸發。Window B/C 的 placeholder 是在 grace timer 到期後才 mount，比開啟空窗的那次 `messages` 變動晚 300ms，屆時 `messages` 沒變 → 不捲動。transcript 超過一屏時，placeholder 會被附加在摺線以下，使用者在它本該覆蓋的那段空窗裡什麼都看不到。
- **修法：** `MessageList` 取 `hasPlaceholder = placeholder != null`（布林，不是每次 render 都新建的 ReactNode），以 `useMemo` 包成 `{ messages, hasPlaceholder }` 當 scrollTrigger。`shouldFollowBottom` 這個「使用者往上捲就別硬拉」的閘門完全沒動。
- **影響：** 這是**本 slice 自己引入的迴歸** —— 舊的 `ReasoningIndicator` 由 `(status, lastMessage)` 同步推導，永遠和 `messages` 變動同一個 commit mount，一定吃得到捲動。是 grace delay 造成了解耦。
- **驗證：** 新增 `MessageList` 迴歸測試（placeholder 在 `messages` 未變下 mount → 視窗捲到底），外加一個閘門 case（使用者上捲 1700px → 不被拉回）。Mutation 檢查：把 scrollTrigger 改回 `messages`，新測試失敗（`expected 2000, got 0`），其餘 10 個 `MessageList` 測試仍過。E2E 既有的兩支 `scroll-behavior` spec 也仍通過。

### M-1.2 — 重造 AI SDK 已導出的 type guard（Major）
- **問題：** `isToolPart` 手刻了 `ai` 已 export 的 `isToolUIPart` 邏輯；`isReasoningPart` 同樣重造了 `isReasoningUIPart`（後者 Codex 沒抓到，是 orchestrator 查 SDK export 清單時發現的）。而且該檔案的註解宣稱自己是「single source of truth for tool-part classification」—— 這句話是假的：`AssistantMessage.tsx:14` 有第三個形狀不同的 predicate，額外匹配純 `"tool"`。
- **修法：** 兩個 wrapper 改為 delegate 給官方 guard。`isToolPart` 前面保留 `typeof part.type !== "string"` 的早退 —— 因為 `isToolUIPart` 內部直接呼叫 `.startsWith()`，而 hooks 傳入的是結構型別、`type` 可能不存在；`isReasoningPart` 不需要，因為 `isReasoningUIPart` 的實作是 `part.type === "reasoning"`，對 undefined 安全。假的 SSOT 宣稱改寫為事實描述。
- **影響：** SDK 未來新增 part 形狀時分類邏輯不會漂移。`AssistantMessage` 的 predicate 刻意未動 —— 它的 `"tool"` 分支目前只有自己的 test fixture 餵得到，統一它會連帶改 fixture，超出本 slice。
- **驗證：** Context7 查證 `ai@6.0.142` 的官方簽章與實作；Round 2/3 reviewer 均確認 delegation 正確且 total。新增的 `reasoning-chips.test.ts` 涵蓋 `dynamic-tool`、純 `"tool"` → false、非字串/缺席 `type` → false。

### M-1.3 — `ActivityPlaceholder` 的 doc comment 與實作不符（Major，部分修正）
- **問題：** 註解寫「fills the **two** windows … submit → first content, chip collapse → reply text」，但 hook 實作**三**個 window（多了 tool round 完成 → 下一個內容）。又寫「never rendered while a tool card … is on screen」，而 window C 的定義正是**顯示在已完成的 tool cards 底下**。
- **修法：** 改寫為三個 window，並區分「執行中的 tool card」（抑制）與「已完成的 tool cards」（window C 正是在其下方渲染）。markup、文案、行為皆未動。
- **影響：** 這支元件是整個 PR 的門面，錯誤註解會直接誤導 human review gate 上的讀者。
- **驗證：** Round 3 兩軸確認文件與實作一致。
- **未採納的另一半：** reviewer 主張依 `docs/frontend_chat_architecture.md` L88 的「inline a new visual element at first use」規則，應把元件 inline 掉。**使用者裁定保留** —— 用途明確的 element 本來就該有自己的邊界，該規則管的是投機性抽象，不是「只有一個消費者」這個表面事實。

### M-1.4 — production hook 暴露不可達的測試專用參數（Major）
- **問題：** `useDeadAirPlaceholder` 的 `graceMs` 沒有任何 caller 或測試覆寫過，其 `graceMs <= 0` 的兩條分支完全不可達；`useStallTimer` 的 `threshold` 唯一消費者是「測試這個參數」的那個測試，循環論證。F6 裁決指定的 seam 是 `vi.mock("@/lib/timing")`，integration test 早就在用。
- **修法：** 兩個參數移除，hook 直接讀 `@/lib/timing`；刪除不可達分支與那個 param-only 測試。
- **影響：** 消除 production 程式碼裡的測試專用接縫與死碼。
- **驗證：** 確認 module mock 仍能驅動 hook —— stall integration case 在 5s timeout 內斷言到降級文案，只有 mock 的 700ms 閾值才做得到，真實的 10s 不可能。

### m-1.1 — reference-definition strip 重複且漏掉縮排（Minor）
- **問題：** 本 PR 導出了 `REF_DEF_LINE_RE` 並寫下「Reuses the exact stripping pipeline AssistantMessage applies」，但 `AssistantMessage.tsx:112` 仍內嵌同一段 literal，兩邊會漂移。另外 regex 錨在第 0 欄，而 CommonMark 允許最多三格縮排 —— `"   [1]: https://…"` 會讓 `hasVisibleReplyText` 回傳 `true`、提前關閉 window A，但畫面其實什麼都沒渲染。
- **修法：** `AssistantMessage` 改為 import 共用常數；regex 放寬為 `/^ {0,3}\[(\d+)\]:?\s+\S+.*$/gm`。
- **影響：** 「兩邊同一條 pipeline」從宣稱變成事實。**注意這連帶改變了 `AssistantMessage` 的渲染行為**（縮排的 definition 現在也會被 strip）。
- **驗證：** `markdown-sources.test.ts` 新增 0/3/4-space 邊界（4-space 是 code block，會渲染 → `true`）。`/g` regex 的 `lastIndex` 安全性已確認：兩個 call site 都用 `String.replace`（會重置），全域無 `.test()` / `.exec()`。

### m-1.2 — `atoms/README.md` 事實錯誤（Minor，部分修正）
- **問題：** 兩處錯誤，都在本 PR 新建的檔案裡。`StatusDot.tsx` 寫「used in `ChatHeader`」，實際消費者是 `molecules/ToolRow.tsx:48`；Testing 段宣稱「Atoms have unit coverage in `__tests__/<Component>.test.tsx`」，但當時 `atoms/__tests__/` 根本不存在。
- **修法：** 更正消費者；Testing 段改寫為實際狀態。
- **影響：** README 是 DEV-106 AC 明文要求的產出，內容錯誤等於 AC 未達成。
- **未採納的另一半：** reviewer 主張刪掉 `atoms` 與 `pages` 兩份 README。**不採納** —— 直接違反 DEV-106 AC「動到的模組 README（streaming、hooks、agents、atoms/pages）與新 code 同步」。Spec 要的是修 drift，不是刪檔案。

### m-1.3 — throttle 註解的 frame 數算錯（Minor）
- **問題：** 本 PR 把原本正確的註解「about 3 frames at a 60Hz display」改成「One frame's worth of coalescing」。50ms 在 60Hz 是約 3 frames，改後是錯的。
- **修法：** 改為「Coalescing into a ~20Hz update rate (about 3 frames at a 60Hz display)」。
- **影響：** 這個常數是效能調校的參考點，錯誤描述會誤導後續調整。
- **驗證：** Round 3 確認。

### m-2.1 — 放寬後的 regex 在消費端沒有迴歸防護（Minor）
- **問題：** m-1.1 讓 `AssistantMessage` 也開始 strip 縮排 definition，但沒有任何測試守著。新增的測試只驗 `hasVisibleReplyText`；`AssistantMessage` 既有的 citation cases 全是第 0 欄。把 `AssistantMessage` 改回舊 literal，所有測試依然全綠。
- **修法：** 把既有的 `streaming strips definition lines (no flicker)` case 改成 `test.each`，涵蓋 `""` 與 `"   "` 兩種縮排，斷言原始 definition URL 在串流期間不會出現。
- **影響：** 跨檔案行為變動終於有了真正的守門員。
- **驗證：** Mutation 檢查：把 regex 縮回 `/^\[(\d+)\]…/`，18 個測試中恰好 1 個失敗；regex 已還原。

### m-2.2 — 架構圖的元件擁有權過期（Minor）
- **問題：** composition graph 仍寫 `MessageList --> ActivityPlaceholder`，但 `ActivityPlaceholder` 的唯一 production import 者是 `ChatPanel.tsx:14`。這條邊在本 PR 之前是正確的（當時 `MessageList` 確實自己 import `ReasoningIndicator`），擁有權隨這次改動移轉了。同一張圖已把 `EmptyState`、`ErrorBlock` 這些同為 slot 的內容歸給 `ChatPanel`，慣例自相矛盾。
- **修法：** 邊改為 `ChatPanel --> ActivityPlaceholder`，置於其他 slot 邊旁；§2.1 的 layer diagram 有同樣缺口，一併補上。
- **影響：** 這張圖自稱記錄「actual compositions」，錯了就失去存在意義。
- **驗證：** import 關係實查確認。

### O-2.1 — `reasoning-chips.ts` 導出無人使用的符號（Major，orchestrator 提出）
- **問題：** 該模組 export 六個符號，只有四個有外部消費者。`isSuppressedChip` 只被同檔案的 `isRenderablePart` 使用，`ReasoningPartLike` 外部零引用。而 PR 描述明文宣稱「ships only the dead-air-relevant exports…so this PR doesn't ship unused exports」—— 該敘述為假，且 `isSuppressedChip` 名字裡就有 Chip，正是描述聲稱推遲到 segment 5 的類別。**兩個 Codex reviewer 都沒抓到。**
- **修法：** 兩者都改為 module-private。
- **影響：** 消除不該公開的 API surface，並讓 PR 描述變成真的。
- **驗證：** `grep "^export"` 確認現在只剩四個函式加 `ChatMessageLike`；`tsc -b --force` 通過 —— 編譯器並不要求 `ReasoningPartLike` 因出現在 `isReasoningPart` 的 type predicate 而保持公開。

### O-2.2 — renderability 測在錯的層級（Major，orchestrator 提出）
- **問題：** `reasoning-chips.ts` 是 78 行純函式 —— 最好測的東西 —— 卻**完全沒有測試檔**。它的行為改在 `useDeadAirPlaceholder.test.ts` 裡間接驗，每個 case 都要搭一整組 fixture、`renderHook`、fake timer `act()`：一條 10–15 行，直接測純函式只要 2 行。15 個 hook case 裡約 5 個加上一個 8 形狀迴圈都是這樣。這不只是「測太多」，是斷言的意圖被無關的機械包裝蓋住。
- **修法：** 新增 `reasoning-chips.test.ts`（35 cases）直接測四個純 predicate；hook 測試瘦身為只驗它才驗得了的東西（window A/B/C 轉換、grace 抑制、兩個 micro-gap、invisible trailing part、status gating），並留註解指明形狀列舉的歸屬。
- **影響：** 測試層級歸位。順帶補上原本**完全不存在**的覆蓋：`isToolPart` 對純 `"tool"` 與非字串 `type`、`dynamic-tool` 的 renderability、`**References**` header、3-space 縮排 ref-def。
- **驗證：** Fixer 交出 coverage ledger 逐條對照；Round 3 **兩軸各自獨立**核對後皆確認無覆蓋遺失。
- **誠實記錄：** orchestrator 原本預期這會壓低行數，**預測錯誤** —— 淨增 135 行（新檔 +132，hook 減 45），因為新測試補的是原本沒有的覆蓋。測試品質改善屬實，行數紅利不存在。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `frontend/src/components/atoms/ActivityPlaceholder.tsx` | doc comment：兩個 window → 三個；區分執行中 / 已完成的 tool card |
| `frontend/src/components/atoms/README.md` | `StatusDot` 消費者更正為 `molecules/ToolRow`；Testing 段改寫為實際狀態 |
| `frontend/src/lib/timing.ts` | throttle 註解 frame 數更正（1 → ~3 frames @60Hz / ~20Hz） |
| `frontend/src/lib/reasoning-chips.ts` | 移除不實的 "single source of truth" 宣稱，改為敘明 `AssistantMessage` 另有 predicate |
| `frontend/src/lib/markdown-sources.ts` | 說明 `^ {0,3}` 的 CommonMark 依據與共用關係 |
| `docs/frontend_chat_architecture.md` | composition graph 與 layer diagram 的 `ActivityPlaceholder` 擁有權改為 `ChatPanel` |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Dismissed（使用者裁定） | SP-1.1：placeholder 未渲染字面的 `Thinking…` / `Still working…` | 現行呈現是「文字 + `aria-hidden` CSS 點動畫」，視覺上等同；`aria-hidden` 包住動畫是正確的 a11y 決定（否則 live region 會被高頻變動洗版）。字面省略號活在 reasoning chip header（segment 5/6） | 無 |
| Dismissed（使用者裁定） | M-1.3 後半：把 `ActivityPlaceholder` inline 掉 | 用途明確的 element 應有自己的邊界；extension rule 管的是投機性抽象 | 無 |
| Dismissed（spec 衝突） | m-1.2 後半：刪除 `atoms` / `pages` README | 直接違反 DEV-106 AC | 無 |
| Dismissed（使用者裁定） | SP-2.1：`start-step` / `finish-step` 不會歸零 stall 碼表 | 技術前提經 orchestrator 查 `ai@6.0.142` 原始碼確認為真（`write()` 寫在各 case 內，這兩個 case 沒有）。但兩者都是畫面上不可見的協定框，為它們把「已等很久」的訊號清掉更糟；且建議修法（攔 raw chunk）會違反 DEV-106「純 derivation：一切輸入 = `useChat` 的 `(status, messages)`」這條根本要求 | 若日後 chip header 需要更細的活動訊號，應在 DEV-106 的 derivation 契約內重新設計，而非加 side channel |
| Closed（非缺陷） | SP-2.2：修正破壞了與終態 tree 的 byte-identity | 使用者裁定終態 tree 只是 base、不是權威；真正 merge 的是這些 PR，屬於 slice scope 的問題就在 slice 裡修 | **有下游工作**：segment 5–8 是從終態 tree 切出來的，需 rebase 或重切以接上修正後的 segment 4 |
| **待人工裁決** | SP-2.3：超出 300–800 行 slice gate | 目前淨 diff 約 1,156 行。**開 PR 時就已 1,210 行**（超線 51%），非 review 造成；review 淨增約 135 行。組成上 production source 僅 424 行，其餘是測試 | 兩條路：(a) 把 `reasoning-chips.ts` + `markdown-sources` renderability 切成獨立一段；(b) 補一次裁決，把 segment 4 列為第三個獲准超線例外，理由是 source 穩在 envelope 內、超的是測試質量 |
| Coverage note | BDD S-place-05「降級文案已顯示後按 Stop」 | 兩個構成要素各自有覆蓋（stall 降級：strengthened integration case；placeholder 期間 Stop：新增的 integration case），但「降級後才 Stop」這個組合沒有直接測試 | 低風險組合；若要補，可在既有的 placeholder-stop case 上加長靜默時間 |

## Final Verification Results

### Code Level

- [x] Unit Tests：**211/211 通過**（23 files）— 起點為 169/21
- [x] Lint：**0 errors**，1 warning（`frontend/public/mockServiceWorker.js` 的 unused eslint-disable，自 PR #12 即存在，本 PR 未動 `frontend/public/`）
- [x] Type Check：`pnpm exec tsc -b --force` **通過**
- [x] Format：`pnpm format:check` **通過**
- [x] Build：`pnpm build` **通過**（僅既有的 >500kB chunk-size advisory）

### Behavior Level（BDD — 來源：終態 branch 的 `bdd-scenarios.md`，Feature F6′）

- [x] **S-place-01**（submit 後立即出現 placeholder，首個內容抵達即消失）：E2E 直接實證 —— `slow-start-stream.spec.ts` 通過，實際 render `activity-placeholder`、文字 `Thinking`、內容抵達後消失
- [x] **S-place-02**（300ms grace 分流：真空窗覆蓋、chip→tool 微空檔不閃現）：`useDeadAirPlaceholder.test.ts` 的 window B/C 與兩個 micro-gap case
- [x] **S-place-03**（tool 執行中不出現 placeholder）：hook 測試「hidden while a tool card is the last part」與「window (c) suppressed while any sibling tool part is still in flight」
- [x] **S-place-04**（stall 降級與恢復）：唯一那個 ChatPanel integration case，經 mutation 驗證（停用 reset wiring 後該 case 失敗、其餘 6 個仍過）
- [~] **S-place-05**（長時間靜默下 Stop 逃生）：**部分覆蓋** —— placeholder 期間 Stop 會留下 Interrupted marker 已有 integration case；「降級文案出現後才 Stop」的組合無直接測試（見未處理項目）

### Runtime / Observable Level

- [x] Playwright E2E：**17/17 通過**（chromium）
- [x] 捲動迴歸（M-1.1 的風險面）：既有的兩支 `scroll-behavior` spec 皆通過
- [x] Mutation 檢查 ×3：M-1.1（scrollTrigger 還原 → 新測試失敗）、SP-1.3（停用 reset wiring → strengthened case 失敗）、m-2.1（regex 縮回 → 18 中 1 失敗）；三次皆已還原

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `frontend/src/hooks/useDeadAirPlaceholder.ts` | 移除 `graceMs` 參數與不可達分支（M-1.4） |
| `frontend/src/hooks/useStallTimer.ts` | 移除 `threshold` 參數（M-1.4） |
| `frontend/src/lib/reasoning-chips.ts` | Delegate 給官方 guard、修正 SSOT 宣稱（M-1.2）；兩個符號改為 private（O-2.1） |
| `frontend/src/lib/markdown-sources.ts` | regex 放寬至 `^ {0,3}` 並成為單一定義（m-1.1） |
| `frontend/src/lib/timing.ts` | throttle 註解更正（m-1.3） |
| `frontend/src/components/atoms/ActivityPlaceholder.tsx` | doc comment 三 window 化（M-1.3） |
| `frontend/src/components/templates/MessageList.tsx` | scrollTrigger 納入 placeholder 可見性（M-1.1） |
| `frontend/src/components/organisms/AssistantMessage.tsx` | 改用共用 `REF_DEF_LINE_RE`（m-1.1） |
| `frontend/src/components/atoms/README.md` | 事實錯誤更正（m-1.2） |
| `docs/frontend_chat_architecture.md` | 兩張圖的擁有權更正（m-2.2） |
| `frontend/src/lib/__tests__/reasoning-chips.test.ts` | **新增** 35 cases（O-2.2） |
| `frontend/src/components/atoms/__tests__/ActivityPlaceholder.test.tsx` | **新增** 兩種文案 + `aria-live` + `aria-hidden`（SP-1.2） |
| `frontend/src/hooks/__tests__/useDeadAirPlaceholder.test.ts` | 瘦身為 window/timing 專責，16 → 13 cases（O-2.2） |
| `frontend/src/hooks/__tests__/useStallTimer.test.ts` | 刪除 param-only 測試（M-1.4） |
| `frontend/src/components/templates/__tests__/MessageList.test.tsx` | 新增捲動迴歸 + 閘門 case（M-1.1） |
| `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` | stall case 補上 reset wiring 驗證（SP-1.3） |
| `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx` | citation case 參數化 0/3-space（m-2.1） |
| `frontend/src/lib/__tests__/markdown-sources.test.ts` | `hasVisibleReplyText` 邊界（m-1.1） |
| `frontend/src/components/pages/ChatPanel.tsx`、`index.css`、`hooks/README.md`、`pages/README.md`、`tests/e2e/*` | 本次 review 未改動（原 PR 內容） |

## Learning Notes

### 採用的工程策略

- **「純 derivation」這條約束在 review 中實際發揮了否決權。** DEV-106 定下「一切輸入 = `useChat` 的 `(status, messages)`」，本輪它直接否決了 SP-2.1 的建議修法 —— reviewer 想攔 raw stream chunk 來滿足「任何 stream part 歸零」的字面要求，但那正是這次重構刪掉的 side channel 類型。**一條寫下來的架構約束，價值在於它能擋掉「看起來更正確」的提案。**
- **把分類規則交還給 library，而不是鏡像它。** M-1.2 的關鍵不是「重複程式碼」，而是 `reasoning-chips.ts` 的註解自稱 SSOT 卻與 `AssistantMessage` 的 predicate 並存 —— 宣稱與事實脫節比重複本身更危險。delegate 之後，SDK 新增 part 形狀時這裡不會默默漂移。

### 權衡取捨

- **預期：測試搬到正確層級會減少行數。實際：淨增 135 行（O-2.2）。** 偏差來源是原本的間接測試根本沒覆蓋到某些分支（`isToolPart` 對純 `"tool"`、非字串 `type`、`dynamic-tool` renderability）。教訓：**「重構測試以減少體積」和「重構測試以澄清意圖」是兩個不同目標，後者常常讓前者不成立** —— 因為釐清意圖的過程會暴露缺口。
- **grace delay 買到了「不閃現」，代價是與捲動系統解耦（M-1.1）。** 300ms 延遲解決了 chip→tool 微空檔的閃爍，但也讓 placeholder 的 mount 時機不再與 `messages` 變動同步，而既有的捲動跟隨正是綁在 `messages` 上。**引入非同步延遲時，要盤點所有以「同步性」為隱含前提的既有機制。**

### 關鍵收穫

- **「終態 tree 也是這樣寫的」不是理由。** orchestrator 一開始用 byte-identity 當作免死金牌，把多條有效 finding 歸類為「繼承自已驗證的樹」。使用者的糾正是對的：base 只是 base，真正 merge 的是每個 PR，屬於 slice scope 的問題就該在 slice 裡修。**訴諸來源權威會讓 review 失去獨立性**（M-1.1 正是這樣差點被放掉 —— 它其實是本 slice 引入的迴歸）。
- **reviewer 的事實陳述與其嚴重性判定要分開評估。** 本輪 17 條 finding 的事實陳述幾乎全部正確，但多條的判定需要打折或推翻：SP-1.1 誤讀 spec 字串、m-1.2 的「刪 README」直接違反 AC、M-1.3 的 inline 建議誤用了 extension rule。**代價最高的錯誤不是 reviewer 看錯，而是 orchestrator 照單全收。**
- **兩個 reviewer 都可能同時漏掉同一類東西（O-2.1 / O-2.2）。** 未使用的 export 與測試層級錯置，兩軸三輪都沒抓到，是回答使用者「為什麼超行數」時才浮現的。**「這個數字為什麼長這樣」是一個能穿透 review 盲區的問法** —— 它強迫你去拆解組成，而不是評判既有結構。
- **mutation 檢查是唯一能證明測試有效的方法。** 本輪三次 mutation 檢查（M-1.1、SP-1.3、m-2.1）各自證實了新測試真的會抓到迴歸。SP-1.3 尤其關鍵 —— 那個 integration case 原本在 `notifyActivity` 完全斷線的情況下依然會通過，**F6 裁決指定它存在的唯一理由（驗 wiring）正是它沒做到的事**。
