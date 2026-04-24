import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test(
  "page refresh produces new chatId and clean state",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-text");

    await chat.sendMessage("test");
    await chat.waitReady();

    const chatPanel = page.getByTestId("chat-panel");
    const chatIdBefore = await chatPanel.getAttribute("data-chat-id");
    expect(chatIdBefore).toMatch(/.+/);

    // Firefox-specific: clear the MSW service worker before reload to avoid a
    // stale-controller handshake where `worker.start()` never resolves on the
    // fresh page. Chromium doesn't need this but it's harmless there.
    await page.evaluate(async () => {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map((r) => r.unregister()));
    });

    await page.reload();

    // Firefox + MSW service worker re-registration on reload needs a beat before app remounts;
    // wait for chat-panel to re-appear before asserting on its children.
    await expect(chatPanel).toBeVisible({ timeout: E2E_TIMEOUTS.streamComplete });
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await expect(page.getByTestId("user-bubble")).toHaveCount(0);

    await expect.poll(() => chatPanel.getAttribute("data-chat-id")).not.toBe(chatIdBefore);
  },
);
