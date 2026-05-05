// SETUP: backend started with STUB_CONTENT_BLOCKS_NO_REASONING dev flag set
//   STUB_CONTENT_BLOCKS_NO_REASONING=gemini \
//   uv run uvicorn backend.api.main:app --reload
//
// S-trace-09 — simulates a regression where the LangChain v1
// content_blocks normalizer stops surfacing ``reasoning`` blocks for a
// given provider. The mapper filter drops every reasoning block before
// iteration — the resulting wire stream contains text and tool blocks
// only, with no ``data-reasoning-status`` events.
//
// The frontend must:
// 1. Never render the reasoning indicator (no events to drive it).
// 2. Still complete the stream with a normal assistant text body.
import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test.use({ video: "on" });

test(
  "S-trace-09 — content_blocks regression suppresses indicator but stream completes with text",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    let reasoningEventCount = 0;
    page.on("response", async (response) => {
      if (
        response.request().method() !== "POST" ||
        !response.url().includes("/api/v1/chat")
      ) {
        return;
      }
      const body = await response.text();
      for (const block of body.split("\n\n")) {
        if (!block.startsWith("data: ")) continue;
        try {
          const json = JSON.parse(block.slice("data: ".length)) as Record<
            string,
            unknown
          >;
          if (json.type === "data-reasoning-status") {
            reasoningEventCount += 1;
          }
        } catch {
          // ignore non-JSON keep-alive blocks
        }
      }
    });

    await chat.gotoFixture("happy-text");
    await chat.sendMessage("trigger no-reasoning regression");
    await chat.waitReady();

    // Assistant text must still render — only reasoning was dropped.
    await expect(page.getByTestId("assistant-message")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    // No reasoning indicator should ever surface for this turn.
    await expect(page.getByTestId("reasoning-indicator")).not.toBeVisible();
    expect(reasoningEventCount).toBe(0);
  },
);
