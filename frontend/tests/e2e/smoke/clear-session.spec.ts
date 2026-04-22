import { test, expect } from "../fixtures";

test(
  "clear session resets messages and chatId",
  { tag: ["@smoke", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-text");
    await chat.sendMessage("first question");
    await chat.waitReady();

    const chatPanel = page.getByTestId("chat-panel");
    await expect(chatPanel).toHaveAttribute("data-chat-id", /.+/);
    const oldChatId = await chatPanel.getAttribute("data-chat-id");

    await page.getByTestId("composer-clear-btn").click();

    await expect(page.getByTestId("empty-state")).toBeVisible();
    await expect(page.getByTestId("user-bubble")).toHaveCount(0);

    await expect.poll(() => chatPanel.getAttribute("data-chat-id")).not.toBe(oldChatId);
  },
);
