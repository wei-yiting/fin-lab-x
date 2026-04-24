import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

// S-err-05: HTTP 200 + content-type text/event-stream, but the first frame after
// the protocol-required `start` is an error event (common on Cloudflare/Render
// cold starts). ChatPanel classifies by whether the last assistant message has
// any parts — with zero parts between `start` and `error` this surfaces as the
// stream-error-block variant (same block family as pre-stream HTTP errors),
// not inline-error-block. Retry must be available when errorText is retriable.
test(
  "gateway SSE error (200 + immediate error frame) renders ErrorBlock with Retry",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("gateway-sse-error");
    await chat.sendMessage("anything");

    // ErrorBlock renders (stream-error-block variant — zero-parts case)
    await expect(page.getByTestId("stream-error-block")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(page.getByTestId("inline-error-block")).not.toBeVisible();

    // Error title is populated (copy specifics covered by error-messages unit tests)
    await expect(page.getByTestId("error-title")).not.toBeEmpty();

    // Retry is available — gateway timeout is retriable
    await expect(page.getByTestId("error-retry-btn")).toBeVisible();

    // Stream didn't hang — status is off "streaming"
    const status = page.getByTestId("message-list");
    await expect(status).not.toHaveAttribute("data-status", "streaming", {
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(status).not.toHaveAttribute("data-status", "submitted");
  },
);
