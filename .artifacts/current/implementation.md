# Implementation Plan: S2 Frontend Scaffold

> Design Reference: [`design_S2_frontend_scaffold.md`](./design_S2_frontend_scaffold.md)
> Master Design: [`design_master.md`](./design_master.md)
> Updated: 2026-03-31 — BDD session decisions: pnpm confirmed, AI SDK ^5.0.0 pinned, strictPort: true added, dark mode class strategy added

**Goal:** Build the frontend project infrastructure (Vite + React + TypeScript + Tailwind CSS v4 + shadcn/ui + test pipelines) so that S3 Streaming Chat UI can start building on a fully working scaffold.

**Architecture / Key Decisions:** Vite SPA (no SSR/Next.js) with Tailwind CSS v4 via `@tailwindcss/vite` plugin and shadcn/ui for component primitives. shadcn/ui components land in `src/components/primitives/` (custom alias, not default `ui/`). AI SDK (`ai` + `@ai-sdk/react`) is installed but not used until S3. Vitest for unit/component tests, Browser-Use CLI for implementation/BDD browser verification, Playwright for final E2E tests.

**Tech Stack:** Vite, React 19, TypeScript, Tailwind CSS v4, shadcn/ui (radix-nova style), AI SDK v5, Vitest, React Testing Library, Playwright, ESLint

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
| --- | --- | --- | --- | --- |
| shadcn/ui | latest | Context7 `/shadcn/ui` | `pnpm dlx shadcn@latest init -t vite` is the official Vite initialization command. `components.json` supports custom `ui` alias path. `style: "radix-nova"` confirmed in official manual.mdx | `rsc: false` required for non-Next.js projects |
| AI SDK | v5 stable (`^5.0.0`) | Context7 `/vercel/ai/ai_5_0_0` | `useChat` lives in `@ai-sdk/react` (not `ai/react`). `DefaultChatTransport` lives in `ai` core. Install: `pnpm add ai@^5.0.0 @ai-sdk/react@^5.0.0`. 鎖定 `^5.0.0` 因為 design master SSE protocol 依賴 v5 API | v5 API: `sendMessage()` + `message.parts[]` pattern (S3 concern) |
| Tailwind CSS v4 | v4 | shadcn/ui Vite installation docs | v4 uses `@tailwindcss/vite` plugin, CSS-first config (`@import "tailwindcss"`), no `tailwind.config.js` needed | `pnpm dlx shadcn@latest init -t vite` handles Tailwind v4 installation |

## Constraints

- No chat logic, `useChat` integration, or streaming state management (S3 scope)
- No backend code changes (S1 scope)
- No Markdown rendering dependencies
- `frontend/` directory currently has only a placeholder `package.json` and outdated `README.md` — both will be replaced
- All pnpm commands run from `frontend/` directory
- `.gitignore` at repo root needs `node_modules/` entry for frontend

---

## File Plan

| Operation | Path | Purpose |
| --- | --- | --- |
| Delete | `frontend/README.md` | Outdated Next.js content, replaced by Vite scaffold |
| Overwrite | `frontend/package.json` | Replace placeholder with Vite-scaffolded package.json |
| Create | `frontend/index.html` | Vite entry HTML |
| Create | `frontend/vite.config.ts` | Vite config + Tailwind plugin + path alias |
| Create | `frontend/tsconfig.json` | Root TypeScript config |
| Create | `frontend/tsconfig.app.json` | App TypeScript config with path aliases |
| Create | `frontend/tsconfig.node.json` | Node TypeScript config (for vite.config.ts) |
| Create | `frontend/eslint.config.js` | ESLint config (from Vite template) |
| Create | `frontend/components.json` | shadcn/ui config with custom primitives path |
| Create | `frontend/src/main.tsx` | React entry point |
| Create | `frontend/src/App.tsx` | Basic App shell (heading + placeholder text) |
| Create | `frontend/src/index.css` | Tailwind CSS v4 entry + shadcn theme |
| Create | `frontend/src/vite-env.d.ts` | Vite type declarations |
| Create | `frontend/src/lib/utils.ts` | shadcn/ui `cn()` utility |
| Create | `frontend/src/components/primitives/` | shadcn/ui component directory (populated by CLI add) |
| Create | `frontend/src/components/ui/` | Custom composed components directory (empty, for S3) |
| Create | `frontend/src/hooks/` | Custom hooks directory (empty, for S3) |
| Create | `frontend/vitest.config.ts` | Vitest config (jsdom environment) |
| Create | `frontend/src/test-setup.ts` | Vitest setup: import jest-dom matchers |
| Create | `frontend/src/App.test.tsx` | Unit test baseline |
| Create | `frontend/playwright.config.ts` | Playwright config with Vite webServer |
| Create | `frontend/e2e/app.spec.ts` | E2E test baseline |
| Update | `.gitignore` | Add `node_modules/` for frontend |

