# Code Review Improvement Report

> **Task:** PR #57 — reasoning chip component, derivation helpers and timing hook (dark), part 5/8 of the stacked streaming/reasoning refactor train
> **Date:** 2026-08-18
> **Rounds:** 3 review rounds + 3 fix rounds
> **Reviewer model:** `gpt-5.6-sol` (Codex, `--read-only --effort high`), two independent axes
> **Fixer model:** Claude (`code-fixer` subagent)
> **Extra standards applied at the user's request:** `vercel-react-best-practices`, `vercel-composition-patterns`

## 架構影響摘要

- **`ReasoningChip` 從 molecule 變成 organism。** 它用了 `useRef` + `useLayoutEffect`，而 `docs/frontend_chat_architecture.md` 定義 organism 為「使用 hooks 或 domain-aware」的層。實測整棵 component tree：atoms 0 個用 hooks、其他 molecules 0 個、organisms 4 個——「用 hooks ⇒ organism」是 100% 遵守中的慣例，本元件是唯一例外。趁尚無任何 import 時移動，成本為零。
- **`useReasoningTimers` 的計時 map 從 `useRef` 改為 hook 自有的 `useState`。** 原設計要求 `observe` 在 render 期間呼叫並改寫 ref，違反 React 19「render 期間不得讀寫 `ref.current`」。改寫後 `observe` 由 consumer 的 `useLayoutEffect` 呼叫、`getSeconds` 讀 state，render path 已無 ref 存取。
- **`data-state` 的語意改為反映 part 生命週期，與 `aria-expanded` 刻意脫鉤。** 原本 `showBody = streaming || expanded` 會吃掉使用者對 streaming chip 的收合操作。修正後可見性只跟 `expanded` 走，`data-state` 答「part 還活著嗎」、`aria-expanded` 答「body 看得到嗎」。DOM contract 文件同步改寫。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 3 review + 3 fix |
| 發現 issues 總數 | 15（Quality 11 + Spec 4） |
| Blocking | 1/1 fixed（SP-1.1，與 M-1.3 為同一缺陷） |
| Major | 6/7 fixed（1 條由使用者 dismiss） |
| Minor | 5/5 fixed |
| Suggestion | 0/1 adopted（1 條由使用者 dismiss） |
| Spec findings (SP-) | 3/4 fixed（1 條經 mutation test 證偽後 dismiss） |
| 文件修正 | 5 個檔案 |

## Spec Conformance（Spec 軸）

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Misimplemented | "`isChipExpanded(state, override)` lets an explicit toggle win in both directions."（PR #57 Key decisions） | **Fixed** — 與 Quality 軸 M-1.3 為同一缺陷，兩軸獨立發現 |
| SP-1.2 | Missing | "a per-chip wall-clock that … freezes when the round's next part arrives"（PR #57 Solution） | **Dismissed（使用者裁決）** — 經 mutation test 證偽，見下方 |
| SP-1.3 | Missing | "live and auto-scrolling while streaming"（ADR-0015） | **Fixed** — 補上 pinned-scroll 測試 |
| SP-1.4 | Missing | "`data-state` / `data-round` / `aria-expanded` contract"（PR #57 Key Changes） | **Fixed** — 三個屬性全部由測試釘住 |

