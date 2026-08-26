import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test(
  "placeholder fills the submit dead-air, then yields to the streamed answer",
  { tag: ["@smoke", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("slow-start-stream");
    await chat.sendMessage("test");

    // Fixture delays the first chunk by 2s — the activity placeholder must
    // cover the submitted dead-air window.
    await expect(page.getByTestId("activity-placeholder")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(page.getByTestId("activity-placeholder")).toHaveText("思考中");

    // After content streams in, the placeholder yields to the answer.
    await chat.waitReady();
    await expect(page.getByTestId("assistant-message")).toContainText("Finally arrived!");
    await expect(page.getByTestId("activity-placeholder")).not.toBeVisible();
  },
);
