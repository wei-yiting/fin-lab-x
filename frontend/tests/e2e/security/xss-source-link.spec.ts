import { test, expect } from "../fixtures";

// Sanitization detail (javascript: stripped, mailto preserved, rel attrs on https
// links) is covered by Markdown RTL. This E2E verifies only the end-to-end
// security invariant that cannot be asserted in jsdom: in a real browser, no
// `javascript:` anchor is rendered and no `dialog` event fires when the page
// is loaded with a hostile fixture.
async function assertNoXss(
  chat: {
    gotoFixture: (n: string) => Promise<void>;
    sendMessage: (t: string) => Promise<void>;
    waitReady: () => Promise<void>;
  },
  page: import("@playwright/test").Page,
  fixture: string,
) {
  let dialogTriggered = false;
  page.on("dialog", async (dialog) => {
    dialogTriggered = true;
    await dialog.dismiss();
  });

  await chat.gotoFixture(fixture);
  await chat.sendMessage("test");
  await chat.waitReady();

  await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0);
  expect(dialogTriggered).toBe(false);
}

test(
  "inline javascript: URL is sanitized end-to-end",
  { tag: ["@security", "@regression"] },
  async ({ chat, page }) => {
    await assertNoXss(chat, page, "xss-inline-body-link");
  },
);

test(
  "source-reference javascript: URL is sanitized end-to-end",
  { tag: ["@security", "@regression"] },
  async ({ chat, page }) => {
    await assertNoXss(chat, page, "xss-javascript-url");
  },
);
