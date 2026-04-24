import { test as base, expect, type Page } from "@playwright/test";
import { E2E_TIMEOUTS } from "./constants";

type ChatFixture = {
  gotoFixture: (name: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  waitReady: () => Promise<void>;
};

export const test = base.extend<{ chat: ChatFixture }>({
  chat: async ({ page }: { page: Page }, use) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks -- Playwright fixture API; `use` here is the yielder, not a React hook
    await use({
      gotoFixture: async (name: string) => {
        await page.goto(`/?msw_fixture=${name}`);
      },
      sendMessage: async (text: string) => {
        await page.getByTestId("composer-textarea").fill(text);
        await page.getByTestId("composer-send-btn").click();
      },
      waitReady: () =>
        expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
          timeout: E2E_TIMEOUTS.streamComplete,
        }),
    });
  },
});

export { expect } from "@playwright/test";
