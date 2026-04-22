import { test, expect } from "../fixtures";

test("S-md-03-inline @security: inline body links with javascript: URL are sanitized", async ({
  chat,
  page,
}) => {
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
  const safeRel = await safeAnchor.getAttribute("rel");
  expect(safeRel).toContain("noopener");
  expect(safeRel).toContain("noreferrer");

  // mailto: documented behavior: react-markdown's defaultUrlTransform allows mailto.
  // Either rendered as mailto href OR stripped — both are acceptable. This assertion
  // merely documents current behavior (never throws).
  const mailAnchor = bodyAnchors.filter({ hasText: "mail link" }).first();
  const mailCount = await mailAnchor.count();
  if (mailCount > 0) {
    const mailHref = await mailAnchor.getAttribute("href");
    // If present, must be mailto: (allowed) or a relative/fallback href — never javascript:
    expect(mailHref ?? "").not.toMatch(/^javascript:/i);
  }

  expect(dialogTriggered).toBe(false);
});

test("S-md-03 @security: javascript: URL is sanitized", async ({ chat, page }) => {
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
});
