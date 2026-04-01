# S2 Frontend Scaffold — Design Document

> S2 subsystem design。定義前端基礎建設的技術選型、專案結構、與驗收標準。
> 供 `implementation-planning` skill 作為輸入。

---

## 背景

FinLab-X V1 streaming chat 已確認採 subsystem-first 分解：

| Subsystem | 職責 | 依賴 |
|---|---|---|
| **S1** Backend Streaming | Orchestrator.astream() + FastAPI SSE endpoint | — |
| **S2** Frontend Scaffold（本文件） | 前端專案基礎建設、tooling、boilerplate tests | — |
| **S3** Streaming Chat UI | useChat 整合、ChatInterface、message rendering | S1 + S2 |

S1 與 S2 可並行開發，S3 等待 S1 + S2 完成後才開始。

### Codebase 現況

- `frontend/` 目錄目前只有 placeholder `package.json` 和一份過時的 `README.md`（內容描述 Next.js，已確認不採用）
- Backend 已有 FastAPI + LangChain + Langfuse，運行在 `:8000`
- 無任何前端原始碼、config、或測試基礎設施

---

## Scope

### S2 包含

1. Vite + React + TypeScript 專案初始化
2. Tailwind CSS v4 + shadcn/ui 設置
3. AI SDK 安裝（`ai` + `@ai-sdk/react`），確認版本相容
4. Vitest + React Testing Library + jsdom（unit/component test）
5. Playwright（E2E test）
6. Path aliases（`@/`）
8. ESLint 設定
9. 專案目錄結構
10. 基本 App shell（無 chat 邏輯）
11. Boilerplate tests：unit test baseline + Playwright E2E baseline

### S2 不包含

- `useChat` hook 整合（S3）
- `ChatInterface` 元件（S3）
- Message rendering / streaming state management（S3）
- Markdown rendering（S3，選型待定）
- 任何 backend 變更（S1）
- Generative UI 元件（V2+）

---

## 設計決策

| # | 決策 | 選擇 | 理由 |
|---|---|---|---|
| D1 | Build tool | Vite | 輕量、HMR 快、Tailwind/Vitest 原生整合。排除 Next.js（不需 SSR/API routes，backend 全在 Python） |
| D2 | UI framework | React + TypeScript | 生態系最成熟，AI SDK `@ai-sdk/react` 原生支援 |
| D3 | Styling | Tailwind CSS v4 + `@tailwindcss/vite` plugin | Utility-first、與 shadcn/ui 搭配、v4 用 Vite plugin 零額外 config |
| D4 | Component library | shadcn/ui | Copy-paste 架構完全可控、Radix UI accessibility、與 AI SDK Generative UI 生態整合最佳（assistant-ui 基於它） |
| D5 | AI SDK | `ai@^5.0.0` + `@ai-sdk/react@^5.0.0` | V1 scope 只裝不用，確認版本相容。鎖定 `^5.0.0` 因為 design master 的 SSE protocol 依賴 v5 特有 API（`DefaultChatTransport`、UIMessage Stream Protocol）。S3 才開始整合 `useChat` |
| D6 | Unit/Component test | Vitest + React Testing Library + jsdom | RTL 有 `renderHook` 可測 async hooks（為 S3 的 `useChat` 測試鋪路）、`waitFor`/`act` 處理 streaming state、生態最成熟 |
| D7 | E2E test | Playwright | Cypress 的 proxy 架構會 buffer SSE stream（2018 年開的 issue 至今未修），無法測試逐字出現。Playwright auto-wait assertions 天生適合 SSE streaming 驗證 |
| D8 | CORS | Backend 處理（FastAPI CORSMiddleware） | CORS 在 backend 統一設定，前端不做 proxy。屬於 S1 scope |
| D9 | Icons | lucide-react | shadcn/ui 預設搭配 |
| D10 | Dark mode strategy | Class-based（Tailwind v4 `@custom-variant`） | shadcn/ui 元件廣泛使用 `dark:` variants。Tailwind v4 CSS-first config 預設用 `@media (prefers-color-scheme: dark)`，無法支援 programmatic toggle。須在 `index.css` 設定 class-based dark mode variant，S3 才能實作 theme 切換 |
| D11 | Package manager | pnpm | 專案統一使用 pnpm。所有 CLI 指令用 `pnpm run`、`pnpm dlx`、`pnpm exec` |

---

## 依賴

### Production

| Package | 用途 |
|---|---|
| `react`, `react-dom` | UI framework |
| `ai` | AI SDK core（DefaultChatTransport 等，S3 使用） |
| `@ai-sdk/react` | useChat hook（S3 使用） |
| `tailwindcss`, `@tailwindcss/vite` | Styling |
| `lucide-react` | Icons |

### Development

