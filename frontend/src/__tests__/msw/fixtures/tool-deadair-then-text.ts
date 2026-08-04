import type { SSEStreamFixture } from "./types";

const fixture: SSEStreamFixture = {
  description:
    "Tool round completes, then 2s dead air before the reply — placeholder window C (DEV-109 ruling)",
  scenarios: ["S-place-02"],
  chunks: [
    { data: { type: "start", messageId: "asst-deadair-1" } },
    { data: { type: "reasoning-start", id: "r1" } },
    { data: { type: "reasoning-delta", id: "r1", delta: "Need the latest quote first." } },
    { data: { type: "reasoning-end", id: "r1" } },
    {
      data: {
        type: "tool-input-available",
        toolCallId: "tc-quote",
        toolName: "yfinance_quote",
        input: { ticker: "AAPL" },
      },
    },
    {
      delayMs: 300,
      data: { type: "tool-output-available", toolCallId: "tc-quote", output: { price: 189.84 } },
    },
    // 2s of dead air: every tool part terminal, no next part yet — the
    // placeholder must appear after the 300ms grace and yield to the text.
    { delayMs: 2000, data: { type: "text-start", id: "t1" } },
    { data: { type: "text-delta", id: "t1", delta: "AAPL is currently trading at $189.84." } },
    { data: { type: "text-end", id: "t1" } },
    { data: { type: "finish" } },
  ],
};
export default fixture;
