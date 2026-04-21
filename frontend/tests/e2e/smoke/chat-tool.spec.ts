import { test, expect } from "@playwright/test";

test("J-stream-02 @smoke: tool + text streaming completes successfully", async ({ page }) => {
  await page.goto("/?msw_fixture=happy-tool-then-text");

  await page.getByTestId("composer-textarea").fill("What is AAPL price?");
  await page.getByTestId("composer-send-btn").click();

  await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
    timeout: 10000,
  });

  await expect(page.locator('[data-tool-state="output-available"]')).toBeVisible();

  await expect(page.getByTestId("composer-send-btn")).toBeVisible();
});
