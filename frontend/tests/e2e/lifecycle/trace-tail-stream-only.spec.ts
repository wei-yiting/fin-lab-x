// SETUP: backend started with STUB_REASONING_ONLY dev flag set
//   STUB_REASONING_ONLY=1 uv run uvicorn backend.api.main:app --reload
//
// S-trace-05 — reasoning-only stream still emits trace tail.
//
// STUB_REASONING_ONLY drops text + tool_call_chunk blocks from the
// content_blocks iteration in StreamEventMapper. The wire stream is
// therefore reasoning-only: the indicator surfaces, then the stream
// finishes without any assistant text. The reasoning trace must still
// be written to Langfuse via the segmenter flush at finalize() — the
// Playwright spec asserts the visual contract; the trace assertion
// itself is exercised by the Python side under tests/streaming.
import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test.use({ video: "on" });

test(
  "S-trace-05 — reasoning-only stream surfaces indicator then finishes with no assistant text",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-text");
    await chat.sendMessage("trigger reasoning-only stub");

    // Reasoning indicator must surface during the stream.
    await expect(page.getByTestId("reasoning-indicator")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });

    await chat.waitReady();
    await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
      timeout: E2E_TIMEOUTS.status,
    });

    // After finish there must be no rendered assistant text body. The
    // assistant-message wrapper may exist with empty content depending on
    // ChatPanel rendering; assert the text-content slot is empty.
    const assistantMessage = page.getByTestId("assistant-message");
    if (await assistantMessage.count()) {
      await expect(assistantMessage).not.toContainText(/\w/);
    }
  },
);
