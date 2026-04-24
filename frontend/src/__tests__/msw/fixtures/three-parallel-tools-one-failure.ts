import type { SSEStreamFixture } from "./types";

// Three tool calls kicked off together; one fails (tavily) while the other two
// succeed (yfinance_quote, yfinance_fields). Assistant still produces a final
// answer using the available data — tool failure must NOT kill the stream.
const fixture: SSEStreamFixture = {
  description:
    "3 parallel tools: 2 succeed, 1 emits tool-output-error; assistant completes using available data",
  scenarios: ["J-tool-01"],
  chunks: [
    { data: { type: "start", messageId: "asst-multi-tool" } },

    {
      data: {
        type: "tool-input-available",
        toolCallId: "tc-quote",
        toolName: "yfinance_stock_quote",
        input: { ticker: "NVDA" },
      },
    },
    {
      data: {
        type: "tool-input-available",
        toolCallId: "tc-fields",
        toolName: "yfinance_get_available_fields",
        input: {},
      },
    },
    {
      data: {
        type: "tool-input-available",
        toolCallId: "tc-search",
        toolName: "tavily_financial_search",
        input: { query: "NVDA earnings" },
      },
    },

    {
      delayMs: 80,
      data: {
        type: "tool-output-available",
        toolCallId: "tc-quote",
        output: { currentPrice: 202.5 },
      },
    },
    {
      delayMs: 40,
      data: {
        type: "tool-output-available",
        toolCallId: "tc-fields",
        output: { fields: ["price", "volume"] },
      },
    },
    {
      delayMs: 60,
      data: {
        type: "tool-output-error",
        toolCallId: "tc-search",
        errorText: "Tavily API timeout",
      },
    },

    { delayMs: 30, data: { type: "text-start", id: "t1" } },
    {
      data: {
        type: "text-delta",
        id: "t1",
        delta:
          "NVIDIA is trading at $202.50. News search was unavailable, but price data confirms the quote.",
      },
    },
    { data: { type: "text-end", id: "t1" } },

    { data: { type: "finish" } },
  ],
};

export default fixture;