Round 2 與 Round 3 的 Spec 軸皆為 **0 findings**。Round 3 特別逐條複驗了 round-2 hook 改寫可能破壞的 spec 語意（freeze 規則、abort 取樣、`chipKey` 跨 turn 隔離、「`done` 但未凍結仍持續計秒」、public surface 未擴張），全部通過。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `docs/adr/0015-reasoning-as-collapsed-transcript-chips.md` | 決策本身:為何 reasoning 以收合 chip 呈現而非 ephemeral indicator | |
| 2 | `docs/frontend_dom_contract.md` | `data-state` enum 與 `aria-expanded` 的脫鉤契約——**下一段 PR 的 Playwright selector 依賴這份** | ⚠️ |
| 3 | `frontend/src/lib/reasoning-chips.ts` | `ChipState` 型別與四個純推導函式(`chipStateOf` / `isChipExpanded` / `chipHeaderLabel` / `chipKey`) | |
| 4 | `frontend/src/hooks/useReasoningTimers.ts` | 計時 hook。**呼叫契約是本 PR 最需要細看的部分**:`observe` 必須從 `useLayoutEffect` 呼叫,`getSeconds` 可在 render 呼叫 | ⚠️ |
| 5 | `frontend/src/components/organisms/ReasoningChip.tsx` | 元件本體:三態 header、pinned-scroll 視窗、a11y 屬性 | |
| 6 | `frontend/src/index.css` | `.reasoning-chip-window` 的 4 行高度 | |
| 7 | `docs/frontend_chat_architecture.md` / `frontend/src/hooks/README.md` / `CONTEXT.md` | 分層表、non-derived state budget、詞彙表 | |
| 8 | `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` | 計時語意 + effect-loop guard + StrictMode | |
| 9 | `frontend/src/components/organisms/__tests__/ReasoningChip.test.tsx` | 三態 header、DOM contract 屬性、pinned-scroll | |
| 10 | `frontend/src/lib/__tests__/reasoning-chips.test.ts` | 純函式推導 | |

## 所有修正問題詳解

### M-1.3 / SP-1.1（Blocking／Major，兩軸獨立發現）
- **問題：** `showBody = streaming || expanded` 讓 streaming 中的 chip 忽略明確的 `expanded={false}`。`isChipExpanded("streaming", false)` 正確回傳 `false` 且有測試背書，component 卻把它吃掉，`aria-expanded` 還謊報 `true`。使用者點 header 收合會毫無反應。
- **修法：** `showBody = expanded`。使用者裁決 `data-state` 改為反映 part 生命週期（streaming 中被收合仍是 `streaming`），與 `aria-expanded` 刻意脫鉤；DOM contract 三個 enum 全部改寫成生命週期語意並明文記錄脫鉤。
- **影響：** 修掉一個在真人操作下立刻可見的失效（envelope §7 rubric 第 3 條）；同時消除 helper 與 component 對同一件事講兩套話的矛盾。
- **驗證：** 新增測試 `an explicit collapse wins over a still-streaming part` — 斷言無 body node、`data-state="streaming"`、`aria-expanded="false"`。

### M-1.1 → M-2.1（Major，跨兩輪，第一次修法不完整）
- **問題：** hook 的 JSDoc 要求 `observe` 在 render 期間呼叫，而它會改寫 `timingsRef.current`。React 19 明文禁止 render 期間讀寫 ref（僅允許一次性 lazy init）。**Round 1 的修法只搬走了「寫」**；Round 2 reviewer 指出 `getSeconds` 仍在 render 期間**讀** ref，而它的回傳值就是畫面上的秒數，非在 render 呼叫不可。
- **修法：** 使用者裁決採 option A——計時 map 移入 hook 自有的 `useState`。`observe` 在函式本體取樣 `now` 後呼叫 `setTimings(prev => …)`，updater 對 `now` 為純函式；lazily clone（`next ??= new Map(prev)`）並以 `return next ?? prev` 讓 React 在無變更時 bail out；凍結產生新的 `ChipTiming` 物件而非原地改寫。`getSeconds` 改讀 state。
- **影響：** render path 已無 ref 存取，符合 React 純度規則。連帶讓三條 Vercel 規則從「不適用／違反」翻成「遵守」：`rerender-use-ref-transient-values`（⚠️→✅）、`rerender-functional-setstate`、`rerender-lazy-state-init`。
- **驗證：** 6 個既有計時測試**未經修改全數通過**；新增 effect-loop guard 測試與 StrictMode 測試。**Orchestrator mutation test：** 把 `return next ?? prev` 改成 `return next ?? new Map(prev)`（拿掉 bail-out），guard 測試立即失敗（`expected [Function] to be [Function]`），還原後 8/8 通過——證明該測試非空轉。
- **殘留且刻意保留：** 未凍結的 chip 在 render 期間仍呼叫 `Date.now()`。完全純化需要定時器持續 re-render，而 header 本來就不跳秒。此點已明文寫入 hook JSDoc，非默默忽略。

