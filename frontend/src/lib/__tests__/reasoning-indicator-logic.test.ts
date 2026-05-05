import { describe, test, expect } from "vitest";
import {
  shouldShowReasoningIndicator,
  resolveReasoningDisplayText,
  IDLE_SYNTHESIZING_TEXT,
  IDLE_THINKING_TEXT,
} from "../reasoning-indicator-logic";

describe("shouldShowReasoningIndicator — truth table", () => {
  type Case = {
    name: string;
    status: "submitted" | "streaming" | "ready" | "error";
    lastMessage: { role: "user" | "assistant"; parts: Record<string, unknown>[] } | null;
    expected: boolean;
  };

  const cases: Case[] = [
    {
      name: "submitted, no last message → show",
      status: "submitted",
      lastMessage: null,
      expected: true,
    },
    {
      name: "submitted, last is user → show",
      status: "submitted",
      lastMessage: { role: "user", parts: [{ type: "text", text: "q" }] },
      expected: true,
    },
    {
      name: "streaming, last assistant has no rendered part → show",
      status: "streaming",
      lastMessage: { role: "assistant", parts: [] },
      expected: true,
    },
    {
      name: "streaming, last assistant has text part → hide",
      status: "streaming",
      lastMessage: { role: "assistant", parts: [{ type: "text", text: "hi" }] },
      expected: false,
    },
    {
      name: "streaming, last assistant has running tool part → hide",
      status: "streaming",
      lastMessage: {
        role: "assistant",
        parts: [{ type: "tool-search", state: "input-available", toolCallId: "tc1" }],
      },
      expected: false,
    },
    {
      name: "streaming, last assistant has only error part → hide (S-stream-07)",
      status: "streaming",
      lastMessage: {
        role: "assistant",
        parts: [{ type: "error", errorText: "oops" }],
      },
      expected: false,
    },
    {
      name: "ready, last assistant complete → hide (S-stream-08)",
      status: "ready",
      lastMessage: { role: "assistant", parts: [{ type: "text", text: "done" }] },
      expected: false,
    },
    {
      name: "error → hide",
      status: "error",
      lastMessage: null,
      expected: false,
    },
  ];

  test.each(cases)("$name", ({ status, lastMessage, expected }) => {
    expect(
      shouldShowReasoningIndicator({
        status,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
        lastMessage: lastMessage as any,
        reasoningStatusText: null,
      }),
    ).toBe(expected);
  });
});

describe("shouldShowReasoningIndicator — reasoningStatusText + post-tool gap branches", () => {
  test("reasoningStatusText overrides everything → true even with text part visible", () => {
    expect(
      shouldShowReasoningIndicator({
        status: "streaming",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
        lastMessage: { role: "assistant", parts: [{ type: "text", text: "hi" }] } as any,
        reasoningStatusText: "Thinking about prices...",
      }),
    ).toBe(true);
  });

  test("parts.length===0 + reasoningStatusText null → true", () => {
    expect(
      shouldShowReasoningIndicator({
        status: "streaming",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
        lastMessage: { role: "assistant", parts: [] } as any,
        reasoningStatusText: null,
      }),
    ).toBe(true);
  });

  test("post-tool gap: completed tool + status streaming + reasoningStatusText null → true", () => {
    expect(
      shouldShowReasoningIndicator({
        status: "streaming",
        lastMessage: {
          role: "assistant",
          parts: [
            { type: "tool-search", state: "output-available", toolCallId: "tc1" },
            // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
          ] as any,
        },
        reasoningStatusText: null,
      }),
    ).toBe(true);
  });

  test("post-tool gap: dynamic-tool completed + status streaming → true", () => {
    expect(
      shouldShowReasoningIndicator({
        status: "streaming",
        lastMessage: {
          role: "assistant",
          parts: [
            { type: "dynamic-tool", state: "output-available", toolCallId: "tc1" },
            // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
          ] as any,
        },
        reasoningStatusText: null,
      }),
    ).toBe(true);
  });

  test("completed tool + status ready → false (existing terminal rule)", () => {
    expect(
      shouldShowReasoningIndicator({
        status: "ready",
        lastMessage: {
          role: "assistant",
          parts: [
            { type: "tool-search", state: "output-available", toolCallId: "tc1" },
            // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
          ] as any,
        },
        reasoningStatusText: null,
      }),
    ).toBe(false);
  });

  test("last part text + status streaming + reasoningStatusText null → false", () => {
    expect(
      shouldShowReasoningIndicator({
        status: "streaming",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
        lastMessage: { role: "assistant", parts: [{ type: "text", text: "hi" }] } as any,
        reasoningStatusText: null,
      }),
    ).toBe(false);
  });
});

describe("resolveReasoningDisplayText", () => {
  test("reasoningStatusText truthy → passthrough", () => {
    expect(
      resolveReasoningDisplayText({
        reasoningStatusText: "thinking...",
        status: "streaming",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
        lastMessage: { role: "assistant", parts: [{ type: "text", text: "hi" }] } as any,
      }),
    ).toBe("thinking...");
  });

  test("reasoningStatusText null + streaming + completed tool last part → IDLE_SYNTHESIZING_TEXT", () => {
    expect(
      resolveReasoningDisplayText({
        reasoningStatusText: null,
        status: "streaming",
        lastMessage: {
          role: "assistant",
          parts: [
            { type: "tool-search", state: "output-available", toolCallId: "tc1" },
            // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
          ] as any,
        },
      }),
    ).toBe("Synthesizing");
  });

  test("reasoningStatusText null + streaming + last part is text → null (post-text gap)", () => {
    expect(
      resolveReasoningDisplayText({
        reasoningStatusText: null,
        status: "streaming",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
        lastMessage: { role: "assistant", parts: [{ type: "text", text: "hi" }] } as any,
      }),
    ).toBeNull();
  });

  test("reasoningStatusText null + status ready → null", () => {
    expect(
      resolveReasoningDisplayText({
        reasoningStatusText: null,
        status: "ready",
        lastMessage: {
          role: "assistant",
          parts: [
            { type: "tool-search", state: "output-available", toolCallId: "tc1" },
            // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
          ] as any,
        },
      }),
    ).toBeNull();
  });

  test("reasoningStatusText null + parts.length===0 → null (caller renders 3-dot)", () => {
    expect(
      resolveReasoningDisplayText({
        reasoningStatusText: null,
        status: "streaming",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
        lastMessage: { role: "assistant", parts: [] } as any,
      }),
    ).toBeNull();
  });

  test("reasoningStatusText null + lastMessage null → null", () => {
    expect(
      resolveReasoningDisplayText({
        reasoningStatusText: null,
        status: "streaming",
        lastMessage: null,
      }),
    ).toBeNull();
  });

  test("reasoningStatusText null + last part is running tool (input-available) → null", () => {
    expect(
      resolveReasoningDisplayText({
        reasoningStatusText: null,
        status: "streaming",
        lastMessage: {
          role: "assistant",
          parts: [
            { type: "tool-search", state: "input-available", toolCallId: "tc1" },
            // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test data uses loose types
          ] as any,
        },
      }),
    ).toBeNull();
  });

  test("idle text constants are exact English values per D16", () => {
    expect(IDLE_SYNTHESIZING_TEXT).toBe("Synthesizing");
    expect(IDLE_THINKING_TEXT).toBe("Thinking");
  });
});
