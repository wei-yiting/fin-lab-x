import { test, expect } from "../fixtures";

const VIEWPORT = "message-list-viewport";

test(
  "overflowed content is scrollable",
  { tag: ["@smoke", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("scroll-overflow");
    await chat.sendMessage("Generate long content");
    await chat.waitReady();

    const viewport = page.getByTestId(VIEWPORT);

    // Content overflows the viewport
    await expect
      .poll(() => viewport.evaluate((el) => el.scrollHeight > el.clientHeight))
      .toBe(true);

    // Programmatic scrollTop assignment succeeds (container is actually scrollable)
    await viewport.evaluate((el) => {
      el.scrollTop = 0;
    });
    await expect.poll(() => viewport.evaluate((el) => el.scrollTop)).toBe(0);
  },
);

test(
  "sending new message auto-scrolls to bottom",
  { tag: ["@smoke", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("scroll-overflow");
    await chat.sendMessage("First message");
    await chat.waitReady();

    const viewport = page.getByTestId(VIEWPORT);

    // User scrolls up — data-at-bottom flips to false
    await viewport.evaluate((el) => {
      el.scrollTop = 0;
    });
    await expect(viewport).toHaveAttribute("data-at-bottom", "false");

    // Sending a new message auto-scrolls — data-at-bottom flips back to true
    await chat.sendMessage("Second message");
    await chat.waitReady();
    await expect(viewport).toHaveAttribute("data-at-bottom", "true");
  },
);
