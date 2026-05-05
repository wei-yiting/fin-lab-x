// SETUP: backend started with EMIT_DELAYED_REASONING dev flag set
//   EMIT_DELAYED_REASONING=1 uv run uvicorn backend.api.main:app --reload
//
// S-rsn-06 — stalled visual modifier.
//
// EMIT_DELAYED_REASONING releases ONE reasoning chunk for this mapper
// instance and drops the rest. The frontend's STALLED_THRESHOLD_MS poll
// (10s) flips ``stalled=true`` after the silence window expires; the
// wrapper class ``.reasoning-status.stalled`` is the visual contract.
//
// We wait 11s (threshold + 1s buffer) before asserting the class. Video
// recording captures the visual state for review.
import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test.use({ video: "on" });

const STALL_WAIT_MS = 11_000;

test(
  "S-rsn-06 — reasoning indicator gains .stalled class after STALLED_THRESHOLD_MS of silence",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-text");
    await chat.sendMessage("trigger delayed reasoning");

    const indicator = page.getByTestId("reasoning-indicator");
    await expect(indicator).toBeVisible({ timeout: E2E_TIMEOUTS.streamComplete });

    // Wait past the stalled threshold. We deliberately use page.waitForTimeout
    // here — there is no observable signal short of the className flip itself,
    // and we want the recording to show the natural transition.
    await page.waitForTimeout(STALL_WAIT_MS);

    await expect(indicator).toHaveClass(/(^|\s)stalled(\s|$)/, {
      timeout: 5_000,
    });
  },
);
