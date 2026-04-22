import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test(
  "pre-stream error recovery via Retry",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("pre-stream-500-then-success");

    await chat.sendMessage("test");

    await expect(page.getByTestId("stream-error-block")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(page.getByTestId("error-title")).toContainText("Server error");
    await expect(page.getByTestId("error-retry-btn")).toBeVisible();

    await expect(page.getByTestId("user-bubble")).toBeVisible();
    await expect(page.getByTestId("user-bubble")).toHaveCount(1);

    await page.getByTestId("error-retry-btn").click();

    await expect(page.getByTestId("stream-error-block")).not.toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });

    await chat.waitReady();

    await expect(page.getByTestId("user-bubble")).toHaveCount(1);

    await expect(page.getByTestId("assistant-message")).toBeVisible();
  },
);