**Structure sketch:**

```text
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── primitives/    ← shadcn/ui CLI 產出（button.tsx 等）
│   │   └── ui/            ← S3 自訂元件（目前空）
│   ├── hooks/             ← S3 自訂 hooks（目前空）
│   ├── lib/
│   │   └── utils.ts       ← cn() utility
│   ├── App.tsx
│   ├── App.test.tsx
│   ├── main.tsx
│   ├── index.css
│   ├── test-setup.ts
│   └── vite-env.d.ts
├── e2e/
│   └── app.spec.ts
├── components.json
├── vite.config.ts
├── vitest.config.ts
├── playwright.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── eslint.config.js
├── package.json
└── index.html
```

---

### Task 0: Install Browser-Use CLI + Verify Browser Visibility

**Files:** None (tooling installation only, no project files created)

**What & Why:** Install Browser-Use CLI and verify it can open a browser and capture a visible page. Subsequent tasks (Task 2–3) rely on Browser-Use CLI for visual verification of Tailwind styling and shadcn/ui rendering. This task ensures the tool chain is operational before any browser-dependent verification.

**Implementation Notes:**

- Install Browser-Use CLI globally or in a virtual environment (not a project dependency)
- Run a smoke test: open any URL (e.g., `https://example.com`) and take a screenshot to confirm the tool can see the page
- If Browser-Use CLI requires browser drivers, install them here

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Targeted | `browser-use open https://example.com` + `browser-use screenshot /tmp/task0-smoke.png` | Screenshot file created, shows rendered page content | Proves Browser-Use CLI can launch browser and capture visible output |

**Execution Checklist:**

- [ ] Install Browser-Use CLI
- [ ] Run smoke test: open a page and take a screenshot
- [ ] Confirm screenshot shows rendered content (not blank/error)
- [ ] No commit needed — this is tooling setup, not project code

---

### Task 1: Initialize Vite + React + TypeScript Project

**Files:**

- Delete: `frontend/README.md`
- Overwrite: `frontend/package.json`
- Create: `frontend/index.html`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`, `frontend/eslint.config.js`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/App.css`, `frontend/src/index.css`, `frontend/src/vite-env.d.ts`, `frontend/public/vite.svg`, `frontend/src/assets/react.svg`

**What & Why:** Scaffold the base Vite + React + TypeScript project, replacing the placeholder files. This establishes the build toolchain and dev server that all subsequent tasks depend on.

**Implementation Notes:**

- Remove existing `README.md` and `package.json` before scaffolding to avoid `create-vite` prompting about non-empty directory
- Use `pnpm create vite@latest . --template react-ts` inside `frontend/` to scaffold in place
- The Vite react-ts template includes ESLint config out of the box
- Do not modify any generated files yet — subsequent tasks will customize them

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Targeted | `cd frontend && pnpm install && pnpm run dev` | Vite dev server starts on `http://localhost:5173`, terminal shows "Local: http://localhost:5173/" | Proves project scaffolding and dependency installation work |
| Targeted | `cd frontend && pnpm exec tsc --noEmit` | Exit code 0, no errors | Proves TypeScript config is valid |

**Execution Checklist:**

