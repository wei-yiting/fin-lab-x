import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test("S-cross-01 @critical: page refresh produces new chatId and clean state", async ({
  chat,
  page,
}) => {
  await chat.gotoFixture("happy-text");

  await chat.sendMessage("test");
  await chat.waitReady();

  const chatIdBefore = await page.getByTestId("chat-panel").getAttribute("data-chat-id");

  await page.reload();

  // Firefox + MSW service worker re-registration on reload needs a beat before app remounts;
  // wait for chat-panel to re-appear before asserting on its children.
  await expect(page.getByTestId("chat-panel")).toBeVisible({
    timeout: E2E_TIMEOUTS.streamComplete,
  });
  await expect(page.getByTestId("empty-state")).toBeVisible();
  await expect(page.getByTestId("user-bubble")).toHaveCount(0);

  const chatIdAfter = await page.getByTestId("chat-panel").getAttribute("data-chat-id");
  expect(chatIdAfter).not.toBe(chatIdBefore);
});
