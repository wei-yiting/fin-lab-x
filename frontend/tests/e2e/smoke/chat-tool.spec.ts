import { test, expect } from "../fixtures";

test(
  "tool + text streaming completes successfully",
  { tag: ["@smoke", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-tool-then-text");
    await chat.sendMessage("What is AAPL price?");
    await chat.waitReady();

    await expect(page.locator('[data-tool-state="output-available"]')).toBeVisible();
    await expect(page.getByTestId("composer-send-btn")).toBeVisible();
  },
);
