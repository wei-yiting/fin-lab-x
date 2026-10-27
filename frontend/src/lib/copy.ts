/**
 * Centralized UI Copy (see CONTEXT.md "UI Copy"), one dictionary per locale.
 * Grouped by domain concept, not by component location. Excludes
 * user-generated/model content and any text that originates from the backend
 * (HTTP error `detail`, SSE error messages, sanitized tool errors) — those
 * keep their original wording.
 *
 * Components read the active dictionary through `useLocale()`; `zhTW` is
 * typed as `Copy`, so a missing or extra key fails `tsc`.
 */
export type Locale = "en" | "zh-TW";

export const en = {
  meta: {
    documentTitle: "FinLab-X — US Equity Research Agent",
  },

  activityIndicator: {
    thinking: "Thinking",
    stalled: "Still working",
  },

  reasoningChip: {
    thinkingLive: "Thinking…",
    stalledLive: "Still working…",
    thoughtFor: (seconds: number): string => `Thought for ${seconds}s`,
    stoppedThoughtFor: (seconds: number): string => `Stopped — thought for ${seconds}s`,
    toggleAriaLabel: (headerLabel: string, showBody: boolean): string =>
      `${headerLabel} — ${showBody ? "collapse" : "expand"} reasoning`,
  },

  errorBlock: {
    showDetails: "Show details",
    hideDetails: "Hide details",
    showMore: "Show more",
    retry: "Retry",
    retryAriaLabel: "Retry",
  },

  errorMessages: {
    regenerateFailed: "Couldn't regenerate that message. Please try again.",
    conversationNotFound: "Conversation not found. Refresh to start a new one.",
    sessionBusy: "The system is busy. Please try again in a moment.",
    serverError: "Server error. Please try again.",
    preStreamFallback: "Something went wrong. Please try again.",
    networkError: "Connection lost. Check your network and try again.",
    toolBudgetReached: "Tool-call budget reached for this request.",
    tooManyRequests: "Too many requests. Please wait a moment and try again.",
    dataNotFound: "We couldn't find that data.",
    toolTimeout: "The tool timed out. Please try again.",
    accessDenied: "Access denied for this resource.",
    toolFailedFallback: "The tool failed to run. Please try again.",
    conversationTooLong: "This conversation is too long. Start a new chat to continue.",
    midStreamFallback: "Something went wrong while generating the response. Please try again.",
    httpStatusFallback: (status: number): string => `HTTP ${status}`,
  },

  toolStatus: {
    running: (toolName: string): string => `Running ${toolName}...`,
    completed: (toolName: string): string => `Completed ${toolName}`,
    error: (toolName: string): string => `Error in ${toolName}`,
    aborted: "Aborted",
  },

  toolDetail: {
    input: "Input",
    output: "Output",
    error: "Error",
  },

  toolCard: {
    toggleDetailsAriaLabel: "Toggle tool details",
  },

  chatHeader: {
    tagline: "US Equity Research Agent",
    clearConversation: "Clear conversation",
    clearConversationAriaLabel: "Clear conversation",
    languageGroupAriaLabel: "Interface language",
  },

  composer: {
    inputAriaLabel: "Message input",
    inputPlaceholder: "Ask about a US-listed company — filings, financials, or news...",
    stopAriaLabel: "Stop response",
    sendAriaLabel: "Send message",
    disclaimer: "AI-generated responses may be inaccurate. Please verify important information.",
  },

  emptyState: {
    heading: "Research any US-listed stock",
    subtext:
      "An AI research agent that reads SEC 10-K filings, live market data, and recent news, then answers with cited sources.",
    everydayGroupLabel: "Everyday questions",
    analystGroupLabel: "Analyst deep dives",
    chips: {
      priceToday: {
        title: "Today's price move",
        prompt: "How is Apple's stock doing today, and is there any news behind the move?",
      },
      businessModel: {
        title: "How a company makes money",
        prompt: "What does NVIDIA actually sell, and where does most of its revenue come from?",
      },
      valuationCheck: {
        title: "Is it expensive?",
        prompt: "Is Tesla's stock expensive right now? Explain it in plain terms.",
      },
      riskVsNews: {
        title: "Risk disclosures vs. recent news",
        prompt:
          "Which of the export-control and China risks NVIDIA flags in its latest 10-K are already showing up in recent news, and which are still only potential? Cite the filing and the news for each.",
      },
      narrativeVsNumbers: {
        title: "Management narrative vs. the numbers",
        prompt:
          "Microsoft attributes its cloud growth to AI demand. Do its revenue growth and gross margin trends support that story, or is AI infrastructure spending eroding margins?",
      },
      crossCompanyDisclosure: {
        title: "Cross-company regulatory risk",
        prompt:
          "Compare the antitrust exposure Apple and Alphabet disclose in their latest 10-Ks: which specific cases does each name, and whose revenue is more directly at risk?",
      },
    },
  },

  interruptedMarker: {
    label: "Interrupted",
  },

  regenerateButton: {
    label: "Regenerate",
    ariaLabel: "Regenerate response",
  },

  sources: {
    heading: "Sources",
  },

  chatPanel: {
    responseComplete: "Response complete",
  },
};

