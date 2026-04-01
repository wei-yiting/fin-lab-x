# Verification Plan — S2 Frontend Scaffold

## Meta

- Scenarios Reference: `.artifacts/current/bdd_scenarios_S2_frontend_scaffold.md`
- Generated: 2026-03-31

---

## Automated Verification

### Deterministic

#### S-env-01: Dev server 啟動並提供 App shell

- **Method**: script
- **Steps**:
  1. `cd frontend && pnpm run dev &` — 背景啟動 dev server
  2. 等待 server ready（poll `http://localhost:5173` 最多 30 秒）
  3. `curl -s http://localhost:5173` — 取得 HTML response
  4. Assert: response 包含 `FinLab-X`
  5. Assert: response 包含 `AI-powered financial analysis assistant`
  6. Kill background dev server
- **Expected**: Dev server 在 :5173 啟動，HTML 包含 App shell 內容

#### S-env-02: Port 5173 被佔用時 dev server 拒絕啟動

- **Method**: script
- **Steps**:
  1. 佔用 port 5173：`python3 -c "import socket; s=socket.socket(); s.bind(('',5173)); s.listen(1); input()" &`
  2. `cd frontend && pnpm run dev 2>&1` — 嘗試啟動 dev server
  3. Capture exit code 和 stderr output
  4. Assert: exit code ≠ 0
  5. Assert: stderr 包含 port 相關錯誤訊息（"5173" 和 "already in use" 或等效）
  6. Kill port-blocking process
- **Expected**: Vite 以 port 衝突錯誤退出（`strictPort: true` 行為）

#### S-env-06: 初始化後 styling pipeline 使用 Tailwind v4 語法（⚠️ Static Check）

> **Note:** 此項為 static code check（grep 檔案內容），非 runtime behavior test。保留於 verification plan 是因為它是 Tailwind v4 styling pipeline 正確運作的前提條件。

- **Method**: script (static check)
- **Steps**:
  1. `cd frontend && cat src/index.css`
  2. Assert: 檔案包含 `@import "tailwindcss"` 或 `@import 'tailwindcss'`
  3. Assert: 檔案不包含 `@tailwind base` 或 `@tailwind components` 或 `@tailwind utilities`
- **Expected**: CSS 使用 v4 import 語法，非 v3 directives

#### S-comp-01: CLI 新增的元件落在 primitives 目錄

- **Method**: script
- **Steps**:
  1. `cd frontend && pnpm dlx shadcn@latest add button --yes` — 自動確認 prompts
  2. Assert: `test -f src/components/primitives/button.tsx` — file exists
  3. Assert: `test ! -f src/components/ui/button.tsx` — file does NOT exist at default path
  4. `grep -q "import.*@/lib/utils" src/components/primitives/button.tsx` — import path 正確
- **Expected**: button.tsx 在 `primitives/`，不在 `ui/`，import 使用 `@/` alias

#### S-comp-02: CLI 新增的元件 import 可解析且 type-check 通過

- **Method**: script
- **Steps**:
  1. 確認 `src/components/primitives/button.tsx` 存在（from S-comp-01）
  2. 建立暫時測試檔 `src/__verify_import.tsx`：
     ```tsx
     import { Button } from '@/components/primitives/button'
     export default function Verify() { return <Button>Test</Button> }
     ```
  3. `cd frontend && pnpm exec tsc --noEmit`
  4. Assert: exit code 0
  5. 刪除 `src/__verify_import.tsx`
- **Expected**: import 解析成功，TypeScript compile 通過

#### S-test-01: Vitest baseline test 透過 pnpm script 通過

- **Method**: script
- **Steps**:
  1. `cd frontend && pnpm run test 2>&1`
  2. Assert: exit code 0
  3. Assert: output 包含 "pass" 或 "✓"（Vitest pass indicator）
  4. Assert: output 包含 "App" 或 "renders the heading"（test name）
- **Expected**: Vitest 發現並通過 App.test.tsx baseline test

#### S-test-02: jest-dom matchers 無需額外設定即可使用

- **Method**: script
- **Steps**:
  1. 確認 `src/test-setup.ts` 存在且包含 `jest-dom`：`grep -q "jest-dom" frontend/src/test-setup.ts`
  2. `cd frontend && pnpm run test 2>&1` — baseline test 使用 jest-dom matchers
  3. Assert: exit code 0（matchers 正確載入）
  4. Assert: output 不包含 "toBeInTheDocument is not a function"
- **Expected**: jest-dom matchers 在 runtime 正確運作

#### S-test-03: Vitest global functions 在 test 檔案中 type-check 通過

