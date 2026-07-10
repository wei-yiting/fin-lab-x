# Failures Museum 展示頁 — Design（WIP）

> **狀態**：design-brainstorming 進行中（§1 已核准、§2 已提出待核准、§3–§4 未提出）。
> **暫停原因**：human 決定等 DEV-77、HQ-4 完成後再繼續（2026-07-10）。
> **Linear**: DEV-81｜**Worktree**: `fin-lab-x-wt/failure-museum-page`（branch `feat/failure-museum-page`）

## 目標

將 DEV-81 策展的 AI engineering 失敗案例（3 展廳 18 件展品）做成 FinLabX 前端的正式頁面，
定位為對外 portfolio 敘事頁。策展內容藍本：Artifact
<https://claude.ai/code/artifact/878db142-9706-48de-9b46-c4c4c74213ca> 與
`.artifacts/current/failure_museum_catalog.md`（完整考古目錄）。

## 已定案決策（clarifying questions 全部完成）

| # | 決策 | 選擇 | 理由 / 被否決的替代 |
|---|---|---|---|
| 1 | 受眾定位 | 對外展示 / Portfolio | 靜態策展內容、不接 backend；否決「內部儀表板」（量化牆多數缺口未補）與「產品功能」 |
| 2 | 內容語言 | 英文 | 對外受眾 + repo pure-English 文件政策；否決繁中沿用與雙語（無 i18n 基礎） |
| 3 | Routing | react-router（library mode），route = **`/failures-museum`** | Portfolio 需要可分享 URL；否決 state 切換（無獨立 URL）與 Vite MPA（雙 entry 維護高） |
| 4 | 視覺方向 | **Mockup A 淺色博物館銘牌風**，不與 chat 深色系對齊 | human 看過四個 mockup（A 淺色博物館 / B 淺色 shadcn / A2 深色對齊 / B2 深色原生）後選 A；museum 用自己的 theme scope |
| 5 | 內容範圍 | 三展廳 18 件展品 + Curator's Notes（橫向 patterns）+ Quantification Wall（eval 覆蓋現況） | 「待考證」區為內部工作狀態，不上對外頁 |
| 6 | 內容格式 | Typed TS data module（`exhibits.ts`） | Type-safe、零新依賴；否決 MDX（需 loader、無 type 保護）與 JSON（無註解/type） |
| 7 | 程式碼組織 | **方案 1：feature folder** `components/pages/failures-museum/`，lazy-loaded route | 元件只有 museum 用，內聚優於打散進 atomic 分類（方案 2 被否決）；sub-routes per hall 過度設計（方案 3 被否決） |
| 8 | Serif 字型 | Georgia 系統字型 stack | 零依賴，macOS/Windows 皆內建；否決 fontsource 新依賴 |
| 9 | 執行分工 | 設計/分析 = Fable main loop；實作 = Opus subagent | human 指定（見 memory `project-model-division`） |

## §1 元件責任與資料流（✅ 已核准）

Routing 層（唯一動到既有程式碼的地方）：

- `App.tsx`：`<Routes>` — `/` → ChatPanel（不變）、`/failures-museum` → `React.lazy(FailuresMuseumPage)`
- 不加全域導覽列；museum 頁 header 放 "← Back to FinLab-X" 連結，chat 視覺零變動

Museum 頁內部（單向資料流、全 stateless render）：

```
exhibits.ts (data)
    ↓
FailuresMuseumPage ── hero、hall 錨點導覽、組裝 sections
    ├── HallSection ×3 ─── 展廳標題 + 該廳展品
    │       └── ExhibitCard ×N ── 銘牌卡（編號、狀態章、欄位、provenance）
    ├── CuratorNotes ───── 橫向 patterns（羅馬數字編號 + 展品引用錨點）
    └── QuantWall ──────── 量化現況表（Measured / Instrumented / Not measured）
```

- 每張 ExhibitCard 有 `id` anchor（`#pe-01`）— URL 直連單一展品
- 無 client state（不做 filter/tab；18 件 + 錨點導覽足夠，YAGNI）

檔案結構（方案 1）：

```
src/components/pages/failures-museum/
├── FailuresMuseumPage.tsx
├── exhibits.ts        ← typed data module
├── museum.css         ← museum 專屬淺色 theme scope
├── ExhibitCard.tsx
├── HallSection.tsx
├── QuantWall.tsx
└── CuratorNotes.tsx
```

## §2 Data schema（🟡 已提出，待 human 核准）

