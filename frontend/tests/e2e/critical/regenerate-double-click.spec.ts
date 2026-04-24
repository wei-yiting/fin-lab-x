import { test, expect } from "../fixtures";

// S-regen-02: rapid double-click on Regenerate must not produce a second
// POST. Component-level coverage (button hidden once status leaves "ready")
// lives in AssistantMessage.test.tsx; this E2E closes the race window that
// only a real browser can exercise — two clicks dispatched before React
// re-renders and unmounts the button.
test(
  "double-click on Regenerate dispatches a single regenerate POST",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    // MSW's Service Worker handles the response, but the browser still
    // emits a `request` event before SW intercept — use `page.on("request")`,
    // not `page.route` (which only fires for outbound-to-network requests).
    const regenerateRequests: string[] = [];
    page.on("request", (req) => {
      if (req.method() !== "POST" || !req.url().includes("/api/v1/chat")) return;
      const body = req.postDataJSON() as { trigger?: string; messageId?: string } | null;
      if (body?.trigger === "regenerate-message") {
        regenerateRequests.push(body.messageId ?? "");
      }
    });

    await chat.gotoFixture("regenerate-happy");
    await chat.sendMessage("first question");
    await chat.waitReady();

    // Fire two clicks within the same microtask queue before yielding to React
    await page.evaluate(() => {
      const btn = document.querySelector<HTMLButtonElement>('[data-testid="regenerate-btn"]');
      btn?.click();
      btn?.click();
    });

    await chat.waitReady();

    // Exactly one regenerate POST was dispatched
    expect(regenerateRequests).toHaveLength(1);
  },
);
