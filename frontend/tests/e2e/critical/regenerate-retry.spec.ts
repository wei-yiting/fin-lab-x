import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test(
  "regenerate failure → retry succeeds without duplicate history",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("regenerate-fail-then-success");

    // Step 1: send initial message → success
    await chat.sendMessage("Tell me about AAPL");
    await chat.waitReady();
    await expect(page.getByTestId("assistant-message")).toContainText("Original response.");

    // Step 2: click Regenerate → fails with 500
    await page.getByTestId("regenerate-btn").click();
    await expect(page.getByTestId("stream-error-block")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(page.getByTestId("error-title")).toContainText("Server error");

    // Step 3: click Retry → succeeds
    await page.getByTestId("error-retry-btn").click();
    await expect(page.getByTestId("stream-error-block")).not.toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await chat.waitReady();
    await expect(page.getByTestId("assistant-message")).toContainText("Retried response.");

    // Step 4: verify no duplicate history
    await expect(page.getByTestId("user-bubble")).toHaveCount(1);
  },
);
