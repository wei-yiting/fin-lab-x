# BDD Scenarios — S2 Frontend Scaffold

## Meta

- Design Reference: `.artifacts/current/design_S2_frontend_scaffold.md`, `.artifacts/current/design_master.md` (S2 section)
- Generated: 2026-03-31
- Discovery Method: Three Amigos (Agent Teams — PO, Dev, QA)

### Discovery Summary

| Metric | Count |
| --- | --- |
| PO Rules extracted | 10 |
| Dev challenges (R1 + R2) | 13 |
| QA challenges (R1 + R2) | 18 |
| Included after PO judgment | 10 (8 original + 2 after contests) |
| Demoted to unit test / impl verification | 8 |
| Needs user input (resolved) | 4 |
| Rejected | 8 |

### Resolved User Decisions

| Question | Resolution |
| --- | --- |
| shadcn/ui style `radix-nova` | Confirmed valid (Context7 verified) |
| AI SDK version pinning | Pin to `^5.0.0` (`ai` + `@ai-sdk/react`) |
| Font loading in S2 | Not included; shadcn init theme variables are standard output |
| Package manager | `pnpm` (all commands use pnpm equivalents) |

### Design Doc Update Action Items

- `vite.config.ts` spec should add `server: { port: 5173, strictPort: true }` (from Dev-C1 + QA-C11)
- `playwright.config.ts` spec should use `command: 'pnpm run dev'` (not `npm run dev`)
- All AC examples should reference `pnpm` commands

---

## Feature: Dev Environment & Styling Pipeline

### Context

S2 建立前端 build toolchain (Vite + React + TypeScript) 和 styling pipeline (Tailwind CSS v4 + shadcn/ui)。S3 開發者依賴這些基礎設施來建構 Streaming Chat UI。

### Rule: Dev server 綁定嚴格 port 5173，fail-fast 避免 Playwright 測試對錯服務

#### S-env-01: Dev server 啟動並提供 App shell

> 驗證 `pnpm run dev` 在 port 5173 啟動並正確 serve App shell

- **Given** S2 scaffold 已安裝（`pnpm install` 完成）
- **When** S3 開發者在 `frontend/` 執行 `pnpm run dev`
- **Then** Vite dev server 在 `http://localhost:5173` 啟動，頁面顯示 "FinLab-X" heading 和 "AI-powered financial analysis assistant." 副標題，Tailwind styling 正確套用

Category: Illustrative
Origin: PO

#### S-env-02: Port 5173 被佔用時 dev server 拒絕啟動

> 驗證 fail-fast 行為，防止 Playwright 測試靜默連接到錯誤的 server

- **Given** 另一個 process 佔用 port 5173
- **When** S3 開發者執行 `pnpm run dev`
- **Then** Vite 以 port 衝突錯誤退出，不會靜默 fallback 到其他 port

Category: Illustrative
Origin: Dev

### Rule: Tailwind CSS v4 utility classes 和 shadcn/ui CSS variables 正確渲染

#### S-env-03: Tailwind utility classes 產生可見 styling

> 驗證 Tailwind v4 + `@tailwindcss/vite` pipeline 端對端運作

- **Given** dev server 正在運行
- **When** S3 開發者開啟 `http://localhost:5173`
- **Then** App shell 顯示可見的 Tailwind styling：heading 有 `text-3xl font-bold`，頁面容器有 `bg-background`（不是無樣式的 raw HTML）

Category: Illustrative
Origin: PO

#### S-env-04: shadcn/ui CSS custom properties 解析為 theme 色彩

> 驗證 shadcn 元件所需的 CSS variables 已定義且正常運作

- **Given** dev server 運行中，shadcn/ui 已初始化
- **When** S3 開發者新增 shadcn Button 元件 `<Button>Click</Button>` 到頁面
- **Then** Button 以可見的 `bg-primary text-primary-foreground` 色彩渲染——不是 transparent 或不可見

Category: Illustrative
Origin: Dev

#### S-env-05: Dark mode variant 回應 class-based 切換

> 驗證 Tailwind v4 已設定 class-based dark mode（shadcn/ui 需要）

- **Given** dev server 運行中，shadcn/ui theme 已設定
- **When** S3 開發者在 `<html>` 元素加入 `dark` class
- **Then** `dark:` utility variants 生效（如 `dark:bg-background` 切換到深色 theme 值），不受 OS preference 影響

Category: Illustrative
Origin: Dev + QA (merged)

### Rule: shadcn init 產生 Tailwind v4 相容的 CSS

#### S-env-06: 初始化後 styling pipeline 使用 Tailwind v4 語法

> 驗證 shadcn init 輸出 v4 相容 CSS，非 v3 directives