### M-1.2（Major）
- **問題：** `ReasoningChip` 使用 `useRef` + `useLayoutEffect` 卻登記為 molecule；架構文件定義 organism 為「使用 hooks 或 domain-aware」。
- **修法：** 使用者裁決移動檔案而非修改分層規則。`git mv` 元件與測試至 `organisms/`（rename 歷史保留，diff 顯示 `similarity index 73%`），架構文件三處同步更新。
- **影響：** 消除全 repo 唯一的分層例外。實測依據：atoms 0 個用 hooks、其他 molecules 0 個、organisms 4 個。
- **驗證：** grep 確認零個 import 站點（本 PR 刻意暗置），`tsc -b` 與全套測試通過。

### M-1.4（Major，部分採納）
- **問題：** `stalled` prop 的 JSDoc 寫 `degraded copy consumer #2`、測試名稱帶 `(C4)`——皆為只在產出當次工作階段內有意義的編號。
- **修法：** JSDoc 改為描述行為（streaming header 在全域 stall 碼錶觸發時換成 `Still working…`）；測試名稱刪除 `(C4)`。
- **影響：** 未來讀者不需回溯任何工作階段紀錄即可理解。
- **驗證：** 測試名稱變更後全套通過。
- **子項未採納：** reviewer 一併指控 ADR-0015 的 `v1 chips`；使用者裁決「v1」屬一般版本敘述而非流程編號，維持原樣。

### m-1.1（Minor）
- **問題：** chip header `<button>` 無 `aria-label`。`docs/frontend_dom_contract.md` Principles 1 明訂互動元素「always carry an `aria-label`」，「Adding new components」第 1 條再次要求。
- **修法：** `aria-label={`${headerLabel} — ${showBody ? "collapse" : "expand"} reasoning`}`，與可見 span 共用同一個 `headerLabel`，因此隨 `Thinking…` → `Still working…` → `Thought for 3s` 同步更新，不會過期。
- **影響：** 補上 repo 明文要求；accessible name 同時傳達狀態與可執行動作。
- **驗證：** 新增測試以 `getByRole("button", { name })` 斷言三種狀態下的 accessible name。Round 2 與 3 的 reviewer 均複核 `aria-label` + `aria-live` + `aria-expanded` 三者並存無衝突：串流 body deltas 位於 live region 之外，符合 `aria-live="polite"` 語意。

### m-1.2（Minor）
- **問題：** `frontend/src/hooks/README.md` 的「Non-derived state budget」仍寫「Two non-derived stores are allowed so far」並只列兩條，本 PR 卻新增了第三個（per-chip 計時），且 ADR-0015 稱其為 deliberate non-derived state——文件自相矛盾。
- **修法：** 計數改為 Three 並補上 `useReasoningTimers` 條目與理由（wire 上不帶 timestamp）。ADR-0015 的措辭從「the one deliberate piece」收斂為 reasoning chip 範圍內的敘述。Round 2 改寫後再次更新為 `timings` state map。
- **影響：** 這份 budget 是刻意設計來擋住非衍生 state 蔓延的閘門；它一旦失準就失去作用。
- **驗證：** 人工核對三條目與實作一致。

### m-1.3（Minor，使用者推翻 orchestrator 建議）
- **問題：** ADR-0015 首行帶 `(DEV-105)`。orchestrator 原建議不修，理由是它已附描述性名稱、符合既有的 issue-ID 規則。
- **修法：** **使用者裁決 ADR 內文一律描述性、不得出現 issue 編號**，即使帶描述也要拿掉。刪除 `(DEV-105)` 並掃過全檔確認無其他 ticket 參照。
- **影響：** ADR 壽命長於 issue tracker；「the multi-provider refactor spec」本身已足以指認。此規則已寫入長期 memory。
- **驗證：** 全檔 grep `DEV-` / `HQ-` / `#N` 無殘留。

