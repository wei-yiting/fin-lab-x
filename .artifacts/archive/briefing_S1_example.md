# ⚡ S1 Streaming 快速審閱手冊 (Review Version)

## 🏗️ 核心架構：資料流 (30 秒掃描)

[LangGraph] --(Raw Chunk)--> [Mapper] --(Domain Event)--> [Serializer] --(SSE)--> [Frontend]

> **你的審閱點：**
>
> 1. Mapper 是為了讓後端不被 Vercel AI SDK 的格式綁死，以後換前端框架也免改核心邏輯。
> 2. Serializer 專門處理 API 格式轉換，保持 Orchestrator 純淨。

---

## 🚦 核心決策：為什麼這樣做？ (只看變動)

| 決策點             | 做法                                      | 你的風險評估                                             |
| :----------------- | :---------------------------------------- | :------------------------------------------------------- |
| **會話儲存**       | 用 LangGraph `InMemorySaver`              | **優點：** 實作超快。**缺點：** Server 重啟紀錄會消失。  |
| **追蹤 (Tracing)** | 拔掉 `@observe()`，改用 `CallbackHandler` | **原因：** 解決 Langfuse 在 Streaming 時會斷掉的老問題。 |
| **自訂事件**       | `data-tool-error`                         | **原因：** 官方協議沒這條，我們自己硬加的，前端需配合。  |

---

## 🧪 測試矩陣：我想測出什麼？ (TDD 核心)

你不需要讀 Code，請確認以下場景是否是你關心的：

| 場景 (Scenario) | 預期反應 (Expected)                                    | 是否重要? |
| :-------------- | :----------------------------------------------------- | :-------: |
| **Happy Path**  | 文字 + Tool Call 能順利流動，最後必有 `finish`         |    ✅     |
| **中途斷線**    | 後端立即停止 API 呼叫，Langfuse 顯示「已結束」         |    ✅     |
| **重複生成**    | 刪除舊的 Assistant Message，重新長出一條新的           |    ✅     |
| **並發衝突**    | 同個 User 連按兩次，第二個會被 Lock 住，直到第一個結束 |    ✅     |

---

## 🛠️ 實作護欄 (AI 不准踩的線)

1. **禁止** 在 Tools 裡寫任何與 `SSE` 或 `HTTP` 有關的 Code。
2. **必須** 確保 `DomainEvent` 是 Frozen 的，不准在流動過程中被修改。
3. **必須** 先通過 POC 的 5 個 Gate (Observability) 才能開始寫 Endpoint。

---

## 💬 你的 Action Item

- **如果矩陣表漏掉了你想測的東西，請直接在這裡推翻我。**
- **如果架構圖的解耦方式你滿意，請回覆 "Go"，我會直接開始實作 Task 1。**
