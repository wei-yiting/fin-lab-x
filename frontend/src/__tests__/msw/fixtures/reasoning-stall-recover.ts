import type { SSEStreamFixture } from "./types";

/**
 * S-place-04 / S-place-05 edge case: a reasoning chip streams, then goes
 * silent for 11s (past the 10s STALL_THRESHOLD_MS) before a further delta
 * arrives and the turn completes normally. Used both to verify the
 * degraded "Still working…" copy + recovery (S-place-04), and that Stop
 * remains usable mid-stall with a clean abort (S-place-05).
 */
const fixture: SSEStreamFixture = {
  description:
    "Reasoning chip streaming, then 11s silent gap past the stall threshold, then recovery",
  scenarios: ["S-place-04", "S-place-05"],
  chunks: [
    { data: { type: "start", messageId: "asst-stall" } },
    { data: { type: "reasoning-start", id: "reasoning-0" } },
    {
      data: {
        type: "reasoning-delta",
        id: "reasoning-0",
        delta: "Analyzing the risk factor sections for material changes.",
      },
    },
    // Silent gap past STALL_THRESHOLD_MS (10s) — stall must trigger before this arrives.
    {
      delayMs: 11000,
      data: { type: "reasoning-delta", id: "reasoning-0", delta: " Continuing after the pause." },
    },
    { data: { type: "reasoning-end", id: "reasoning-0" } },
    { data: { type: "text-start", id: "t1" } },
    { data: { type: "text-delta", id: "t1", delta: "Here is the summary." } },
    { data: { type: "text-end", id: "t1" } },
    { data: { type: "finish" } },
  ],
};
export default fixture;