### SP-1.3（Major）
- **問題：** pinned-scroll 的 `useLayoutEffect`（`el.scrollTop = el.scrollHeight`）零覆蓋——整段刪掉測試仍全綠。這是元件內唯一一段命令式 DOM 邏輯。
- **修法：** effect 加上 `if (!streaming || !showBody) return;` 並把 `showBody` 納入 deps（配合 M-1.3 的可見性改動：collapsed 時無 body node）。新增兩個測試，於 `HTMLElement.prototype` 上 stub `scrollHeight`／`scrollTop`（jsdom 無 layout）並在 `afterEach` 還原。
- **影響：** envelope §5 對非 §4 區的標準是「happy path + 一個 legible-failure case」，此處原本是 0。
- **驗證：** fixer 自行做 mutation check（停用 effect → 兩個測試皆失敗）。Round 3 reviewer 確認 stub 以 `Reflect.deleteProperty` 還原，會讓原本繼承自 `Element` 的 descriptor 重新露出，不會外洩至其他測試。

### SP-1.4（Major）
- **問題：** DOM contract 宣告 `data-state`／`data-round`／`aria-expanded` 為穩定契約，測試卻只涵蓋部分 `data-state`，`data-round` 與 `aria-expanded` 完全未斷言，`data-state="collapsed"` 也從未被釘住。
- **修法：** 新增 `DOM contract attributes` describe block，涵蓋 streaming-expanded／streaming-collapsed／done-collapsed／done-expanded 四種組合的 `data-state` + `aria-expanded`，外加 `data-round` 序數斷言（1 → 3）。
- **影響：** 下一段 PR 的 Playwright specs 會直接依賴這些 selector；契約漂移現在會在 unit 層就被擋下。
- **驗證：** 4 個 `data-state`／`aria-expanded` 案例 + 1 個 `data-round` 案例通過。

### m-2.1（Minor）
- **問題：** 本 PR 把 `export type ChipState` 插進註解 `/** Minimal structural view of a chat message… */` 與它所描述的 `ChatMessageLike` 之間，導致該註解變成在描述 `ChipState`。
- **修法：** 註解移回 `ChatMessageLike` 上方，`ChipState` 另給一行 `/** Lifecycle a reasoning chip's header renders from. */`。
- **影響：** 編輯器產生的型別說明不再誤導。
- **驗證：** 人工核對；`tsc -b` 通過。

### m-3.1（Minor，本次修法自身造成的 staleness）
- **問題：** `chipKey` 的 JSDoc 仍寫 `Stable key for timer refs / override map`，但 Round 2 已將 ref 換成 state，與實作及 `hooks/README.md` 皆矛盾。
- **修法：** 改為 implementation-neutral 的 `Stable key for the timer and override maps`；part-id 重用的說明（承重的那一半）原樣保留。
- **影響：** 這是修正動作自身留下的過時描述，正是需要第三輪 review 才會浮現的類型。
- **驗證：** fixer 於 `frontend/src/` 全域 grep `ref` / `useRef` / `timingsRef` / `timer ref`，確認全樹僅此一處殘留。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `docs/frontend_dom_contract.md` | `data-state` 三個 enum 改寫為生命週期語意；新增 `data-state` 與 `aria-expanded` 刻意脫鉤的說明；companion testid 段補上 `aria-label` |
| `docs/frontend_chat_architecture.md` | `ReasoningChip` 由 molecules 移至 organisms（mermaid subgraph、class 指派、分層表三處） |
| `docs/adr/0015-...md` | 刪除 `(DEV-105)`；non-derived state 的措辭收斂至 reasoning chip 範圍 |
| `frontend/src/hooks/README.md` | Non-derived state budget 由 Two 改為 Three 並補 `useReasoningTimers` 條目；Round 2 後再更新為 `timings` state map |
| `frontend/src/lib/reasoning-chips.ts` / `ReasoningChip.tsx` | JSDoc:註解歸位、流程編號改為描述性文字、`chipKey` 措辭去實作化 |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Major (Quality) | M-1.4 子項:ADR-0015 的 `v1 chips` | 使用者裁決「v1」為一般版本敘述而非流程編號 | 無 |
| Suggestion | S-1.1:chevron 動畫改包 wrapper（`rendering-animate-svg-wrapper`） | 14px 圖示、每次點擊轉一次;envelope §7 rubric 第 4 條 optional polish | 無 |
| Major (Spec) | SP-1.2:計時測試未鎖 freeze 邊界 | **經 orchestrator mutation test 證偽**——把實作改成在 `part.state === "done"` 時凍結，6 個測試中 2 個失敗。測試確實鎖得住 | 無 |
| 觀察（非 finding） | `.reasoning-chip-window` `max-height: calc(4 * 1.25rem)` = 5rem，但同元素帶 `pb-2` 且 Tailwind preflight 設 `box-sizing: border-box`，實際內容區為 4.5rem ≈ 3.6 行 | 註解寫「~4 lines」有波浪號不算錯;第 4 行露一半反而是可捲動的視覺提示 | 若日後要求精確 4 行，改 `max-height: calc(4 * 1.25rem + 0.5rem)` |

