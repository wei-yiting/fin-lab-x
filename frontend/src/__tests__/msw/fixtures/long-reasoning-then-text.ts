import type { SSEStreamFixture } from "./types";

const fixture: SSEStreamFixture = {
  description:
    "Native reasoning part streaming with a long mid-part hold — the chip stays streaming long enough for an abort (or a full run collapses it before text)",
  scenarios: [],
  chunks: [
    { data: { type: "start", messageId: "asst-reason" } },
    { data: { type: "reasoning-start", id: "reasoning-0" } },
    {
      data: {
        type: "reasoning-delta",
        id: "reasoning-0",
        delta: "Analyzing the 10-K filing structure and comparing risk factor sections",
      },
    },
    // Hold the chip in streaming state — abort tests Stop inside this window.
    { delayMs: 5000, data: { type: "reasoning-delta", id: "reasoning-0", delta: " in depth." } },
    { data: { type: "reasoning-end", id: "reasoning-0" } },
    { data: { type: "text-start", id: "t1" } },
    { data: { type: "text-delta", id: "t1", delta: "Here is the comparison." } },
    { data: { type: "text-end", id: "t1" } },
    { data: { type: "finish" } },
  ],
};
export default fixture;
