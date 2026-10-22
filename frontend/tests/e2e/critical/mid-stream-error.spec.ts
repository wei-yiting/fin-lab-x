import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test(
  "mid-stream error preserves partial text + surfaces non-retriable inline error",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("mid-stream-error-after-text");
    await chat.sendMessage("test");

    // Partially streamed text must remain visible after the error arrives
    const assistantMessage = page.getByTestId("assistant-message");
    await expect(assistantMessage).toContainText("NVDA Q2", {
      timeout: E2E_TIMEOUTS.streamComplete,
    });

    // Mid-stream errors render the inline variant (NOT the pre-stream block)
    await expect(page.getByTestId("inline-error-block")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(page.getByTestId("stream-error-block")).not.toBeVisible();

    // "context length exceeded" maps to a non-retriable friendly error
    await expect(page.getByTestId("error-title")).toContainText(/too long/i);
    await expect(page.getByTestId("error-retry-btn")).not.toBeVisible();

    // Partial text + already-extracted sources persist alongside the error
    await expect(assistantMessage).toContainText("NVDA Q2");
    await expect(page.getByTestId("sources-block")).toBeVisible();
  },
);