- **Given** shadcn/ui 透過 `pnpm dlx shadcn@latest init` 完成初始化
- **When** S3 開發者檢查 `src/index.css`
- **Then** 檔案使用 `@import "tailwindcss"` (v4 語法)，不是 `@tailwind base; @tailwind components; @tailwind utilities;` (v3 語法)；shadcn theme variables 在正確的 CSS layer 中定義

Category: Illustrative
Origin: Dev

---

## Feature: Component Primitive Pipeline

### Context

shadcn/ui CLI 將元件檔案產出到 `src/components/primitives/`（自訂路徑），`src/components/ui/` 保留給 S3 的自訂組合元件。

### Rule: shadcn CLI 新增元件到自訂的 `primitives/` 目錄

#### S-comp-01: CLI 新增的元件落在 primitives 目錄

> 驗證 `components.json` 中自訂的 `ui` alias 正確運作

- **Given** shadcn/ui 已成功初始化（init 無錯誤完成，`pnpm-lock.yaml` 存在）
- **When** S3 開發者執行 `pnpm dlx shadcn@latest add button`
- **Then** `src/components/primitives/button.tsx` 被建立，`src/components/ui/button.tsx` 不存在

Category: Illustrative
Origin: PO

#### S-comp-02: CLI 新增的元件 import 可解析且 type-check 通過

> 驗證生成的元件使用正確的 import paths

- **Given** `button.tsx` 已透過 shadcn CLI 新增到 `src/components/primitives/`
- **When** S3 開發者在新檔案中 import `{ Button } from '@/components/primitives/button'`
- **Then** `pnpm exec tsc --noEmit` 通過，Button 在 dev server 中正確渲染

Category: Illustrative
Origin: PO + Dev

---

## Feature: Test Infrastructure

### Context

雙層測試基礎設施：Vitest + RTL 用於 unit/component 測試，Playwright 用於 E2E。兩條 pipeline 都必須 out-of-the-box 可用。

### Rule: Unit test pipeline 在 runtime 和 type-check 層級都正常運作

#### S-test-01: Vitest baseline test 透過 pnpm script 通過

> 驗證 Vitest + RTL + jsdom pipeline 端對端運作

- **Given** `package.json` 定義了 `"test": "vitest run"` script
- **When** S3 開發者執行 `pnpm run test`
- **Then** Vitest 發現 `src/App.test.tsx`，在 jsdom 環境執行，assert "FinLab-X" heading 的測試通過，exit code 0

Category: Illustrative
Origin: PO

#### S-test-02: jest-dom matchers 無需額外設定即可使用

> 驗證 test-setup.ts 正確 import jest-dom extensions

- **Given** `src/test-setup.ts` imports `@testing-library/jest-dom/vitest`
- **When** S3 開發者寫測試使用 `expect(element).toBeInTheDocument()`
- **Then** matcher 在 runtime 正常運作（測試因 assertion 成功或失敗，不是因為 "toBeInTheDocument is not a function"）

Category: Illustrative
Origin: Dev

#### S-test-03: Vitest global functions 在 test 檔案中 type-check 通過

> 驗證 `describe`、`it`、`expect` 在不顯式 import 的情況下有正確的 TypeScript 型別

- **Given** `vitest.config.ts` 有 `globals: true` 且 TypeScript 設定了 Vitest type augmentation
- **When** S3 開發者寫測試使用 `describe()` 和 `it()` 但不 import 它們
- **Then** `pnpm run test`（runtime）和 `pnpm exec tsc --noEmit`（type-check）都通過——無 "Cannot find name 'describe'" 錯誤

Category: Illustrative
Origin: QA

### Rule: E2E test pipeline 搭配自動 dev server lifecycle 運作

#### S-test-04: Playwright baseline test 搭配自動啟動的 dev server 通過

> 驗證 Playwright + Vite webServer 整合正常運作

- **Given** 無 dev server 運行中，Playwright browsers 已安裝
- **When** S3 開發者執行 `pnpm run test:e2e`
- **Then** Playwright 透過 `webServer` config 在 :5173 啟動 Vite dev server，執行驗證 "FinLab-X" heading 的 baseline test，通過且 exit code 0

Category: Illustrative
Origin: PO

#### S-test-05: Playwright 在 fresh install 後能執行測試

> 驗證 browser binaries 可用，無需手動介入

- **Given** S3 開發者在 fresh clone 上已執行 `pnpm install`
- **When** 執行 `pnpm run test:e2e`
- **Then** Playwright 不會因 "Executable doesn't exist" 而 crash——要嘛 browsers 已預裝，要嘛有清楚的錯誤訊息提供 one-step 修復指示

Category: Illustrative
Origin: Dev

---

## Feature: SDK & Scaffold Contract

### Context

S2 預裝 AI SDK v5 並設定 tooling（path aliases、ESLint、directory structure），讓 S3 能立即開始 streaming chat UI 開發。

### Rule: Path alias `@/` 在所有 toolchain 中解析

