// SETUP: backend started with EMIT_LATE_REASONING dev flag set
//   EMIT_LATE_REASONING=1 uv run uvicorn backend.api.main:app --reload
//
// S-rsn-12 — post-finish reasoning event must be dropped by the frontend.
//
// The mapper injects a synthetic ReasoningStatus AFTER Finish. The
// frontend's ``finishedRef`` (latched on the SSE ``finish`` event) makes
// useReasoningStatus.handleData short-circuit — the indicator stays
// cleared even though the wire delivered a late ``data-reasoning-status``
// payload. Video records the no-op for review.
import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test.use({ video: "on" });

test(
  "S-rsn-12 — late reasoning event after finish does not re-show the indicator",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-text");
    await chat.sendMessage("hello");

    await chat.waitReady();
    await expect(page.getByTestId("message-list")).toHaveAttribute(
      "data-status",
      "ready",
      { timeout: E2E_TIMEOUTS.status },
    );

    // Hold for a beat so any late SSE frame the backend sent post-finish has
    // had a chance to land. The finishedRef guard should keep the indicator
    // hidden regardless.
    await page.waitForTimeout(1_500);

    await expect(page.getByTestId("reasoning-indicator")).not.toBeVisible();
  },
);
