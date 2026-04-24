import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

// J-tool-01: three tools run in parallel, one fails. The failed tool's card
// must render in output-error state while the other two land in output-available,
// and the assistant completes its reply using the available data — a single
// tool failure must not kill the whole stream.
test(
  "three parallel tools with one failure produce three correctly-attributed cards and a completed reply",
  { tag: ["@critical", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("three-parallel-tools-one-failure");
    await chat.sendMessage("Give me NVDA context");

    // All three cards resolve to terminal states (success or error)
    const quoteCard = page.locator('[data-testid="tool-card"][data-tool-call-id="tc-quote"]');
    const fieldsCard = page.locator('[data-testid="tool-card"][data-tool-call-id="tc-fields"]');
    const searchCard = page.locator('[data-testid="tool-card"][data-tool-call-id="tc-search"]');

    await expect(quoteCard).toHaveAttribute("data-tool-state", "output-available", {
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(fieldsCard).toHaveAttribute("data-tool-state", "output-available", {
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(searchCard).toHaveAttribute("data-tool-state", "output-error", {
      timeout: E2E_TIMEOUTS.streamComplete,
    });

    // No cross-attribution — exactly 3 tool cards are rendered
    await expect(page.getByTestId("tool-card")).toHaveCount(3);

    // Stream completed (finish received, no lingering error block)
    await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(page.getByTestId("inline-error-block")).not.toBeVisible();

    // Assistant used the available data to compose a reply
    await expect(page.getByTestId("assistant-message")).toContainText(/NVIDIA/);
  },
);
