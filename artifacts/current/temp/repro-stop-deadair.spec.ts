import { test, expect } from "../../../frontend/tests/e2e/fixtures";
import path from "node:path";

const CANONICAL_PROMPT =
  "Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)";

const SCREEN_DIR = path.join(__dirname, "screenshots");

test("repro: Stop pressed during tool-complete dead air — screen must settle", async ({ page }) => {
  test.setTimeout(240_000);

  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => consoleErrors.push(`pageerror: ${err.message}`));

  await page.goto("/");
  await page.getByTestId("composer-textarea").fill(CANONICAL_PROMPT);
  await page.getByTestId("composer-send-btn").click();

  // Wait for the first tool card to complete (output-available).
  await expect(page.locator('[data-tool-state="output-available"]').first()).toBeVisible({
    timeout: 120_000,
  });

  // We are now at/near the dead-air window (tool done, next round pending).
  // Click Stop immediately.
  const stopBtn = page.getByTestId("composer-stop-btn");
  await stopBtn.click();
  await page.screenshot({ path: path.join(SCREEN_DIR, "repro-stop-deadair-t0.png") });

  // Observe for 8s: what does the UI settle to?
  const observations: Array<Record<string, unknown>> = [];
  for (let i = 0; i < 16; i++) {
    const status = await page.getByTestId("message-list").getAttribute("data-status");
    const stopVisible = await stopBtn.isVisible().catch(() => false);
    const sendBtnEnabled = await page
      .getByTestId("composer-send-btn")
      .isEnabled()
      .catch(() => false);
    const textareaEnabled = await page
      .getByTestId("composer-textarea")
      .isEnabled()
      .catch(() => false);
    const placeholderVisible = await page
      .getByTestId("activity-placeholder")
      .isVisible()
      .catch(() => false);
    observations.push({
      t_ms: i * 500,
      status,
      stopVisible,
      sendBtnEnabled,
      textareaEnabled,
      placeholderVisible,
    });
    await page.waitForTimeout(500);
  }
  await page.screenshot({ path: path.join(SCREEN_DIR, "repro-stop-deadair-t8s.png") });

  console.log(JSON.stringify({ observations, consoleErrors }, null, 2));

  // Settlement contract (S-pres-02): shortly after Stop the status leaves the
  // active pair, no placeholder remains, and the composer accepts a resend.
  const settled = observations.at(-1)!;
  expect(settled.status).toBe("ready");
  expect(settled.stopVisible).toBe(false);
  expect(settled.placeholderVisible).toBe(false);
  expect(settled.textareaEnabled).toBe(true);

  // DEV-109 ruling 11: every user Stop leaves an explicit "Interrupted" row.
  await expect(page.getByTestId("interrupted-marker")).toBeVisible();

  // Resend must work.
  await page.getByTestId("composer-textarea").fill("What does Item 1A cover?");
  await page.getByTestId("composer-send-btn").click();
  await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
    timeout: 240_000,
  });
});
