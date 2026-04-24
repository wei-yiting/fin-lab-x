import type { SSEStreamFixture } from "./types";

const fixture: SSEStreamFixture = {
  description: "Tool call completes then text follows",
  scenarios: ["J-stream-02", "S-tool-01"],
  chunks: [
    { data: { type: "start", messageId: "asst-tool-1" } },
    {
      data: {
        type: "tool-input-available",
        toolCallId: "tc-quote",
        toolName: "yfinance_quote",
        input: { ticker: "AAPL" },
      },
    },
    {
      delayMs: 100,
      data: { type: "tool-output-available", toolCallId: "tc-quote", output: { price: 189.84 } },
    },
    { data: { type: "text-start", id: "t1" } },
    { data: { type: "text-delta", id: "t1", delta: "AAPL is currently trading at $189.84." } },
    { data: { type: "text-end", id: "t1" } },
    { data: { type: "finish" } },
  ],
};
export default fixture;