export type Copy = typeof en;

export const zhTW: Copy = {
  meta: {
    documentTitle: "FinLab-X — 美股研究 AI Agent",
  },

  activityIndicator: {
    thinking: "思考中",
    stalled: "仍在處理中",
  },

  reasoningChip: {
    thinkingLive: "思考中…",
    stalledLive: "仍在處理中…",
    thoughtFor: (seconds) => `思考了 ${seconds} 秒`,
    stoppedThoughtFor: (seconds) => `已停止 — 思考了 ${seconds} 秒`,
    toggleAriaLabel: (headerLabel, showBody) =>
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
    httpStatusFallback: (status) => `HTTP ${status}`,
  },

  toolStatus: {
    running: (toolName) => `執行 ${toolName} 中…`,
    completed: (toolName) => `${toolName} 已完成`,
    error: (toolName) => `${toolName} 發生錯誤`,
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
    tagline: "美股研究 AI Agent",
    clearConversation: "清除對話",
    clearConversationAriaLabel: "清除對話",
    languageGroupAriaLabel: "介面語言",
  },

  composer: {
    inputAriaLabel: "訊息輸入框",
    inputPlaceholder: "詢問美國上市公司的財報、申報文件或新聞…",
    stopAriaLabel: "停止回應",
    sendAriaLabel: "傳送訊息",
    disclaimer: "AI 生成的回覆可能不準確，重要資訊請自行查證。",
  },

  emptyState: {
    heading: "研究任何一檔美股",
    subtext: "AI 研究 Agent 會讀取 SEC 10-K 年報、即時市場資料與近期新聞，回答時附上引用來源。",
    everydayGroupLabel: "日常提問",
    analystGroupLabel: "深度分析",
    chips: {
      priceToday: {
        title: "今日股價表現",
        prompt: "Apple 今天的股價表現如何？背後有什麼相關新聞嗎？",
      },
      businessModel: {
        title: "這家公司靠什麼賺錢",
        prompt: "NVIDIA 主要在賣什麼？它大部分的營收來自哪裡？",
      },
      valuationCheck: {
        title: "現在買算貴嗎？",
        prompt: "Tesla 現在的股價算貴嗎？請用白話的方式解釋。",
      },
      riskVsNews: {
        title: "風險揭露 vs. 近期新聞",
        prompt:
          "NVIDIA 在最新 10-K 揭露的出口管制與中國相關風險中，哪些已經反映在近期新聞裡，哪些仍只是潛在風險？請逐項引用 10-K 與新聞來源。",
      },
      narrativeVsNumbers: {
        title: "經營團隊說法 vs. 實際數字",
        prompt:
          "Microsoft 將雲端業務成長歸功於 AI 需求。它的營收成長與毛利率趨勢是否支持這個說法？還是 AI 基礎建設支出正在侵蝕毛利率？",
      },
      crossCompanyDisclosure: {
        title: "跨公司法規風險比較",
        prompt:
          "比較 Apple 與 Alphabet 在最新 10-K 中揭露的反托拉斯風險：各自點名了哪些具體案件？哪一家的營收受到更直接的威脅？",
      },
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
};

export const copies: Record<Locale, Copy> = { en, "zh-TW": zhTW };
