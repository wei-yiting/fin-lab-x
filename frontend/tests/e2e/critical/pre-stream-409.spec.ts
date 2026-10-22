import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test(
  "pre-stream 409 surfaces retriable 'system busy' error",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("pre-stream-409");
    await chat.sendMessage("test");

    const errorBlock = page.getByTestId("stream-error-block");
    await expect(errorBlock).toBeVisible({ timeout: E2E_TIMEOUTS.streamComplete });

    // 409 maps to a retriable friendly error, so Retry button must be present
    await expect(page.getByTestId("error-title")).toContainText(/system is busy/i);
    await expect(page.getByTestId("error-retry-btn")).toBeVisible();

    // No assistant message renders (the request never even streamed)
    await expect(page.getByTestId("assistant-message")).not.toBeVisible();
  },
);
