import type { SSEStreamFixture } from "./types";

const fixture: SSEStreamFixture = {
  description: "Markdown with duplicate [1] reference definitions — first-wins dedup test",
  scenarios: ["S-md-02"],
  chunks: [
    { delayMs: 0, data: { type: "start", messageId: "asst-dup-ref-1" } },
    { delayMs: 30, data: { type: "text-start", id: "t1" } },
    {
      delayMs: 80,
      data: {
        type: "text-delta",
        id: "t1",
        delta: "Analysis shows strong results [1] in the sector.\n\n",
      },
    },
    {
      delayMs: 130,
      data: {
        type: "text-delta",
        id: "t1",
        delta: '[1]: https://reuters.com/report-a "Reuters Report A"\n',
      },
    },
    {
      delayMs: 180,
      data: {
        type: "text-delta",
        id: "t1",
        delta: '[1]: https://bloomberg.com/report-b "Bloomberg Report B"\n',
      },
    },
    { delayMs: 230, data: { type: "text-end", id: "t1" } },
    { delayMs: 280, data: { type: "finish" } },
  ],
};

export default fixture;