## Final Verification Results

全部由 orchestrator 獨立執行，非採信 subagent 回報。

### Code Level

- [x] Unit Tests: `pnpm test` → **25 files / 245 tests passed**（review 前為 235，本次淨增 10）
- [x] Lint: `pnpm lint` → **0 errors**（1 個 pre-existing warning 位於產生檔 `public/mockServiceWorker.js`，不在 diff 內）
- [x] Format: `pnpm format:check` → **All matched files use Prettier code style**
- [x] Type Check: `pnpm build`（`tsc -b` + vite）→ **通過**，僅既有的 >500 kB chunk 建議

### Behavior Level

- [x] Mutation test — 計時 freeze 邊界：實作改為在 `state === "done"` 凍結 → 6 個測試中 2 個失敗（證偽 SP-1.2）
- [x] Mutation test — effect-loop guard：移除 `return next ?? prev` 的 bail-out → guard 測試失敗；還原後 8/8 通過
- [x] Mutation test — pinned-scroll（fixer 執行）：停用 `useLayoutEffect` → 兩個 pinning 測試皆失敗

### Runtime / Observable Level

- [x] E2E: `pnpm test:e2e` → **34 passed (31.2s)**，涵蓋 critical／security／smoke。本 PR 不新增 E2E——跑這套是為了確認新增的 CSS 與元件在未被 import 的情況下對既有行為完全惰性
- [ ] 產品流程驗證: **不適用且刻意如此**。本 PR 為暗置交付，無任何頁面 import `ReasoningChip`／`useReasoningTimers`。chip 在 transcript 中的行為驗證屬於下一段 PR（wiring + a11y announcer + profile 開啟 reasoning）
- [ ] BDD: **未執行**。`artifacts/current/` 無 `bdd-scenarios.md` / `verification-plan.md`——本 PR 由既有 stacked train 分支進入，非 BDD 流程產出

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `frontend/src/components/organisms/ReasoningChip.tsx` | 由 `molecules/` 移入(M-1.2);`showBody` 改吃 `expanded`(M-1.3);pinned-scroll effect 加 guard 與 `showBody` dep(SP-1.3);新增 `aria-label`(m-1.1);`stalled` JSDoc 去流程編號(M-1.4) |
| `frontend/src/components/organisms/__tests__/ReasoningChip.test.tsx` | 由 `molecules/__tests__/` 移入;測試名去 `(C4)`;新增 accessible-name、DOM contract 屬性(4 案例 + `data-round`)、pinned-scroll(2 案例) |
| `frontend/src/hooks/useReasoningTimers.ts` | `useRef` → `useState`,updater 純化、lazy clone、bail-out、凍結不原地改寫(M-2.1);JSDoc 契約兩度改寫並明載殘留不純 |
| `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` | 6 個既有案例未改動;新增 effect-loop guard 與 StrictMode 兩案例 |
| `frontend/src/lib/reasoning-chips.ts` | JSDoc 註解歸位至 `ChatMessageLike`(m-2.1);`chipKey` 措辭去實作化(m-3.1) |
| `frontend/src/lib/__tests__/reasoning-chips.test.ts` | 未經 review 修改（本 PR 原有的純函式測試） |
| `frontend/src/hooks/README.md` | Non-derived state budget Two → Three(m-1.2);Round 2 後更新為 state map |
| `frontend/src/index.css` | 未經 review 修改 |
| `docs/frontend_dom_contract.md` | `data-state` enum 改寫為生命週期語意 + 脫鉤說明(M-1.3);`aria-label` 補入(m-1.1) |
| `docs/frontend_chat_architecture.md` | `ReasoningChip` 移至 organisms 層(M-1.2) |
| `docs/adr/0015-...md` | 刪 `(DEV-105)`(m-1.3);non-derived state 措辭收斂(m-1.2) |
| `CONTEXT.md` | 未經 review 修改 |

