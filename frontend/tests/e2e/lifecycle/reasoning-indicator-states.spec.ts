// SETUP: backend started without dev flags — natural Gemini reasoning stream
//   uv run uvicorn backend.api.main:app --reload
//
// Covers the visual state-sequence scenarios for the reasoning indicator:
// - S-rsn-01 idle dots → first reasoning text
// - S-rsn-02 streaming text appears in the indicator
// - S-rsn-03 indicator clears on text-start
// - S-rsn-04 indicator clears on tool-input-available
// - S-rsn-08 indicator clears on finish
//
// Each block asserts via DOM attribute / className the visual state, not
// implementation internals. Video recording is forced ON for this spec
// because the lifecycle review needs the recording regardless of pass/fail.
import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test.use({ video: "on" });

test(
  "S-rsn-01/02 — idle dots morph into streaming text in the reasoning indicator",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-text");
    await chat.sendMessage("explain SEC 10-K item 7 briefly");

    const indicator = page.getByTestId("reasoning-indicator");
    // Initial visible state — idle dots variant has aria-hidden + no text
    // content. Visibility is the load-bearing assertion.
    await expect(indicator).toBeVisible({ timeout: E2E_TIMEOUTS.streamComplete });

    // Eventually transitions to a frame containing streaming text.
    const reasoningText = indicator.locator(".reasoning-status-text");
    await expect(reasoningText).toBeVisible({ timeout: E2E_TIMEOUTS.streamComplete });
    await expect(reasoningText).not.toHaveText("", {
      timeout: E2E_TIMEOUTS.streamComplete,
    });
  },
);

test(
  "S-rsn-03 — reasoning indicator clears when assistant text-start arrives",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-text");
    await chat.sendMessage("hello");

    // Once the assistant message renders any text, the reasoning indicator
    // must no longer be visible.
    const assistantMessage = page.getByTestId("assistant-message");
    await expect(assistantMessage).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(page.getByTestId("reasoning-indicator")).not.toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
  },
);

test(
  "S-rsn-04 — reasoning indicator clears when tool-input-available arrives",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    // The tool-call fixture path emits tool-input-available before any text
    // streams; the indicator should clear at that boundary.
    await chat.gotoFixture("tool-call-then-text");
    await chat.sendMessage("look up MSFT quote");

    await expect(page.getByTestId("tool-card").first()).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(page.getByTestId("reasoning-indicator")).not.toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
  },
);

test(
  "S-rsn-08 — reasoning indicator clears when finish arrives",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-text");
    await chat.sendMessage("hello");

    await chat.waitReady();

    // After the stream finishes the indicator must be gone, and the
    // message-list status attribute reflects ready.
    await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
      timeout: E2E_TIMEOUTS.status,
    });
    await expect(page.getByTestId("reasoning-indicator")).not.toBeVisible();
  },
);