- [ ] Remove `frontend/README.md` and `frontend/package.json`
- [ ] Run `cd frontend && pnpm create vite@latest . --template react-ts`
- [ ] Run `cd frontend && pnpm install`
- [ ] Run verification: `pnpm run dev` starts successfully, `pnpm exec tsc --noEmit` passes
- [ ] Commit: `git commit -m "feat(frontend): initialize Vite + React + TypeScript project"`

---

### Task 2: Tailwind CSS v4 + shadcn/ui Setup

**Files:**

- Update: `frontend/package.json` (new dependencies)
- Update: `frontend/vite.config.ts` (add Tailwind plugin + path alias)
- Update: `frontend/tsconfig.json` (add path alias baseUrl)
- Update: `frontend/tsconfig.app.json` (add path alias)
- Create: `frontend/components.json`
- Update: `frontend/src/index.css` (Tailwind imports + theme)
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/components/primitives/` (via shadcn CLI add)

**What & Why:** Install Tailwind CSS v4 and configure shadcn/ui with custom `primitives/` path. This establishes the styling foundation and component primitive pipeline that S3 depends on.

**Implementation Notes:**

- Run `pnpm dlx shadcn@latest init` from `frontend/` directory. When prompted, select:
  - Style: `radix-nova`
  - Base color: `neutral`
  - CSS variables: yes
  - CSS file: `src/index.css`
  - The init command installs `tailwindcss`, `@tailwindcss/vite`, `tw-animate-css`, `class-variance-authority`, `clsx`, `tailwind-merge` and creates `components.json`, `src/lib/utils.ts`, updates `vite.config.ts`, `tsconfig.json`, `tsconfig.app.json`
- After init, edit `components.json` to change the `ui` alias from `@/components/ui` to `@/components/primitives`
- Verify with `pnpm dlx shadcn@latest add button` — the file must land at `src/components/primitives/button.tsx`
- Ensure `vite.config.ts` has both the `tailwindcss()` plugin and `@` path alias as specified in design doc

**Critical Contract — `components.json`:**

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

**Critical Contract — `vite.config.ts` (final shape):**

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

**Test Strategy:** No automated tests for this task. Verification is via visual confirmation and CLI output.

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Targeted | `cd frontend && pnpm exec tsc --noEmit` | Exit code 0 | Path aliases resolve correctly in TypeScript |
| Targeted | `cd frontend && pnpm dlx shadcn@latest add button` | File created at `src/components/primitives/button.tsx` | Proves `ui` alias in `components.json` works |
| Targeted | `cd frontend && pnpm run dev`, open browser at `localhost:5173` | Page renders with Tailwind utility classes applied (verify in next task's App shell) | Proves Tailwind CSS v4 pipeline works |

**Execution Checklist:**

- [ ] Run `cd frontend && pnpm dlx shadcn@latest init` and answer prompts per implementation notes
- [ ] Edit `components.json`: change `"ui"` alias to `"@/components/primitives"`
- [ ] Verify `vite.config.ts` matches the critical contract (tailwindcss plugin + path alias + `server: { port: 5173, strictPort: true }`)
- [ ] Verify `tsconfig.app.json` has `"baseUrl": "."` and `"paths": { "@/*": ["./src/*"] }`
- [ ] Verify `index.css` uses Tailwind v4 syntax (`@import "tailwindcss"`, not `@tailwind` directives)
- [ ] Configure class-based dark mode variant in `index.css` for Tailwind v4 (shadcn/ui requires class strategy, not media query)
- [ ] Run `pnpm dlx shadcn@latest add button` and confirm file lands at `src/components/primitives/button.tsx`
- [ ] Run `pnpm exec tsc --noEmit` — exit code 0
- [ ] Commit: `git commit -m "feat(frontend): configure Tailwind CSS v4 + shadcn/ui with custom primitives path"`

---

### Task 3: App Shell + Directory Structure + AI SDK

**Files:**

- Update: `frontend/src/App.tsx` (replace Vite boilerplate with App shell)
- Delete: `frontend/src/App.css` (styling via Tailwind, not CSS modules)
- Create: `frontend/src/components/ui/.gitkeep`
- Create: `frontend/src/hooks/.gitkeep`
- Update: `frontend/package.json` (add `ai`, `@ai-sdk/react`, `lucide-react`)
- Update: `.gitignore` (add `node_modules/`)

**What & Why:** Replace the Vite boilerplate with a minimal App shell, create the directory structure S3 needs, and install AI SDK + lucide-react. Grouping these together because they're all lightweight setup steps that produce the final scaffold shape.

**Implementation Notes:**

- `App.tsx` should render a heading (`h1`) and a placeholder paragraph — no chat logic
- Use Tailwind utility classes on the shell to serve as AC3 visual verification
- Remove `App.css` since all styling goes through Tailwind
- Remove `frontend/src/assets/` and `frontend/public/vite.svg` (Vite logo boilerplate)
- Install AI SDK: `pnpm add ai@^5.0.0 @ai-sdk/react@^5.0.0 lucide-react`
- Add `node_modules/` to root `.gitignore`

**Critical Contract — `App.tsx`:**

```tsx
function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto max-w-4xl p-8">
        <h1 className="text-3xl font-bold">FinLab-X</h1>
        <p className="mt-4 text-muted-foreground">
          AI-powered financial analysis assistant.
        </p>
      </div>
    </div>
  )
}

