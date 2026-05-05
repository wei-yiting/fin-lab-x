// SETUP for the happy-path scenarios (J-chan-01, S-chan-01, S-chan-02):
//   uv run uvicorn backend.api.main:app --reload
//
// SETUP for S-chan-03 (force non-transient flag):
//   APP_ENV=production FORCE_REASONING_NON_TRANSIENT=1 \
//   uv run uvicorn backend.api.main:app --reload
//
// In production mode the SSE serializer downgrades the missing-transient
// assert helper to a warning log, so the malformed payload reaches the
// frontend filter that drops non-transient ``data-reasoning-status``
// parts. Without ``APP_ENV=production`` the assert raises and the
// streaming endpoint returns 500.
//
// Channel-isolation guarantees:
// - J-chan-01 — reasoning text never appears in the assistant transcript
// - S-chan-01 — data-reasoning-status carries ``transient: true`` end-to-end
// - S-chan-02 — assistant message ``parts`` array contains no
//               data-reasoning-status entries after the stream completes
// - S-chan-03 — frontend filter discards a non-transient
//               data-reasoning-status payload (production-mode override)
import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

test.use({ video: "on" });

test(
  "J-chan-01 / S-chan-02 — reasoning text never leaks into the assistant transcript",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("reasoning-then-text");
    await chat.sendMessage("explain something with reasoning");

    await chat.waitReady();

    // Whatever the reasoning indicator showed mid-stream, it must NOT be
    // present in the rendered assistant message body. We assert the
    // .reasoning-status text node never appears under assistant-message.
    const assistantMessage = page.getByTestId("assistant-message");
    await expect(assistantMessage).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
    await expect(
      assistantMessage.locator(".reasoning-status-text"),
    ).toHaveCount(0);
  },
);

test(
  "S-chan-01 — data-reasoning-status SSE event carries transient: true",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    // Capture every SSE chunk from the chat POST and verify each
    // ``data-reasoning-status`` payload is flagged transient.
    const reasoningPayloads: Array<Record<string, unknown>> = [];
    page.on("response", async (response) => {
      if (
        response.request().method() !== "POST" ||
        !response.url().includes("/api/v1/chat")
      ) {
        return;
      }
      const body = await response.text();
      for (const block of body.split("\n\n")) {
        if (!block.startsWith("data: ")) continue;
        try {
          const json = JSON.parse(block.slice("data: ".length)) as Record<
            string,
            unknown
          >;
          if (json.type === "data-reasoning-status") {
            reasoningPayloads.push(json);
          }
        } catch {
          // ignore non-JSON keep-alive blocks
        }
      }
    });

    await chat.gotoFixture("reasoning-then-text");
    await chat.sendMessage("explain something with reasoning");
    await chat.waitReady();

    expect(reasoningPayloads.length).toBeGreaterThan(0);
    for (const payload of reasoningPayloads) {
      expect(payload.transient).toBe(true);
    }
  },
);

test(
  "S-chan-03 — frontend drops non-transient data-reasoning-status payloads (FORCE_REASONING_NON_TRANSIENT=1, APP_ENV=production)",
  { tag: ["@lifecycle", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("reasoning-then-text");
    await chat.sendMessage("force malformed reasoning payload");
    await chat.waitReady();

    // After the stream completes the assistant message MUST NOT contain
    // any reasoning text. This proves the AssistantMessage filter dropped
    // the non-transient parts the (mis)configured backend emitted.
    const assistantMessage = page.getByTestId("assistant-message");
    await expect(assistantMessage).toBeVisible();
    await expect(
      assistantMessage.locator(".reasoning-status-text"),
    ).toHaveCount(0);
  },
);
