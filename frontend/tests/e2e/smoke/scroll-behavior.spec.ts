import { test, expect } from "../fixtures";

const VIEWPORT = "message-list-viewport";

test("S-scroll-e2e-01 @smoke: overflowed content is scrollable", async ({ chat, page }) => {
  await chat.gotoFixture("scroll-overflow");
  await chat.sendMessage("Generate long content");
  await chat.waitReady();

  const viewport = page.getByTestId(VIEWPORT);

  const isScrollable = await viewport.evaluate((el) => el.scrollHeight > el.clientHeight);
  expect(isScrollable).toBe(true);

  const canScrollUp = await viewport.evaluate((el) => {
    el.scrollTop = 0;
    return el.scrollTop === 0 && el.scrollHeight > el.clientHeight;
  });
  expect(canScrollUp).toBe(true);
});

test("S-scroll-e2e-02 @smoke: sending new message auto-scrolls to bottom", async ({
  chat,
  page,
}) => {
  await chat.gotoFixture("scroll-overflow");
  await chat.sendMessage("First message");
  await chat.waitReady();

  const viewport = page.getByTestId(VIEWPORT);

  // Scroll up
  await viewport.evaluate((el) => {
    el.scrollTop = 0;
  });

  const notAtBottom = await viewport.evaluate(
    (el) => el.scrollHeight - el.scrollTop - el.clientHeight > 100,
  );
  expect(notAtBottom).toBe(true);

  // Send new message — should auto-scroll to bottom
  await chat.sendMessage("Second message");
  await chat.waitReady();

  const isAtBottom = await viewport.evaluate(
    (el) => el.scrollHeight - el.scrollTop - el.clientHeight < 100,
  );
  expect(isAtBottom).toBe(true);
});