export default App
```

**Test Strategy:** No automated tests yet (Task 5 adds unit test). Verification is visual + TypeScript compile.

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Targeted | `cd frontend && pnpm run dev`, open `localhost:5173` | Page shows "FinLab-X" heading with Tailwind styling (bg color, font sizing) | AC2 + AC3: App shell renders with Tailwind |
| Targeted | `cd frontend && pnpm exec tsc --noEmit` | Exit code 0 | AC9: AI SDK packages installed, TypeScript resolves types |
| Targeted | `cd frontend && pnpm ls ai @ai-sdk/react lucide-react` | All three packages listed without errors | Packages installed correctly |

**Execution Checklist:**

- [ ] Delete `frontend/src/App.css`, `frontend/src/assets/`, `frontend/public/vite.svg`
- [ ] Rewrite `frontend/src/App.tsx` to App shell per critical contract
- [ ] Verify `frontend/src/main.tsx` does not import `App.css` (the Vite template imports it in `App.tsx`, which is already replaced above)
- [ ] Create `frontend/src/components/ui/.gitkeep` and `frontend/src/hooks/.gitkeep`
- [ ] Run `cd frontend && pnpm add ai@^5.0.0 @ai-sdk/react@^5.0.0 lucide-react`
- [ ] Add `node_modules/` to root `.gitignore`
- [ ] Run verification: dev server shows App shell, `pnpm exec tsc --noEmit` passes
- [ ] Commit: `git commit -m "feat(frontend): add App shell, directory structure, and AI SDK"`

---

### Flow Verification: Dev Server + Styling Pipeline

> Tasks 1–3 complete the development server and styling pipeline. All verifications must pass before proceeding to test infrastructure tasks.

| # | Method | Step | Expected Result |
| --- | --- | --- | --- |
| 1 | Browser-Use CLI | Open `http://localhost:5173` | Page loads, shows "FinLab-X" heading with Tailwind-applied styling (background color, font) |
| 2 | Browser-Use CLI | Inspect element, check computed styles on `h1` | `font-weight: 700` (bold), `font-size` matches `text-3xl` |
| 3 | CLI | `cd frontend && pnpm exec tsc --noEmit` | Exit code 0, no type errors |
| 4 | CLI | `cd frontend && ls src/components/primitives/button.tsx` | File exists (from Task 2 shadcn add) |
| 5 | CLI | `cd frontend && pnpm ls ai @ai-sdk/react` | Both packages listed, no missing peer deps |

- [ ] All flow verifications pass

---

### Task 4: Vitest + React Testing Library + Unit Test Baseline

**Files:**