#### S-sdk-01: Path alias 在 TypeScript、Vite、和 Vitest 中解析

> 驗證 `@/` 在 source、dev server、和 test runner 中都能運作

- **Given** `vite.config.ts`、`vitest.config.ts`、和 `tsconfig.app.json` 都定義了 `@/` → `src/`
- **When** S3 開發者在 source 檔寫 `import { cn } from '@/lib/utils'`，在 test 檔寫 `import App from '@/App'`
- **Then** `pnpm run dev` 正常 serve，`pnpm run test` 通過，`pnpm exec tsc --noEmit` 無錯誤

Category: Illustrative
Origin: PO

### Rule: AI SDK v5 packages 已安裝且型別相容

#### S-sdk-02: AI SDK v5 imports type-check 成功

> 驗證 S2→S3 contract 中 AI SDK 的可用性

- **Given** `ai@^5.0.0` 和 `@ai-sdk/react@^5.0.0` 已安裝
- **When** S3 開發者寫 `import { useChat } from '@ai-sdk/react'` 和 `import { DefaultChatTransport } from 'ai'`
- **Then** `pnpm exec tsc --noEmit` 通過，這些 imports 無型別錯誤

Category: Illustrative
Origin: PO

### Rule: ESLint 捕捉 React-specific 錯誤

#### S-sdk-03: ESLint 在 scaffold codebase 上報告零錯誤

> 驗證 baseline ESLint 設定是乾淨的

- **Given** `package.json` 定義了 `"lint": "eslint ."` script
- **When** S3 開發者執行 `pnpm run lint`
- **Then** exit code 0，零錯誤

Category: Illustrative
Origin: PO

#### S-sdk-04: ESLint 捕捉 React hooks 違規

> 驗證 ESLint 包含 React hooks rules（不只是基本的 JS/TS rules）

- **Given** S2 ESLint config 包含 React hooks plugin（沿用自 create-vite template）
- **When** S3 開發者寫一個元件包含 `if (condition) { useChat() }`（conditional hook call）
- **Then** `pnpm run lint` 報告 hooks rules 違規錯誤

Category: Illustrative
Origin: Dev (contest → PO strengthened Rule 8)

### Rule: Directory structure 符合設計 contract

#### S-sdk-05: S3 預留目錄和 config 檔案存在

> 驗證 scaffold 的目錄結構已準備好供 S3 使用

- **Given** S2 scaffold 已交付
- **When** S3 開發者檢查 `frontend/` 目錄
- **Then** `src/components/primitives/`、`src/components/ui/`、`src/hooks/`、`src/lib/` 目錄存在；`components/ui/` 和 `hooks/` 為空（預留給 S3）；`lib/utils.ts` 包含 `cn()` function；所有 config 檔案（`components.json`、`vite.config.ts`、`vitest.config.ts`、`playwright.config.ts`、`tsconfig.json`、`eslint.config.js`）都存在

Category: Illustrative
Origin: PO

### Rule: S2 不包含 S3 的關注事項

#### S-sdk-06: 無 chat 邏輯、API 呼叫、或 markdown 依賴

> 驗證 scope guardrail——S2 是純 infrastructure

- **Given** S2 scaffold 已交付
- **When** S3 開發者搜尋 codebase
- **Then** 零 `useChat()` 呼叫、零 `fetch(` 或 `axios` 對 API endpoint 的呼叫、`package.json` 中無 `react-markdown` 或類似 markdown packages、無 `'use server'` 或 `next/` imports

Category: Illustrative
Origin: PO

---

### Journey Scenarios

#### J-scaffold-01: S3 開發者 Onboarding — Zero-friction 交接

> 證明完整的 S2→S3 交接流程：install → dev server → styling → component add → tests → AI SDK type-check

- **Given** S3 開發者 fresh clone repository
- **When** 他們依序執行 `pnpm install`、啟動 dev server 確認 App shell 以 Tailwind styling 渲染、新增 shadcn button 元件確認落在 `primitives/`、執行 unit tests、執行 E2E tests、寫 AI SDK import 確認 type-check 通過
- **Then** 每一步都無錯誤成功——scaffold 已準備好供 S3 streaming chat UI 開發

Category: Journey
Origin: Multiple

#### J-scaffold-02: Styling Pipeline End-to-End — Tailwind + shadcn + Dark Mode

> 證明完整的 styling stack 運作：Tailwind utilities、shadcn CSS variables、dark mode toggle

- **Given** S2 scaffold 已安裝，dev server 運行中
- **When** S3 開發者看到 App shell 的 Tailwind styling、新增 shadcn Button 元件確認以 theme colors 渲染、透過 `dark` class 切換 dark mode
- **Then** 所有視覺狀態正確：App shell 有 styling、Button 以 primary colors 可見、dark mode 改變 theme 色彩

Category: Journey
Origin: Multiple