| Package | 用途 |
|---|---|
| `typescript` | Type checking |
| `vite`, `@vitejs/plugin-react` | Build + HMR |
| `vitest`, `jsdom` | Test runner + DOM 環境 |
| `@testing-library/react` | Component testing |
| `@testing-library/jest-dom` | DOM assertion matchers |
| `@testing-library/user-event` | User interaction simulation |
| `@playwright/test` | E2E testing |
| `eslint` | Linting |

> AI SDK 鎖定 `^5.0.0`（見 D5）。其餘依賴版本以 `pnpm create vite@latest` 和 `pnpm dlx shadcn@latest init` 安裝的版本為準。

---

## 專案結構

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── primitives/    ← shadcn/ui 原始元件（CLI add 進來，盡量不改）
│   │   └── ui/            ← 基於 primitives 組合/客製的元件（S3 開始用）
│   ├── hooks/             ← custom hooks（S3 開始使用）
│   ├── lib/
│   │   └── utils.ts       ← shadcn/ui cn() utility
│   ├── App.tsx            ← 基本 shell（heading + placeholder）
│   ├── App.test.tsx       ← unit test baseline
│   ├── main.tsx           ← entry point
│   └── index.css          ← Tailwind CSS 入口
├── e2e/
│   └── app.spec.ts        ← Playwright E2E baseline
├── components.json         ← shadcn/ui config
├── vite.config.ts          ← Vite config + Tailwind plugin
├── vitest.config.ts        ← Vitest config（environment: jsdom）
├── playwright.config.ts    ← Playwright config（webServer: vite dev）
├── tsconfig.json           ← TypeScript config + path aliases
├── tsconfig.app.json
├── eslint.config.js
├── package.json
└── index.html
```

---

## 關鍵 Configuration

### Vite Config（`vite.config.ts`）

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

### shadcn/ui Config（`components.json`）

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "radix-nova",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/primitives",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
```

### Playwright Config（`playwright.config.ts`）

```ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  webServer: {
    command: 'pnpm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
  use: {
    baseURL: 'http://localhost:5173',
  },
})
```

### Vitest Config（`vitest.config.ts`）

```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

---

## Boilerplate Tests

### Unit Test Baseline（`src/App.test.tsx`）

驗證 React + Vitest + RTL pipeline 正常運作：
- App component renders 成功
- 頁面包含預期的 heading 文字
- 使用 `screen.getByRole` query

### E2E Test Baseline（`e2e/app.spec.ts`）

驗證 Vite dev server + Playwright pipeline 正常運作：
- 啟動 Vite dev server（透過 `webServer` config）
- 瀏覽器開啟 `http://localhost:5173`
- 頁面載入成功，title 或 heading 正確顯示

---

## Acceptance Criteria

| # | 條件 | 驗證方式 |
|---|---|---|
| AC1 | `pnpm run dev` 啟動 Vite dev server 在 `:5173`（`strictPort: true`） | 手動 / CI |
| AC2 | 瀏覽器開啟 `localhost:5173` 看到 App shell | 手動 |
| AC3 | Tailwind utility classes 正常套用（如 `bg-blue-500`） | 視覺確認 |
| AC4 | shadcn/ui 元件可透過 CLI 新增（如 `pnpm dlx shadcn@latest add button`） | 執行命令 |
| AC5 | `@/` path alias 在 import 中正常解析 | TypeScript compile |
| AC6 | shadcn/ui CLI add 元件時，檔案落在 `src/components/primitives/` | 執行 `pnpm dlx shadcn@latest add button` 確認路徑 |
| AC7 | `pnpm run test` 執行 Vitest，unit test baseline 通過 | `vitest run` |
| AC8 | `pnpm run test:e2e` 執行 Playwright E2E test baseline 通過 | `playwright test` |
| AC9 | AI SDK `^5.0.0` 已安裝且 TypeScript 可 import 無型別錯誤 | `tsc --noEmit` |
| AC10 | ESLint 無 error | `pnpm run lint` |

---

## Must NOT Have（範圍護欄）

- ❌ useChat hook 整合或任何 streaming 邏輯
- ❌ Chat UI 元件（ChatInterface、message list、input form）
- ❌ API 呼叫或 backend 互動
- ❌ Markdown rendering 依賴（react-markdown、shiki 等）
- ❌ 任何 backend 程式碼變更
- ❌ Next.js patterns（no SSR、no server components、no route.ts）
- ❌ Message persistence 或 session management

---

## 與其他 Subsystem 的介面契約

### S2 → S3 提供

- 已設定好的 Vite + React + TypeScript 專案
- Tailwind CSS + shadcn/ui 可用（primitives 目錄已建立）
- `ai` + `@ai-sdk/react` 已安裝
- Vitest + RTL test 基礎設施
- Playwright E2E 基礎設施
- `@/` path alias

### S2 對 S1 的假設

- Backend 在 `:8000` 提供 API（S2 不依賴 S1 完成）
- CORS 由 S1 在 backend 處理（FastAPI CORSMiddleware）
