import { test, expect } from "../fixtures";

test("J-regen-01 @smoke: regenerate replaces assistant response", async ({ chat, page }) => {
  await chat.gotoFixture("regenerate-happy");
  await chat.sendMessage("Tell me about MSFT");
  await chat.waitReady();
  await expect(page.getByTestId("assistant-message")).toContainText("Original response.");

  await page.getByTestId("regenerate-btn").click();
  await chat.waitReady();
  await expect(page.getByTestId("assistant-message")).toContainText("Regenerated response.");

  await expect(page.getByTestId("user-bubble")).toHaveCount(1);
});
