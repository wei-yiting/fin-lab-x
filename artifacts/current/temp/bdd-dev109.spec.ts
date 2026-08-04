import { test, expect } from "../../../frontend/tests/e2e/fixtures";
import path from "node:path";

const CANONICAL_PROMPT =
  "Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)";

const SCREEN_DIR = path.join(__dirname, "screenshots");

test.describe.configure({ mode: "serial" });

test("S-chip-02: segment ends -> chip collapses to Thought for Xs, content readable, aria-live", async ({
  page,
}) => {
  test.setTimeout(300_000);
  await page.goto("/");
  await page.getByTestId("composer-textarea").fill(CANONICAL_PROMPT);
  await page.getByTestId("composer-send-btn").click();

  const chip = page.getByTestId("reasoning-chip").first();
  await expect(chip).toHaveAttribute("data-state", "streaming", { timeout: 30_000 });

  // Wait for it to collapse (segment ends).
  await expect(chip).toHaveAttribute("data-state", "collapsed", { timeout: 60_000 });
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-chip-02-collapsed.png") });

  const header = chip.getByTestId("reasoning-chip-header");
  await expect(header).toHaveAttribute("aria-live", "polite");
  const headerText = await header.innerText();
  expect(headerText).toMatch(/^Thought for \d+s$/);

  await header.click();
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-chip-02-expanded.png") });
  const body = chip.getByTestId("reasoning-chip-body");
  await expect(body).toBeVisible();
  const bodyText = await body.innerText();
  expect(bodyText.trim().length).toBeGreaterThan(0);

  // Let the turn finish before moving to next test to avoid session-busy 409.
  await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
    timeout: 240_000,
  });
});

test("S-chip-03: Thought for Xs excludes tool execution time (bracket assertion)", async ({ page }) => {
  test.setTimeout(180_000);
  await page.goto("/");
  await page.getByTestId("composer-textarea").fill(CANONICAL_PROMPT);

  // Timer semantics (ratified decision 2): the clock starts when the
  // reasoning PART appears (reasoning-start) and freezes at the round's
  // first tool-start. The DOM can only see the chip at its first delta,
  // which on GPT can lag reasoning-start by several seconds — so a
  // symmetric tolerance against (tool-card − chip-visible) flaps with
  // provider lag (observed diffs: 2.0 / 2.1 / 5.1s). Bracket instead:
  //   lower = t_tool − t_chip  (excludes the pre-delta lag)
  //   upper = t_tool − t_submit (includes it fully)
  // X must land in [lower − 2, upper + 2]; both bounds exclude tool
  // execution time, which is the scenario's actual claim.
  const tSubmit = Date.now();
  await page.getByTestId("composer-send-btn").click();

  const chip = page.getByTestId("reasoning-chip").first();
  await expect(chip).toHaveAttribute("data-state", "streaming", { timeout: 30_000 });
  const tChip = Date.now();

  const toolCard = page.getByTestId("tool-card").first();
  await expect(toolCard).toBeVisible({ timeout: 90_000 });
  const tTool = Date.now();

  await expect(chip).toHaveAttribute("data-state", "collapsed", { timeout: 15_000 });

  const header = chip.getByTestId("reasoning-chip-header");
  const headerText = await header.innerText();
  const match = headerText.match(/^Thought for (\d+)s$/);
  expect(match).not.toBeNull();
  const x = Number(match![1]);

  const lowerSec = (tTool - tChip) / 1000;
  const upperSec = (tTool - tSubmit) / 1000;

  console.log(
    JSON.stringify({
      scenario: "S-chip-03",
      lower_sec: lowerSec,
      upper_sec: upperSec,
      reported_X_sec: x,
    }),
  );

  expect(x).toBeGreaterThanOrEqual(lowerSec - 2);
  expect(x).toBeLessThanOrEqual(upperSec + 2);
});

test("S-chip-04: second reasoning segment start collapses previous chip (tail-only)", async ({ page }) => {
  test.setTimeout(240_000);
  await page.goto("/");
  await page.getByTestId("composer-textarea").fill(CANONICAL_PROMPT);
  await page.getByTestId("composer-send-btn").click();

  const chips = page.getByTestId("reasoning-chip");
  await expect(chips.nth(1)).toHaveAttribute("data-state", "streaming", { timeout: 90_000 });
  // At the moment chip2 starts streaming, chip1 must already be collapsed.
  await expect(chips.nth(0)).toHaveAttribute("data-state", "collapsed");
  const states = await chips.evaluateAll((els) => els.map((el) => el.getAttribute("data-state")));
  const streamingCount = states.filter((s) => s === "streaming").length;
  expect(streamingCount).toBeLessThanOrEqual(1);
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-chip-04-chip2-streaming.png") });

  await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
    timeout: 200_000,
  });
  const finalStates = await chips.evaluateAll((els) => els.map((el) => el.getAttribute("data-state")));
  for (const s of finalStates) expect(s).toBe("collapsed");
  expect(finalStates.length).toBeGreaterThanOrEqual(2);
});

