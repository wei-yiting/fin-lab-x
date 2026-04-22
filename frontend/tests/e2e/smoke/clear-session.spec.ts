import { test, expect } from "../fixtures";

test("J-clear-01 @smoke: clear session resets messages and chatId", async ({ chat, page }) => {
  await chat.gotoFixture("happy-text");
  await chat.sendMessage("first question");
  await chat.waitReady();

  const oldChatId = await page.getByTestId("chat-panel").getAttribute("data-chat-id");
  expect(oldChatId).toBeTruthy();

  await page.getByTestId("composer-clear-btn").click();

  await expect(page.getByTestId("empty-state")).toBeVisible();
  await expect(page.getByTestId("user-bubble")).toHaveCount(0);

  const newChatId = await page.getByTestId("chat-panel").getAttribute("data-chat-id");
  expect(newChatId).toBeTruthy();
  expect(newChatId).not.toBe(oldChatId);
});
