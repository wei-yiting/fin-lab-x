import type { SequentialFixture, SSEStreamFixture } from "./types";

const initialResponse: SSEStreamFixture = {
  description: "Initial assistant response",
  scenarios: [],
  chunks: [
    { data: { type: "start", messageId: "asst-initial-1" } },
    { data: { type: "text-start", id: "t1" } },
    { data: { type: "text-delta", id: "t1", delta: "Original response." } },
    { data: { type: "text-end", id: "t1" } },
    { data: { type: "finish" } },
  ],
};

const regeneratedResponse: SSEStreamFixture = {
  description: "Regenerated assistant response",
  scenarios: [],
  chunks: [
    { data: { type: "start", messageId: "asst-regen-1" } },
    { data: { type: "text-start", id: "t2" } },
    { data: { type: "text-delta", id: "t2", delta: "Regenerated response." } },
    { data: { type: "text-end", id: "t2" } },
    { data: { type: "finish" } },
  ],
};

const fixture: SequentialFixture = {
  description: "First request returns initial response, second (regenerate) returns different text",
  scenarios: ["J-regen-01"],
  responses: [initialResponse, regeneratedResponse],
};
export default fixture;
