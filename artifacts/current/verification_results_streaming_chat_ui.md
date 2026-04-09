# Verification Results — S3 Streaming Chat UI

## Meta

- Implementation Plan: `artifacts/current/implementation_streaming_chat_ui.md`
- Generated during Milestone 0+ execution.

## V-1 Result: TBD (S1 partial-turn regenerate probe)

_Pending — requires backend running on :8000._

## V-2 Result: PASS — useChat pre-stream HTTP 500 user-message lifecycle

- **Contract test**: `frontend/src/__tests__/contract/use-chat-error-lifecycle.test.ts`
- **Runner**: `pnpm vitest run src/__tests__/contract/use-chat-error-lifecycle.test.ts --reporter=verbose`
- **Result**: 1 passed / 0 failed（`Tests 1 passed (1)`）
- **Assertions confirmed**：
  - `result.current.error` 在 HTTP 500 之後成為 truthy（MSW 攔截 `POST /api/v1/chat` 回 500）。
  - `result.current.messages.length === 1`
  - `result.current.messages[0].role === 'user'`
- **結論**：AI SDK v6（`@ai-sdk/react@3.0.144` + `ai@6.0.142`）在 pre-stream HTTP 500 時**會保留** user message 在 `messages` array 中。`BDD S-err-02` 與 `Ch-Dev-1` 所假設的「user bubble 還在」前提成立，`ChatPanel` **不需要**自己做 `lastUserText` stash/restore（至少對此 SDK 版本而言）。

### Plan defect found — TC-int-v2-01 import path
- `artifacts/current/implementation_test_cases_streaming_chat_ui.md` lines 1637–1640 的 verbatim 版本寫：
  ```ts
  import { useChat, DefaultChatTransport } from '@ai-sdk/react'
  ```
- 但在實際安裝的 AI SDK v6 中，`@ai-sdk/react` 僅 re-export `CreateUIMessage` / `UIMessage` / `UseCompletionOptions`，`DefaultChatTransport` 住在 `ai` package。直接照抄會得到 `TypeError: DefaultChatTransport is not a constructor`，而非 V-2 contract 結果。
- 已在 test file 中修正為：
  ```ts
  import { useChat } from '@ai-sdk/react'
  import { DefaultChatTransport } from 'ai'
  ```
- **行動建議**：後續更新 `implementation_test_cases_streaming_chat_ui.md` 的 TC-int-v2-01 範例（以及 TC-int-v3-01 若引用相同 import），避免 Milestone 1+ 工作者再次踩到同一個坑。此問題與 V-2 contract 本身無關，純粹是計畫文件的 import-path typo。

### Additional notes
- Vitest 設定 `globals: false`，因此 test file 最頂端額外加上 `import { test, expect, beforeAll, afterAll } from 'vitest'`（計畫的 verbatim 片段未包含）。
- `msw@2.13.2` 已加入 `frontend/package.json` devDependencies（僅套件本身，未執行 `pnpm dlx msw init public/`，service worker 初始化屬 M1 範疇）。

## V-3 Result: TBD (useChat.stop() abort semantic)

_Pending — Task 0.3._
