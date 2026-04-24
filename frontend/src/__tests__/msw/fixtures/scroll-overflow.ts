import type { SSEStreamFixture } from "./types";

const chunks: SSEStreamFixture["chunks"] = [
  { data: { type: "start", messageId: "asst-scroll" } },
  { data: { type: "text-start", id: "t1" } },
];
for (let i = 0; i < 30; i++) {
  chunks.push({
    data: {
      type: "text-delta",
      id: "t1",
      delta: `Paragraph ${i + 1}. This is a moderately long paragraph designed to fill the viewport and force scrolling behavior in the chat panel during end-to-end testing. It contains enough text to wrap across multiple lines in a typical browser window width.\n\n`,
    },
  });
}
chunks.push({ data: { type: "text-end", id: "t1" } });
chunks.push({ data: { type: "finish" } });

const fixture: SSEStreamFixture = {
  description: "Text stream long enough to overflow viewport for scroll testing",
  scenarios: ["S-scroll-e2e-01", "S-scroll-e2e-02"],
  chunks,
};
export default fixture;