## Learning Notes

### 採用的工程策略

- **「衍生而非記錄」在 chip 狀態上完整存活。** `chipStateOf` 從 part 形狀推導 abort（「chat 離開 active pair 後 part 仍是 streaming」），沒有引入任何 per-message 記帳。三輪 review 沒有任何一條 finding 指向這個決策——反倒是**唯一被引入的非衍生 state（計時 map）連續兩輪成為 Major finding 的來源**（M-1.1 → M-2.1）。這是對「非衍生 state 是有成本的」最直接的實證。
- **暗置交付讓分層與契約的修正變成零成本。** M-1.2 移動檔案時 grep 到零個 import 站點；如果等下一段 PR 接好 `AssistantMessage`／`ChatPanel` 才移，就要動 import。「趁沒有消費者時修正結構」在本輪出現兩次（M-1.2 的移動、M-1.1 的契約改寫），兩次都因為暗置而幾乎免費。

### 權衡取捨

- **expected vs actual：我在 Round 1 gate 判斷「只改呼叫契約就夠」，這個判斷是錯的（M-1.1 → M-2.1）。** 預期是「把寫入搬到 layout effect 就合規」；實際 React 的規則是「不得讀**或**寫」，而 `getSeconds` 的回傳值就是畫面上的秒數，非在 render 期間呼叫不可。半套修法比不修更糟——JSDoc 宣稱合規，讀取路徑仍違規。教訓是引用規則時要引全句，不能只引對自己方案有利的那一半。
- **envelope 校準與「修不修」是兩個獨立問題。** M-1.1／M-2.1 按 envelope §7 rubric 確實只是第 4 條 optional polish（無使用者可見失效）。但真正促使我建議修的不是嚴重性，而是**那段 JSDoc 是寫給下一段 PR 作者的指令**——會擴散的錯誤指示比靜態的技術債貴。嚴重性決定「擋不擋」，擴散性決定「現在修還是以後修」。

### 關鍵收穫

- **對「測試沒鎖住 X」這類指控，mutation test 是最短的裁決路徑（SP-1.2）。** reviewer 主張測試放得過錯誤實作；我把實作改成它描述的錯法，2/6 測試失敗，指控當場證偽。這比讀測試碼推論快也可靠。同一招在本輪用了三次（證偽 SP-1.2、驗證 loop guard、fixer 自驗 pinned-scroll），三次都給出明確答案。
- **修正動作本身會產生新的 staleness，這正是多輪 review 的價值所在（m-3.1）。** Round 2 把 ref 換成 state，`hooks/README.md` 記得改，`chipKey` 的 JSDoc 沒人想到。單輪 review 抓不到這種缺陷——它在第一輪還不存在。
- **兩軸獨立跑會產生訊號強度資訊（M-1.3 / SP-1.1）。** 兩個互不見對方 context 的 reviewer 同時指向同一行 code，這條 finding 的可信度高於任一軸的獨立判斷。若把兩軸合併成一份報告，這個訊號就消失了。
- **「repo 明文規則」與「repo 實際慣例」要分開查證，兩者一致時反對意見才站不住（M-1.2）。** 我原本想改文件遷就單一個案；去數了 atoms/molecules/organisms 的 hook 使用分布（0/0/4）之後才確定「用 hooks ⇒ organism」不只是文字而是零反例的慣例，於是改推薦移動檔案。用一個 grep 換掉一個錯誤建議。
