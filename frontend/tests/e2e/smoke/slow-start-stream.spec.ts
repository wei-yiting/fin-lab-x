import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test(
  "typing indicator persists during slow stream start, clears when content arrives",
  { tag: ["@smoke", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("slow-start-stream");
    await chat.sendMessage("test");

    // Fixture delays the first chunk by 2s — typing indicator must be visible
    // during that waiting period (not hidden prematurely)
    await expect(page.getByTestId("typing-indicator")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });

    // After content streams in, indicator is replaced by the assistant message
    await chat.waitReady();
    await expect(page.getByTestId("assistant-message")).toContainText("Finally arrived!");
    await expect(page.getByTestId("typing-indicator")).not.toBeVisible();
  },
);
