import { test, expect } from "../fixtures";

// S-life-03: after Clear, an immediate prompt-chip + Send in the same
// interaction window must carry the NEW chatId. React 18 automatic batching
// can coalesce `setChatId(new)` with composer-fill + submit into one render
// pass — if the outgoing POST captures state from before the chatId update,
// session isolation breaks (next turn still targets the pre-Clear chatId).
test(
  "Clear followed by immediate chip-send uses the post-Clear chatId in the POST body",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    // See regenerate-double-click.spec.ts for why this uses page.on("request")
    // rather than page.route.
    const postedChatIds: string[] = [];
    page.on("request", (req) => {
      if (req.method() !== "POST" || !req.url().includes("/api/v1/chat")) return;
      const body = req.postDataJSON() as { id?: string } | null;
      if (body?.id) postedChatIds.push(body.id);
    });

    await chat.gotoFixture("happy-text");
    await chat.sendMessage("first turn");
    await chat.waitReady();

    const chatPanel = page.getByTestId("chat-panel");
    const oldChatId = await chatPanel.getAttribute("data-chat-id");
    expect(oldChatId).toBeTruthy();
    expect(postedChatIds).toEqual([oldChatId]);

    // Clear → chip → Send in rapid succession. React's state batches are
    // per event-handler; each click flushes its own setState before the
    // next event fires. If a future refactor deferred the chatId update
    // (e.g. via effect) the Send POST below would leak the pre-Clear id —
    // that is the regression this guards against.
    await page.getByTestId("composer-clear-btn").click();
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await page.getByTestId("prompt-chip").and(page.locator('[data-chip-index="0"]')).click();
    await page.getByTestId("composer-send-btn").click();

    await chat.waitReady();

    // chatId must have rotated
    const newChatId = await chatPanel.getAttribute("data-chat-id");
    expect(newChatId).toBeTruthy();
    expect(newChatId).not.toBe(oldChatId);

    // The second POST must use the new chatId — never the pre-Clear one
    expect(postedChatIds).toHaveLength(2);
    expect(postedChatIds[1]).toBe(newChatId);
    expect(postedChatIds[1]).not.toBe(oldChatId);
  },
);
