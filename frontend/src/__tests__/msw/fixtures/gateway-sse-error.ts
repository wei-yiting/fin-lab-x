import type { SSEStreamFixture } from "./types";

const fixture: SSEStreamFixture = {
  description:
    "HTTP 200 text/event-stream, first frame after start is an error event (gateway cold-start / 504-wrapped-as-SSE pattern). Distinct from mid-stream-error which has content before the error.",
  scenarios: ["S-err-05"],
  chunks: [
    { data: { type: "start", messageId: "asst-gateway-err" } },
    { delayMs: 20, data: { type: "error", errorText: "upstream timeout" } },
  ],
};

export default fixture;