- Update: `frontend/package.json` (add dev deps)
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test-setup.ts`
- Create: `frontend/src/App.test.tsx`

**What & Why:** Set up the unit/component test infrastructure with Vitest + RTL + jsdom. Write a baseline test for `App.tsx` to prove the pipeline works. This lays the foundation for S3's `useChat` hook testing. Execution 過程中的 BDD browser 驗證使用 Browser-Use CLI，Playwright 僅用於最終 E2E test（Task 5）。

**Implementation Notes:**

- Install: `pnpm add -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event`
- `vitest.config.ts` uses separate config from `vite.config.ts` with `jsdom` environment and `globals: true`
- `test-setup.ts` imports `@testing-library/jest-dom/vitest` to extend `expect` with DOM matchers
- Add `"test": "vitest run"` and `"test:watch": "vitest"` to `package.json` scripts
- `App.test.tsx` verifies the heading renders via `screen.getByRole('heading')`

**Critical Contract — `vitest.config.ts`:**

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

**Critical Contract — `src/test-setup.ts`:**

```ts
import '@testing-library/jest-dom/vitest'
```

**Critical Contract — `src/App.test.tsx`:**

```tsx
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders the heading', () => {
    render(<App />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('FinLab-X')
  })
})
```

**Test Strategy:** The test proves the Vitest + RTL + jsdom pipeline works end to end. It uses `screen.getByRole` (accessible query) and `toHaveTextContent` (jest-dom matcher) to verify both the test runner and the DOM assertion library are correctly wired.

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Targeted | `cd frontend && pnpm run test` | 1 test passes: `App > renders the heading` | AC7: Vitest unit test pipeline works |
| Targeted | `cd frontend && pnpm exec tsc --noEmit` | Exit code 0 | Test file type-checks correctly |

**Execution Checklist:**

- [ ] Run `cd frontend && pnpm add -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event`
- [ ] Create `frontend/vitest.config.ts` per critical contract
- [ ] Create `frontend/src/test-setup.ts` per critical contract
- [ ] Add `"test": "vitest run"` and `"test:watch": "vitest"` to `package.json` scripts
- [ ] Create `frontend/src/App.test.tsx` per critical contract
- [ ] Run `pnpm run test` — 1 test passes
- [ ] Commit: `git commit -m "test(frontend): add Vitest + RTL setup and App unit test baseline"`

---

### Task 5: Playwright E2E Setup + Baseline Test

**Files:**

- Update: `frontend/package.json` (add dev dep)
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/app.spec.ts`

**What & Why:** Set up Playwright E2E test infrastructure with a webServer config that auto-starts the Vite dev server. Write a baseline test that verifies the page loads. Playwright is chosen over Cypress because Cypress's proxy architecture buffers SSE streams, making it unsuitable for S3's streaming tests.

**Implementation Notes:**

- Install: `pnpm add -D @playwright/test`
- Install browsers: `npx playwright install --with-deps chromium` (only Chromium needed for dev; CI can install all)
- `playwright.config.ts` uses `webServer` to auto-start `pnpm run dev` and wait for `localhost:5173`
- E2E test navigates to root and verifies the heading is visible
- Add `"test:e2e": "playwright test"` to `package.json` scripts

**Critical Contract — `playwright.config.ts`:**

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

**Critical Contract — `e2e/app.spec.ts`:**

```ts
import { test, expect } from '@playwright/test'

test('app shell loads and displays heading', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('FinLab-X')
})
```

**Test Strategy:** The E2E test proves the full Vite dev server → browser → assertion pipeline works. It uses Playwright's auto-wait `toHaveText` assertion, which is the same pattern S3 will use for streaming verification.

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Targeted | `cd frontend && pnpm run test:e2e` | 1 test passes: `app shell loads and displays heading` | AC8: Playwright E2E pipeline works |

**Execution Checklist:**

- [ ] Run `cd frontend && pnpm add -D @playwright/test`
- [ ] Run `cd frontend && npx playwright install --with-deps chromium`
- [ ] Create `frontend/playwright.config.ts` per critical contract
- [ ] Create `frontend/e2e/app.spec.ts` per critical contract
- [ ] Add `"test:e2e": "playwright test"` to `package.json` scripts
- [ ] Run `pnpm run test:e2e` — 1 test passes
- [ ] Commit: `git commit -m "test(frontend): add Playwright E2E setup and baseline test"`

