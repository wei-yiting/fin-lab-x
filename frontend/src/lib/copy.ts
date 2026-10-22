/**
 * Centralized UI Copy (see CONTEXT.md "UI Copy"). Grouped by domain concept,
 * not by component location. Excludes user-generated/model content and any
 * text that originates from the backend (HTTP error `detail`, SSE error
 * messages, sanitized tool errors) — those keep their original wording.
 */
export const copy = {
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
    chips: {
      riskVsNews: {
        title: "China risk: real or hype?",
        prompt:
          "Everyone says China export bans are NVIDIA's biggest risk. What does NVIDIA itself say in its latest 10-K, and has any of it actually shown up in the news yet, or is it still a what-if?",
      },
      narrativeVsNumbers: {
        title: "Is AI actually paying off?",
        prompt:
          "Microsoft keeps saying AI is driving Azure growth. Do the actual numbers back that up, or are margins quietly paying the price?",
      },
      crossCompanyDisclosure: {
        title: "Apple vs. Google antitrust",
        prompt:
          "Apple and Google are both fighting antitrust cases. Based on their own filings, which one has more revenue on the line if regulators win?",
      },
      bearCaseAudit: {
        title: "Tesla bear case: signal vs. noise",
        prompt:
          "Give me the bear case on Tesla at today's price. What's backed by the numbers and filings, and what's just noise?",
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
} as const;
