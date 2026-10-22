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
        title: "Risk disclosures vs. recent news",
        prompt:
          "Which export-control and supply-chain risks disclosed in NVIDIA's latest 10-K have actually materialized in recent news, and which remain only potential? Map each risk to the evidence and cite your sources.",
      },
      narrativeVsNumbers: {
        title: "Management narrative vs. the numbers",
        prompt:
          "How does Microsoft's latest 10-K MD&A explain the growth drivers of its cloud business? Test that narrative against current financial metrics such as revenue growth and gross margin. Does it hold up?",
      },
      crossCompanyDisclosure: {
        title: "Cross-company regulatory risk",
        prompt:
          "Compare how Apple's and Alphabet's latest 10-Ks disclose antitrust and regulatory risk. Which specific lawsuits or regulations does each company name, and which one describes the potential revenue impact more concretely?",
      },
      bearCaseAudit: {
        title: "Evidence-checked bear case",
        prompt:
          "Build a bear case for Tesla: find the strongest evidence from its latest 10-K risk factors, its current valuation metrics, and recent news. Then flag which common bear arguments lack supporting evidence.",
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