test("S-chip-06 (MSW): zero-delta block suppressed, whitespace chip stays", async ({ chat, page }) => {
  await chat.gotoFixture("zero-delta-whitespace-reasoning");
  await chat.sendMessage("test");
  await chat.waitReady();

  const chips = page.getByTestId("reasoning-chip");
  await expect(chips).toHaveCount(1);
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-chip-06-final.png") });
});

test("S-chip-08: mid-stream abort collapses half chip with Stopped header", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await page.getByTestId("composer-textarea").fill(CANONICAL_PROMPT);
  await page.getByTestId("composer-send-btn").click();

  const chip = page.getByTestId("reasoning-chip").first();
  await expect(chip).toHaveAttribute("data-state", "streaming", { timeout: 30_000 });
  await expect
    .poll(async () => (await chip.getByTestId("reasoning-chip-body").innerText()).trim().length)
    .toBeGreaterThan(0);

  await page.getByTestId("composer-stop-btn").click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-chip-08-after-stop.png") });

  await expect(chip).toHaveAttribute("data-state", "collapsed");
  const header = chip.getByTestId("reasoning-chip-header");
  const headerText = await header.innerText();
  expect(headerText).toMatch(/^Stopped — thought for \d+s$/);

  await header.click();
  const bodyText = await chip.getByTestId("reasoning-chip-body").innerText();
  expect(bodyText.trim().length).toBeGreaterThan(0);
});

test("S-chip-09: reload mid-stream discards the in-flight turn entirely", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await page.getByTestId("composer-textarea").fill(CANONICAL_PROMPT);
  await page.getByTestId("composer-send-btn").click();

  await expect(page.getByTestId("message-list")).not.toHaveAttribute("data-status", "ready", {
    timeout: 15_000,
  });

  await page.reload();
  await page.waitForTimeout(500);

  await expect(page.getByTestId("reasoning-chip")).toHaveCount(0);
  await expect(page.getByTestId("assistant-message")).toHaveCount(0);
  await expect(page.getByTestId("activity-placeholder")).toHaveCount(0);
  const bodyText = await page.locator("body").innerText();
  expect(bodyText.toLowerCase()).not.toContain("error");
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-chip-09-after-reload.png") });
});

test("S-place-02 (post-ruling, MSW): placeholder appears in the tool-complete dead-air gap, yields to reply text", async ({
  chat,
  page,
}) => {
  // Deterministic window-C check (DEV-109 ruling 2026-08-04). The real-backend
  // sampling variant of this scenario was run twice (235 + 371 samples): the
  // negative invariants held throughout (placeholder never covered a streaming
  // chip or an executing tool card), but no dead-air gap occurred on the live
  // provider, so the positive half is pinned here with a fixture instead.
  test.setTimeout(30_000);
  await chat.gotoFixture("tool-deadair-then-text");
  await chat.sendMessage("test");

  // Tool completes at ~300ms, then 2s dead air before text-start.
  await expect(page.locator('[data-tool-state="output-available"]')).toBeVisible({
    timeout: 5_000,
  });
  const placeholder = page.getByTestId("activity-placeholder");
  // Placeholder must appear once the 300ms grace elapses inside the gap...
  await expect(placeholder).toBeVisible({ timeout: 1_500 });
  await expect(placeholder).toHaveAttribute("aria-live", "polite");
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-place-02-deadair-covered.png") });

  // ...and must yield once reply text arrives.
  await chat.waitReady();
  await expect(placeholder).toHaveCount(0);
});

