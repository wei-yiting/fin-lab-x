import type { SSEStreamFixture } from "./types";

const fixture: SSEStreamFixture = {
  description: "Text stream with CommonMark reference definition citations",
  scenarios: ["S-md-01", "TC-e2e-citation-01"],
  chunks: [
    { data: { type: "start", messageId: "asst-cite-1" } },
    { data: { type: "text-start", id: "t1" } },
    {
      data: {
        type: "text-delta",
        id: "t1",
        delta: "Analysis shows strong growth [1] in the technology sector. ",
      },
    },
    {
      data: { type: "text-delta", id: "t1", delta: "Bloomberg reports [2] confirm the trend.\n\n" },
    },
    {
      data: {
        type: "text-delta",
        id: "t1",
        delta: '[1]: https://reuters.com/tech-report "Reuters Tech Report"\n',
      },
    },
    {
      data: {
        type: "text-delta",
        id: "t1",
        delta: '[2]: https://bloomberg.com/analysis "Bloomberg Analysis"\n',
      },
    },
    { data: { type: "text-end", id: "t1" } },
    { data: { type: "finish" } },
  ],
};
export default fixture;