- **Method**: script
- **Steps**:
  1. 確認 `src/App.test.tsx` 使用 `describe` 和 `it` 但不 import 它們：`! grep -q "import.*describe\|import.*it\b" frontend/src/App.test.tsx`
  2. `cd frontend && pnpm run test` — runtime check
  3. Assert: exit code 0
  4. `cd frontend && pnpm exec tsc --noEmit` — type check
  5. Assert: exit code 0
  6. Assert: output 不包含 "Cannot find name 'describe'" 或 "Cannot find name 'it'"
- **Expected**: Vitest globals 在 runtime 和 type-check 層級都正常運作

#### S-test-04: Playwright baseline test 搭配自動啟動的 dev server 通過

- **Method**: script
- **Steps**:
  1. 確保無 dev server 運行（kill 任何 :5173 process）
  2. `cd frontend && pnpm run test:e2e 2>&1`
  3. Assert: exit code 0
  4. Assert: output 包含 "passed" 或 "1 passed"（Playwright pass indicator）
- **Expected**: Playwright 透過 webServer config 自動啟動 Vite，baseline test 通過

#### S-test-05: Playwright 在 fresh install 後能執行測試

- **Method**: script
- **Steps**:
  1. `[POST-CODING: 確認 package.json 中是否有 postinstall 或 prepare script 處理 playwright install]`
  2. 如果有 script：`pnpm install` 後直接 `pnpm run test:e2e` — 應可運行
  3. 如果無 script：`pnpm run test:e2e` — 確認錯誤訊息包含修復指示（如 "npx playwright install"）
  4. Assert: 要嘛 test 通過，要嘛錯誤訊息提供清楚的 one-step 修復
- **Expected**: fresh install 後 Playwright 可用或有清楚的修復路徑

#### S-sdk-01: Path alias 在 TypeScript、Vite、和 Vitest 中解析

- **Method**: script
- **Steps**:
  1. 確認 App.test.tsx 或 source 檔使用 `@/` import：`grep -r "@/" frontend/src/ --include="*.tsx" --include="*.ts" -l`
  2. `cd frontend && pnpm run dev &` — 啟動 dev server
  3. 等待 server ready，`curl -s http://localhost:5173` — Assert: 200 OK
  4. Kill dev server
  5. `cd frontend && pnpm run test` — Assert: exit code 0
  6. `cd frontend && pnpm exec tsc --noEmit` — Assert: exit code 0
- **Expected**: `@/` alias 在 dev server、test runner、和 TypeScript compiler 三處都正確解析

#### S-sdk-02: AI SDK v5 imports type-check 成功

- **Method**: script
- **Steps**:
  1. 建立暫時檔 `frontend/src/__verify_ai_sdk.ts`：
     ```ts
     import type { UIMessage } from '@ai-sdk/react'
     import { DefaultChatTransport } from 'ai'
     // Type-only verification — no runtime usage
     type _Check = UIMessage
     const _transport: typeof DefaultChatTransport = DefaultChatTransport
     ```
  2. `cd frontend && pnpm exec tsc --noEmit`
  3. Assert: exit code 0
  4. 確認版本：`cd frontend && pnpm ls ai @ai-sdk/react --depth=0`
  5. Assert: output 顯示 `ai@5.x` 和 `@ai-sdk/react@5.x`
  6. 刪除 `src/__verify_ai_sdk.ts`
- **Expected**: AI SDK v5 imports type-check 通過，安裝版本為 5.x

#### S-sdk-03: ESLint 在 scaffold codebase 上報告零錯誤

- **Method**: script
- **Steps**:
  1. `cd frontend && pnpm run lint 2>&1`
  2. Assert: exit code 0
  3. Assert: output 不包含 "error"（ESLint error indicators）
- **Expected**: ESLint 對所有 S2 source 檔報告零錯誤

#### S-sdk-04: ESLint 捕捉 React hooks 違規

- **Method**: script
- **Steps**:
  1. 建立暫時檔 `frontend/src/__verify_hooks_lint.tsx`：
     ```tsx
     import { useState } from 'react'
     export function BadComponent({ condition }: { condition: boolean }) {
       if (condition) {
         const [state] = useState(0) // hooks rule violation
         return <div>{state}</div>
       }
       return null
     }
     ```
  2. `cd frontend && pnpm run lint 2>&1`
  3. Assert: exit code ≠ 0 或 output 包含 "react-hooks" 相關 error/warning
  4. 刪除 `src/__verify_hooks_lint.tsx`
- **Expected**: ESLint 捕捉到 conditional hook call 違規

#### S-sdk-05: S3 預留目錄和 config 檔案存在

