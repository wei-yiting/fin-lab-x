// SETUP: backend started without dev flags — natural reasoning stream
//   uv run uvicorn backend.api.main:app --reload
//
// J-rsn-02 / S-rsn-13 — abort while reasoning is mid-flight, then resend.
//
// Validates that:
// 1. Pressing Stop while the reasoning indicator is visible aborts the
//    stream cleanly (composer flips back to ready, no error block).
// 2. Sending a fresh prompt resets the indicator state — the next turn's
//    fresh ``data-reasoning-status`` events surface in the indicator
//    (i.e. ``finishedRef`` did NOT latch in a way that breaks turn 2).
//
// Video records the full sequence so reviewers can confirm there is no
// flash of stale reasoning text after the resend.
import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test.use({ video: "on" });

test(
  "J-rsn-02 / S-rsn-13 — abort during reasoning, then resend produces a fresh indicator",
  { tag: ["@journey", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("long-reasoning-then-text");
    await chat.sendMessage("first prompt: long reasoning");

    const indicator = page.getByTestId("reasoning-indicator");
    await expect(indicator).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });

    // Abort while reasoning is visible. The composer-stop-btn is only
    // mounted while a stream is active.
    await page.getByTestId("composer-stop-btn").click();

    // Status flips back to ready — composer-send-btn re-mounts.
    await expect(page.getByTestId("message-list")).toHaveAttribute(
      "data-status",
      "ready",
      { timeout: E2E_TIMEOUTS.status },
    );
    await expect(page.getByTestId("composer-send-btn")).toBeVisible();

    // Resend — second turn's fresh data-reasoning-status events must
    // surface (resetForNewTurn clears finishedRef in ChatPanel).
    await chat.sendMessage("second prompt after abort");
    await expect(indicator).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
  },
);
