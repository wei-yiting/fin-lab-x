import type { SSEStreamFixture } from "./types";

const fixture: SSEStreamFixture = {
  description: "Stream with delayed start (2s before first content)",
  scenarios: ["S-stop-04"],
  chunks: [
    { delayMs: 2000, data: { type: "start", messageId: "asst-slow" } },
    { data: { type: "text-start", id: "t1" } },
    { data: { type: "text-delta", id: "t1", delta: "Finally arrived!" } },
    { data: { type: "text-end", id: "t1" } },
    { data: { type: "finish" } },
  ],
};
export default fixture;
