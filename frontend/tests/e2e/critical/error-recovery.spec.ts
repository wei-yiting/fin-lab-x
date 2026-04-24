import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

// Hook-level invariants (no user-bubble duplication, error-title text matching,
// status transitions) are covered by ChatPanel integration RTL. This E2E
// verifies only what the real browser can: error UI surfaces + retry completes
// the flow end-to-end.
test(
  "pre-stream error recovery via Retry",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("pre-stream-500-then-success");

    await chat.sendMessage("test");

    // 1. Error UI surfaces
    await expect(page.getByTestId("stream-error-block")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(page.getByTestId("error-retry-btn")).toBeVisible();

    // 2. Retry click actually recovers
    await page.getByTestId("error-retry-btn").click();

    // 3. Stream completes after retry
    await chat.waitReady();
    await expect(page.getByTestId("stream-error-block")).not.toBeVisible();
    await expect(page.getByTestId("assistant-message")).toBeVisible();
  },
);