test("S-place-04 (MSW): stall triggers degraded chip header copy, recovers on next part", async ({
  chat,
  page,
}) => {
  test.setTimeout(30_000);
  await chat.gotoFixture("reasoning-stall-recover");
  await chat.sendMessage("test");

  const chip = page.getByTestId("reasoning-chip").first();
  await expect(chip).toHaveAttribute("data-state", "streaming", { timeout: 5_000 });
  const header = chip.getByTestId("reasoning-chip-header");
  await expect(header).toHaveText("Thinking…");

  // Past the 10s stall threshold, before the 11s recovery delta arrives.
  await page.waitForTimeout(10_500);
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-place-04-stalled.png") });
  await expect(header).toHaveText("Still working…");

  // The 11s delta arrives shortly after — recovery: the degraded "Still
  // working…" copy must clear. The fixture's reasoning-end follows the
  // recovery delta immediately, so the chip may land on the still-streaming
  // "Thinking…" label or go straight to collapsed "Thought for Xs" — either
  // is a valid recovery, as long as it's no longer the stalled copy.
  await expect(header).not.toHaveText("Still working…", { timeout: 3_000 });
  const recoveredText = await header.innerText();
  expect(recoveredText === "Thinking…" || /^Thought for \d+s$/.test(recoveredText)).toBe(true);
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-place-04-recovered.png") });

  await chat.waitReady();
});

test("S-place-05 (MSW): Stop remains usable during a long silent stall", async ({ chat, page }) => {
  test.setTimeout(30_000);
  await chat.gotoFixture("reasoning-stall-recover");
  await chat.sendMessage("test");

  const chip = page.getByTestId("reasoning-chip").first();
  await expect(chip).toHaveAttribute("data-state", "streaming", { timeout: 5_000 });
  await page.waitForTimeout(10_500);
  const header = chip.getByTestId("reasoning-chip-header");
  await expect(header).toHaveText("Still working…");

  await expect(page.getByTestId("composer-stop-btn")).toBeVisible();
  await page.getByTestId("composer-stop-btn").click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(SCREEN_DIR, "s-place-05-after-stop.png") });

  await expect(chip).toHaveAttribute("data-state", "collapsed");
  const headerText = await header.innerText();
  expect(headerText).toMatch(/^Stopped — thought for \d+s$/);
  await expect(page.getByTestId("composer-stop-btn")).not.toBeVisible();
  await expect(page.getByTestId("composer-textarea")).toBeEnabled();
});

test("J-03: abort + recovery journey (UI half) — captures session_id for Langfuse readback", async ({
  page,
}) => {
  test.setTimeout(180_000);

  let sessionId: string | null = null;
  page.on("request", (req) => {
    if (req.url().includes("/api/v1/chat") && req.method() === "POST") {
      try {
        const body = req.postDataJSON() as { id?: string };
        if (body?.id) sessionId = body.id;
      } catch {
        /* ignore non-JSON */
      }
    }
  });

  await page.goto("/");
  await page.getByTestId("composer-textarea").fill(CANONICAL_PROMPT);
  await page.getByTestId("composer-send-btn").click();

  const chip = page.getByTestId("reasoning-chip").first();
  await expect(chip).toHaveAttribute("data-state", "streaming", { timeout: 30_000 });
  await expect
    .poll(async () => (await chip.getByTestId("reasoning-chip-body").innerText()).trim().length)
    .toBeGreaterThan(0);

  await page.getByTestId("composer-stop-btn").click();
  await page.waitForTimeout(1000);

  // S-chip-08 end state.
  await expect(chip).toHaveAttribute("data-state", "collapsed");
  const abortedHeaderText = await chip.getByTestId("reasoning-chip-header").innerText();
  expect(abortedHeaderText).toMatch(/^Stopped — thought for \d+s$/);
  await page.screenshot({ path: path.join(SCREEN_DIR, "j-03-after-stop.png") });

  // Resend a simple prompt on the same session; must complete normally end-to-end.
  await page.getByTestId("composer-textarea").fill("What does Item 1A cover?");
  await page.getByTestId("composer-send-btn").click();

  await expect(page.getByTestId("activity-placeholder")).toBeVisible({ timeout: 5_000 });
  await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
    timeout: 240_000,
  });
  const finalText = await page.getByTestId("assistant-message").last().innerText();
  expect(finalText.trim().length).toBeGreaterThan(0);
  await page.screenshot({ path: path.join(SCREEN_DIR, "j-03-resend-complete.png") });

  console.log(JSON.stringify({ scenario: "J-03", sessionId }));
  expect(sessionId).not.toBeNull();

  // Hand off to the Langfuse readback script via a file (cross-process handoff —
  // the SDK trace lookup runs from Python, not inside this Playwright process).
  const fs = await import("node:fs/promises");
  await fs.writeFile(path.join(__dirname, "j03_session_id.txt"), String(sessionId), "utf-8");
});
