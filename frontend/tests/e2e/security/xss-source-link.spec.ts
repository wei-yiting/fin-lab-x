import { test, expect } from "../fixtures";

test(
  "inline body links with javascript: URL are sanitized",
  { tag: ["@security", "@regression"] },
  async ({ chat, page }) => {
    let dialogTriggered = false;
    page.on("dialog", async (dialog) => {
      dialogTriggered = true;
      await dialog.dismiss();
    });

    await chat.gotoFixture("xss-inline-body-link");
    await chat.sendMessage("show me inline links");
    await chat.waitReady();

    // Anchor queries scoped to assistant-message body; sources-block is separate.
    const assistantBody = page.getByTestId("assistant-message");
    const bodyAnchors = assistantBody.locator("a").filter({
      hasNot: page.getByTestId("sources-block").locator("a"),
    });

    // No javascript: URL allowed anywhere in body
    const jsAnchors = assistantBody.locator('a[href^="javascript:"]');
    await expect(jsAnchors).toHaveCount(0);

    // Safe https link renders with secure attributes
    const safeAnchor = bodyAnchors.filter({ hasText: "safe" }).first();
    await expect(safeAnchor).toHaveAttribute("href", "https://example.com");
    await expect(safeAnchor).toHaveAttribute("target", "_blank");
    await expect(safeAnchor).toHaveAttribute("rel", /noopener/);
    await expect(safeAnchor).toHaveAttribute("rel", /noreferrer/);

    // mailto: is allowed by react-markdown's defaultUrlTransform — the sanitizer
    // strips javascript: only. Assert the mailto link is kept as-is.
    const mailAnchor = bodyAnchors.filter({ hasText: "mail link" }).first();
    await expect(mailAnchor).toHaveAttribute("href", "mailto:x@y.com");

    expect(dialogTriggered).toBe(false);
  },
);

test(
  "javascript: URL in source reference is sanitized",
  { tag: ["@security", "@regression"] },
  async ({ chat, page }) => {
    let dialogTriggered = false;
    page.on("dialog", async (dialog) => {
      dialogTriggered = true;
      await dialog.dismiss();
    });

    await chat.gotoFixture("xss-javascript-url");
    await chat.sendMessage("show me sources");
    await chat.waitReady();

    const xssAnchors = page.locator('a[href^="javascript:"]');
    await expect(xssAnchors).toHaveCount(0);

    const mailtoAnchors = page.locator('a[href^="mailto:"]');
    await expect(mailtoAnchors).toHaveCount(0);

    expect(dialogTriggered).toBe(false);
  },
);