- **Method**: script
- **Steps**:
  1. Assert 目錄存在：
     - `test -d frontend/src/components/primitives`
     - `test -d frontend/src/components/ui`
     - `test -d frontend/src/hooks`
     - `test -d frontend/src/lib`
  2. Assert `ui/` 和 `hooks/` 為空或只含 `.gitkeep`：
     - `[ $(find frontend/src/components/ui -not -name '.gitkeep' -not -path '*/ui' | wc -l) -eq 0 ]`
     - `[ $(find frontend/src/hooks -not -name '.gitkeep' -not -path '*/hooks' | wc -l) -eq 0 ]`
  3. Assert `lib/utils.ts` 包含 `cn` function：`grep -q "function cn\|export.*cn" frontend/src/lib/utils.ts`
  4. Assert config 檔案存在：
     - `test -f frontend/components.json`
     - `test -f frontend/vite.config.ts`
     - `test -f frontend/vitest.config.ts`
     - `test -f frontend/playwright.config.ts`
     - `test -f frontend/tsconfig.json`
     - `test -f frontend/eslint.config.js`
- **Expected**: 所有目錄和 config 檔案存在，S3 預留目錄為空

#### S-sdk-06: 無 chat 邏輯、API 呼叫、或 markdown 依賴

- **Method**: script
- **Steps**:
  1. `grep -r "useChat()" frontend/src/ --include="*.tsx" --include="*.ts" | wc -l` — Assert: 0
  2. `grep -r "fetch(" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v "node_modules" | wc -l` — Assert: 0
  3. `grep -r "axios" frontend/src/ --include="*.tsx" --include="*.ts" | wc -l` — Assert: 0
  4. `cd frontend && pnpm ls react-markdown remark rehype shiki 2>&1` — Assert: 各 package 均顯示 "not found" 或 ERR
  5. `grep -r "'use server'" frontend/src/ --include="*.tsx" --include="*.ts" | wc -l` — Assert: 0
  6. `grep -r "from 'next/" frontend/src/ --include="*.tsx" --include="*.ts" | wc -l` — Assert: 0
- **Expected**: S2 codebase 完全不含 S3 的關注事項

---

### Browser Automation

#### S-env-03: Tailwind utility classes 產生可見 styling

- **Method**: Browser-Use CLI
- **Steps**:
  1. `browser-use open http://localhost:5173`
  2. `browser-use state` → 確認頁面載入
  3. `browser-use screenshot /tmp/s-env-03-shell.png` → 截圖 App shell
  4. 確認 heading "FinLab-X" 可見
  5. 確認頁面有背景色（非白色 default）和 font styling（bold, text-3xl size）
- **Checkpoints**: App shell 截圖應顯示有 Tailwind styling 的頁面，非無樣式 HTML
- **Expected**: 頁面載入，heading 有粗體和正確字型大小，背景色來自 `bg-background` theme variable

#### S-env-04: shadcn/ui CSS custom properties 解析為 theme 色彩

- **Method**: Browser-Use CLI
- **Steps**:
  1. `[POST-CODING: 確認 S-comp-01 已執行，button.tsx 存在]`
  2. `[POST-CODING: 在 App.tsx 中暫時加入 <Button>Click</Button> import 和渲染]`
  3. `browser-use open http://localhost:5173`
  4. `browser-use state` → 找到 button 元素
  5. `browser-use screenshot /tmp/s-env-04-button.png`
  6. Assert: button 有可見的背景色（非 transparent），文字顏色與背景色形成對比
  7. `[POST-CODING: 還原 App.tsx]`
- **Checkpoints**: Button 截圖應顯示有 primary theme 色彩的可見按鈕
- **Expected**: shadcn Button 以 `--primary` / `--primary-foreground` CSS variables 定義的色彩渲染

#### S-env-05: Dark mode variant 回應 class-based 切換

- **Method**: Browser-Use CLI
- **Steps**:
  1. `browser-use open http://localhost:5173`
  2. `browser-use screenshot /tmp/s-env-05-light.png` → 截圖 light mode
  3. `browser-use execute document.documentElement.classList.add('dark')` → 啟用 dark mode
  4. `browser-use screenshot /tmp/s-env-05-dark.png` → 截圖 dark mode
  5. Assert: 兩張截圖在背景色和文字顏色上有明顯差異
- **Checkpoints**: light vs dark 截圖比較
- **Expected**: 加入 `dark` class 後背景和文字色彩切換為 dark theme 值

---

### Journey Scenarios

#### J-scaffold-01: S3 開發者 Onboarding — Zero-friction 交接

##### Deterministic (script chain)

