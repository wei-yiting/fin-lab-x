import type { SSEStreamFixture } from "./types";

/**
 * S-chip-06 edge case: a reasoning part that opens and closes without ever
 * carrying a delta (zero-delta suppression) followed by a reasoning part
 * whose only delta is whitespace (must still render + collapse normally).
 */
const fixture: SSEStreamFixture = {
  description:
    "Zero-delta reasoning block (no chip) followed by a whitespace-only-delta reasoning block (chip stays)",
  scenarios: ["S-chip-06"],
  chunks: [
    { data: { type: "start", messageId: "asst-zero-delta" } },
    { data: { type: "reasoning-start", id: "reasoning-empty" } },
    { delayMs: 30, data: { type: "reasoning-end", id: "reasoning-empty" } },
    { delayMs: 30, data: { type: "reasoning-start", id: "reasoning-ws" } },
    { delayMs: 30, data: { type: "reasoning-delta", id: "reasoning-ws", delta: "   " } },
    { delayMs: 30, data: { type: "reasoning-end", id: "reasoning-ws" } },
    { delayMs: 30, data: { type: "text-start", id: "t1" } },
    { delayMs: 30, data: { type: "text-delta", id: "t1", delta: "Done." } },
    { delayMs: 30, data: { type: "text-end", id: "t1" } },
    { delayMs: 30, data: { type: "finish" } },
  ],
};
export default fixture;
