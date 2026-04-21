import type { SSEStreamFixture } from "./types";

const fixture: SSEStreamFixture = {
  description: "Simple text-only stream response",
  scenarios: ["S-stream-01"],
  chunks: [
    { data: { type: "start", messageId: "asst-happy-1" } },
    { data: { type: "text-start", id: "t1" } },
    { data: { type: "text-delta", id: "t1", delta: "Hello! " } },
    { data: { type: "text-delta", id: "t1", delta: "This is a response." } },
    { data: { type: "text-end", id: "t1" } },
    { data: { type: "finish" } },
  ],
};
export default fixture;