四個 typed 結構，同一 data module：`Hall`、`Exhibit`、`CuratorNote`、`CoverageRow`。

```ts
export type HallId = "prompt" | "context" | "harness";
export type ExhibitStatus = "fixed" | "in-progress" | "open";

export interface Hall {
  id: HallId;
  numeral: string;        // "HALL I"
  title: string;
  tagline: string;
}

export interface Exhibit {
  id: string;             // "PE-01" — 也是 URL anchor（#pe-01）
  hall: HallId;
  title: string;
  status: ExhibitStatus;
  statusNote?: string;    // 補充章，如 "3 residual bugs"
  scene: string;
  rootCause?: string;     // 未有正式分析者（HE-01）可缺
  fix?: string;           // open 展品沒有
  quantified?: string;
  lesson?: string;
  provenance: string;     // "PR #3 · 65ba25b · language_policy_scorer.py"
}

export interface CuratorNote {
  title: string;
  body: string;
  exhibitIds: string[];   // render 成展品錨點連結
}

export interface CoverageRow {
  exhibitId: string;
  label: string;
  level: "measured" | "instrumented" | "none";
  exists: string;
  missing: string;
}
```

Schema 決策（§2 內提出）：

1. `quantified` 用自由文字非結構化數字 — 各展品量化形式差異大，現在結構化是過度設計；未來接 eval 分數時加欄位，tsc 強迫補齊
2. 展品 id 引用用 `string` 非 literal union — 用測試驗證 `exhibitIds`/`exhibitId` 存在於 exhibits 陣列，錯字 CI 抓
3. 內容全英文寫在 data module，元件零文案

## §3 Theme 處理（⬜ 未提出）

要點（草案）：app 是 `html.dark` 寫死深色；museum 淺色 tokens 全部 scope 在頁面 wrapper class
底下（`.museum` 或 route 層 wrapper），不動全域 theme、不 toggle `.dark`。色票沿用
mockup-a：gallery stone `#f2f2ee`、archival blue `#35597e`、狀態色 oxblood/amber/moss。

## §4 測試策略（⬜ 未提出）

要點（草案）：data 完整性測試（id 引用存在、必填欄位）；RTL render 測試（各 section、anchor）；
既有 chat 路由不受影響的 regression（`/` 仍 render ChatPanel）；Playwright 視覺 smoke（可選）。

## 視覺參考

- `mockups/mockup-a-museum.html` — 已選定的視覺方向（淺色博物館銘牌）
- `mockups/mockup-notes-wall.html` — Curator's Notes + Quantification Wall 區塊示意
- `mockups/failure-museum.html` — Artifact 策展版原稿（深/淺雙主題、完整 18 件展品文案的中文版）

## Out of scope

- 接真實 eval 分數（量化牆先靜態；schema 預留演化空間）
- chat ↔ museum 全域導覽與視覺對齊
- i18n / 雙語
- 「待考證」區（內部工作狀態，留在 DEV-81）

## Learning Notes

### 探索的領域概念

- **Typed TS data module 作為內容儲存**：用 TypeScript 檔案當「資料庫」— 定義 interface 再寫符合形狀的
  資料陣列。相對 Markdown/MDX 的取捨：結構化短欄位內容適合 typed module（編譯期防錯、schema 演化時
  tsc 強迫補齊、零 loader 依賴）；自由排版長文才需要 Markdown。
- **Scoped theme 與全域 dark mode 共存**：app 級 `html.dark` 與頁面級淺色 theme 可以並存 —
  把頁面 tokens scope 在 wrapper class 下，不 toggle 全域 class。

### 評估過的方案與取捨

- 視覺方向四選一：淺色博物館銘牌（選定）vs 淺色 shadcn vs 深色對齊 app tokens vs 深色原生 —
  human 以實際 rendered mockup 比較後決定，而非文字描述。
- Feature folder vs atomic design 分類：只被單一頁面使用的元件，內聚在 feature folder
  勝過遵循全域分類慣例 — 分類的復用好處為零時，就近維護價值更高。
- MDX vs typed TS module：內容是「固定欄位的短文」時，type 安全 > 編輯體驗。

### 關鍵收穫與資源

- Portfolio 頁的核心需求是「可分享的 URL」— routing 決策由此推導（react-router 而非 state 切換）。
- 對外展示頁誠實列出量測缺口（Quantification Wall 的 "Not measured"）本身就是 eval 成熟度的展現。
