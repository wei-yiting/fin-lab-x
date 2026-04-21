import type { SSEStreamFixture } from "./types";

const fixture: SSEStreamFixture = {
  description: "Text streams 2 chunks (with [1] ref and def) then error event arrives",
  scenarios: ["S-err-05", "S-err-08"],
  chunks: [
    { delayMs: 0, data: { type: "start", messageId: "asst-mock-1" } },
    { delayMs: 30, data: { type: "text-start", id: "t1" } },
    { delayMs: 80, data: { type: "text-delta", id: "t1", delta: "NVDA Q2 [1] beat estimates" } },
    { delayMs: 130, data: { type: "text-delta", id: "t1", delta: ", and per [2]" } },
    {
      delayMs: 180,
      data: {
        type: "text-delta",
        id: "t1",
        delta: '\n\n[1]: https://reuters.com/nvda-q2 "Reuters NVDA Q2"',
      },
    },
    { delayMs: 220, data: { type: "error", errorText: "context length exceeded" } },
  ],
};

export default fixture;
