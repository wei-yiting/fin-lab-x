// Abort while a reasoning chip is streaming, then resend.
//
// Validates that:
// 1. Pressing Stop while a chip is streaming aborts cleanly: the half-chip
//    collapses to a "Stopped — thought for Xs" header, its text preserved.
// 2. Sending a fresh prompt runs a full clean turn — the aborted chip's
//    Stopped header persists on the prior bubble while the new turn streams
//    and collapses its own chip normally (no cross-turn contamination).
import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test(
  "stop during reasoning collapses to a Stopped half-chip, resend runs clean",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("long-reasoning-then-text");
    await chat.sendMessage("first prompt: long reasoning");

    const chip = page.getByTestId("reasoning-chip").first();
    await expect(chip).toHaveAttribute("data-state", "streaming", {
      timeout: E2E_TIMEOUTS.streamComplete,
    });

    // Abort while the chip is streaming. The composer-stop-btn is only
    // mounted while a stream is active.
    await page.getByTestId("composer-stop-btn").click();

    // Status flips back to ready; the half-chip collapses with the
    // abort-distinct header.
    await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
      timeout: E2E_TIMEOUTS.status,
    });
    await expect(chip).toHaveAttribute("data-state", "collapsed");
    await expect(chip.getByTestId("reasoning-chip-header")).toHaveText(
      /Stopped — thought for \d+s/,
    );

    // Resend — the new turn streams its own chip and completes.
    await chat.sendMessage("second prompt after abort");
    await chat.waitReady();

    // Both bubbles coexist; the prior Stopped chip is untouched; the new
    // chip collapsed to a clean header.
    await expect(page.getByTestId("assistant-message")).toHaveCount(2);
    await expect(
      page.getByTestId("reasoning-chip-header").filter({ hasText: /^Stopped/ }),
    ).toHaveCount(1);
    await expect(
      page.getByTestId("reasoning-chip-header").filter({ hasText: /^Thought for/ }),
    ).toHaveCount(1);
  },
);
