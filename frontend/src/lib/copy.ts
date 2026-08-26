/**
 * Centralized UI Copy (see CONTEXT.md "UI Copy"). Grouped by domain concept,
 * not by component location. Excludes user-generated/model content and any
 * text that originates from the backend (HTTP error `detail`, SSE error
 * messages, sanitized tool errors) — those stay untranslated at their source.
 */
export const copy = {
  activityIndicator: {
    thinking: "思考中",
    stalled: "仍在處理中",
  },

  reasoningChip: {
    thinkingLive: "思考中…",
    stalledLive: "仍在處理中…",
    thoughtFor: (seconds: number): string => `思考了 ${seconds} 秒`,
    stoppedThoughtFor: (seconds: number): string => `已停止 — 思考了 ${seconds} 秒`,
    toggleAriaLabel: (headerLabel: string, showBody: boolean): string =>
      `${headerLabel} — ${showBody ? "收合" : "展開"}推理過程`,
  },

  errorBlock: {
    showDetails: "顯示詳情",
    hideDetails: "隱藏詳情",
    showMore: "顯示更多",
    retry: "重試",
    retryAriaLabel: "重試",
  },

  errorMessages: {
    regenerateFailed: "無法重新產生這則回覆，請再試一次。",
    conversationNotFound: "找不到這個對話，請重新整理頁面以開始新對話。",
    sessionBusy: "系統忙碌中，請稍後再試一次。",
    serverError: "伺服器發生錯誤，請再試一次。",
    preStreamFallback: "發生錯誤，請再試一次。",
    networkError: "連線中斷，請檢查網路連線後再試一次。",
    toolBudgetReached: "這次請求的工具呼叫次數已達上限。",
    tooManyRequests: "請求過於頻繁，請稍候片刻後再試。",
    dataNotFound: "找不到相關資料。",
    toolTimeout: "工具執行逾時，請再試一次。",
    accessDenied: "沒有權限存取這項資源。",
    toolFailedFallback: "工具執行失敗，請再試一次。",
    conversationTooLong: "這段對話已經太長，請開啟新對話繼續。",
    midStreamFallback: "產生回覆時發生錯誤，請再試一次。",
    httpStatusFallback: (status: number): string => `HTTP 錯誤 ${status}`,
  },

  toolStatus: {
    running: (toolName: string): string => `執行 ${toolName} 中…`,
    completed: (toolName: string): string => `${toolName} 已完成`,
    error: (toolName: string): string => `${toolName} 發生錯誤`,
    aborted: "已中止",
  },

  toolDetail: {
    input: "輸入",
    output: "輸出",
    error: "錯誤",
  },

  toolCard: {
    toggleDetailsAriaLabel: "切換工具詳細資訊",
  },

  chatHeader: {
    clearConversation: "清除對話",
    clearConversationAriaLabel: "清除對話",
  },

  composer: {
    inputAriaLabel: "訊息輸入框",
    inputPlaceholder: "詢問市場、公司或財報相關問題…",
    stopAriaLabel: "停止回應",
    sendAriaLabel: "傳送訊息",
    disclaimer: "AI 生成的回覆可能不準確，重要資訊請自行查證。",
  },

  emptyState: {
    heading: "想了解什麼？",
    subtext: "詢問市場、公司、財報或申報文件相關問題。",
    chips: {
      nvdaNews: "NVDA 最新市場新聞",
      aaplQuote: "查詢 AAPL 股價",
      compareFinancials: "比較 NVDA 和 AMD 財報",
      msftLatest10K: "摘要 MSFT 最新的 10-K 申報文件",
    },
  },

  interruptedMarker: {
    label: "已中斷",
  },

  regenerateButton: {
    label: "重新產生",
    ariaLabel: "重新產生回覆",
  },

  sources: {
    heading: "資料來源",
  },

  chatPanel: {
    responseComplete: "回覆已完成",
  },
} as const;