- **Method**: script
- **Steps**:
  1. **Install**: `cd frontend && pnpm install`
     - Assert: exit code 0，無 peer dep errors
  2. **Dev server**: `pnpm run dev &` → 等待 :5173 ready → `curl -s http://localhost:5173`
     - Assert: response 包含 "FinLab-X"
     - Kill dev server
  3. **Unit test**: `pnpm run test`
     - Assert: exit code 0，baseline test 通過
  4. **E2E test**: `pnpm run test:e2e`
     - Assert: exit code 0，baseline test 通過
  5. **shadcn add**: `pnpm dlx shadcn@latest add button --yes`
     - Assert: `test -f src/components/primitives/button.tsx`
  6. **S3 component import**: 建立 `src/components/ui/ChatStub.tsx`：
     ```tsx
     import { Button } from '@/components/primitives/button'
     export function ChatStub() { return <Button>Send</Button> }
     ```
     - `pnpm exec tsc --noEmit` — Assert: exit code 0
  7. **AI SDK import**: 建立 `src/hooks/useChatStub.ts`：
     ```ts
     import { useChat } from '@ai-sdk/react'
     import { DefaultChatTransport } from 'ai'
     export type { DefaultChatTransport }
     export { useChat }
     ```
     - `pnpm exec tsc --noEmit` — Assert: exit code 0
  8. Cleanup：刪除 `ChatStub.tsx` 和 `useChatStub.ts`
- **Expected**: 從 fresh clone 到 S3 就緒的每一步都零錯誤通過

##### Browser Automation (visual flow)

- **Method**: Browser-Use CLI
- **Steps**:
  1. `browser-use open http://localhost:5173`
  2. `browser-use screenshot /tmp/j-scaffold-01-shell.png` → App shell 有 styling
  3. `[POST-CODING: 暫時 render ChatStub component with Button]`
  4. `browser-use open http://localhost:5173`
  5. `browser-use screenshot /tmp/j-scaffold-01-component.png` → S3 component renders
  6. Assert: 兩張截圖都顯示有 styling 的內容
- **Expected**: 視覺確認 App shell 和 S3 component 都正確渲染

#### J-scaffold-02: Styling Pipeline End-to-End — Tailwind + shadcn + Dark Mode

- **Method**: Browser-Use CLI
- **Steps**:
  1. `browser-use open http://localhost:5173`
  2. `browser-use screenshot /tmp/j-scaffold-02-1-shell.png` → Tailwind styling 確認
  3. `[POST-CODING: 暫時在 App.tsx 加入 <Button>Click</Button>]`
  4. `browser-use open http://localhost:5173`
  5. `browser-use screenshot /tmp/j-scaffold-02-2-button.png` → shadcn Button 有 theme color
  6. `browser-use execute document.documentElement.classList.add('dark')`
  7. `browser-use screenshot /tmp/j-scaffold-02-3-dark.png` → dark mode 生效
  8. Assert: 截圖 1 有 light styling，截圖 2 有 Button 且色彩正確，截圖 3 dark mode 色彩不同
- **Checkpoints**: 三個階段的截圖比較：shell → button → dark mode
- **Expected**: styling pipeline 從 Tailwind utilities 到 shadcn CSS variables 到 dark mode 切換全部正常運作

---

## Manual Verification

### User Acceptance Test

#### J-scaffold-01: S3 開發者 Onboarding — Zero-friction 交接

- **Acceptance Question**: S2 scaffold 是否提供零摩擦的 S3 開發體驗？
- **Steps**:
  1. 在 `frontend/` 執行 `pnpm install` 和 `pnpm run dev`
  2. 開啟 `http://localhost:5173` — App shell 是否有 styling？
  3. 執行 `pnpm run test` — 是否通過？
  4. 執行 `pnpm run test:e2e` — 是否通過？
  5. 執行 `pnpm dlx shadcn@latest add button` — 檔案是否落在 `primitives/`？
  6. 執行 `pnpm exec tsc --noEmit` — 是否零錯誤？
  7. 執行 `pnpm run build` — production build 是否成功？
- **Expected**: 每一步都無摩擦成功。S3 開發者無需修改任何 S2 config 即可開始工作。

#### J-scaffold-02: Styling Pipeline End-to-End

- **Acceptance Question**: 整個 styling pipeline 是否視覺上正確且一致？
- **Steps**:
  1. 開啟 dev server，確認 App shell styling
  2. 新增 shadcn Button，確認 theme color 正確（不是 transparent）
  3. Toggle dark mode（DevTools → `document.documentElement.classList.add('dark')`）— theme 色彩是否切換？
  4. 確認 Tailwind utility classes 可 override shadcn 預設值（如 `className="bg-red-500"` 覆蓋 Button 的 `bg-primary`）
- **Expected**: Tailwind utilities、shadcn CSS variables、dark mode 三層 styling 正確互動
