import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test(
  "stop preserves partial text and resets Composer",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("long-text-stream");

    await chat.sendMessage("write a long essay");

    const assistantMessage = page.getByTestId("assistant-message");
    await expect(assistantMessage).toBeVisible({ timeout: E2E_TIMEOUTS.streamComplete });
    // Wait until at least the first paragraph has streamed in before pressing stop,
    // so "stop preserves partial" has something partial to preserve.
    await expect(assistantMessage).toContainText("Paragraph 0.", {
      timeout: E2E_TIMEOUTS.streamComplete,
    });

    await page.getByTestId("composer-stop-btn").click();

    await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
      timeout: E2E_TIMEOUTS.status,
    });

    await expect(page.getByTestId("composer-send-btn")).toBeVisible();
    // The partially streamed text must still be present after stop
    await expect(assistantMessage).toContainText("Paragraph 0.");
  },
);