---

### Flow Verification: Full Test Pipeline

> Tasks 4–5 complete the test infrastructure. All verifications must pass before final delivery.

| # | Method | Step | Expected Result |
| --- | --- | --- | --- |
| 1 | CLI | `cd frontend && pnpm run test` | Vitest: 1 test passes |
| 2 | CLI | `cd frontend && pnpm run test:e2e` | Playwright: 1 test passes |
| 3 | CLI | `cd frontend && pnpm exec tsc --noEmit` | Exit code 0, no type errors |

- [ ] All flow verifications pass

---

### Task 6: ESLint Verification + .gitignore + Final Acceptance

**Files:**

- Update: `frontend/eslint.config.js` (verify, fix if needed)
- Update: `.gitignore` (verify `node_modules/` is present)

**What & Why:** Verify ESLint passes on all source files, ensure `.gitignore` covers frontend artifacts, and run all acceptance criteria from the design doc as a final gate.

**Implementation Notes:**

- The Vite react-ts template generates `eslint.config.js` with React + TypeScript rules
- Run `pnpm run lint` from `frontend/` to verify no errors
- If ESLint reports errors in generated/scaffold files, fix them
- Add `dist/`, `test-results/`, `playwright-report/` to root `.gitignore`（`node_modules/` already added in Task 3）

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Targeted | `cd frontend && pnpm run lint` | Exit code 0, no errors | AC10: ESLint clean |
| Broader | `cd frontend && pnpm run dev` | Dev server on `:5173` | AC1 |
| Broader | `cd frontend && pnpm exec tsc --noEmit` | Exit code 0 | AC5 + AC9 |
| Broader | `cd frontend && pnpm run test` | All tests pass | AC7 |
| Broader | `cd frontend && pnpm run test:e2e` | All tests pass | AC8 |

**Execution Checklist:**

- [ ] Run `cd frontend && pnpm run lint` — fix any errors
- [ ] Add `dist/`, `test-results/`, `playwright-report/` to root `.gitignore`
- [ ] Run full acceptance suite (all verification commands above)
- [ ] Commit: `git commit -m "chore(frontend): verify ESLint and finalize S2 scaffold"`

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] `cd frontend && pnpm run test` — Vitest passes (1 test)
- [ ] `cd frontend && pnpm run test:e2e` — Playwright passes (1 test)
- [ ] `cd frontend && pnpm run lint` — no errors
- [ ] `cd frontend && pnpm exec tsc --noEmit` — no type errors
- [ ] `cd frontend && pnpm run build` — Vite build succeeds

### Flow Level (Behavioral)

- [ ] All flow verification steps executed and passed
- [ ] Flow: Dev Server + Styling Pipeline — PASS / FAIL
- [ ] Flow: Full Test Pipeline — PASS / FAIL

### Acceptance Criteria Cross-Check

| AC | Description | Verification |
| --- | --- | --- |
| AC1 | `pnpm run dev` 在 `:5173` 啟動 | `pnpm run dev` |
| AC2 | 瀏覽器看到 App shell | Browser check |
| AC3 | Tailwind utility classes 正常套用 | Visual: `bg-background`, `text-3xl`, `font-bold` |
| AC4 | shadcn/ui CLI 可新增元件 | `pnpm dlx shadcn@latest add button` |
| AC5 | `@/` path alias 正常解析 | `pnpm exec tsc --noEmit` |
| AC6 | shadcn CLI add 落在 `primitives/` | `ls src/components/primitives/button.tsx` |
| AC7 | Vitest unit test 通過 | `pnpm run test` |
| AC8 | Playwright E2E test 通過 | `pnpm run test:e2e` |
| AC9 | AI SDK 已安裝、TypeScript 無型別錯誤 | `pnpm ls ai @ai-sdk/react` + `pnpm exec tsc --noEmit` |
| AC10 | ESLint 無 error | `pnpm run lint` |

### Summary

- [ ] Both levels pass → ready for delivery
- [ ] Any failure is documented with cause and next action
