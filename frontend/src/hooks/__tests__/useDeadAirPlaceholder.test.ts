import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDeadAirPlaceholder } from "../useDeadAirPlaceholder";
import { PLACEHOLDER_GRACE_MS } from "@/lib/timing";

function assistantMsg(id: string, parts: Array<Record<string, unknown>>) {
  return { id, role: "assistant", parts };
}
const userMsg = { id: "u1", role: "user", parts: [{ type: "text", text: "q" }] };

describe("useDeadAirPlaceholder — dead-air windows (C1 + decision 5)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  test("window (a): visible while status === 'submitted' (D17 4-value status)", () => {
    const { result } = renderHook(() => useDeadAirPlaceholder([userMsg], "submitted"));
    expect(result.current).toBe("waiting");
  });

  test("window (a): stays visible after the `start` frame flips status to streaming", () => {
    // The assistant message may not exist yet, exist with no parts, or hold
    // only not-yet-renderable parts (reasoning-start before its first delta,
    // step boundaries) — all still dead air, no grace delay.
    const preContentShapes = [
      [userMsg],
      [userMsg, assistantMsg("a1", [])],
      [userMsg, assistantMsg("a1", [{ type: "step-start" }])],
      [userMsg, assistantMsg("a1", [{ type: "reasoning", text: "", state: "streaming" }])],
      [userMsg, assistantMsg("a1", [{ type: "text", text: "" }])],
    ];
    for (const messages of preContentShapes) {
      const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
      expect(result.current).toBe("waiting");
    }
  });

  test("hidden while a chip is streaming", () => {
    const messages = [
      userMsg,
      assistantMsg("a1", [{ type: "reasoning", text: "…", state: "streaming" }]),
    ];
    const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS * 5);
    });
    expect(result.current).toBe("hidden");
  });

  test("hidden while a tool card is the last part (tool owns feedback — decision 5)", () => {
    const messages = [
      userMsg,
      assistantMsg("a1", [
        { type: "reasoning", text: "r", state: "done" },
        { type: "tool-get_section", toolCallId: "tc-1", state: "input-available" },
      ]),
    ];
    const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS * 5);
    });
    expect(result.current).toBe("hidden");
  });

  test("window (b): chip collapsed with nothing after → visible after the grace delay", () => {
    const messages = [
      userMsg,
      assistantMsg("a1", [{ type: "reasoning", text: "r", state: "done" }]),
    ];
    const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
    expect(result.current).toBe("hidden");
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS);
    });
    expect(result.current).toBe("waiting");
  });

  test("chip→tool micro-gap inside the grace delay never flashes (decision 5)", () => {
    const collapsed = [
      userMsg,
      assistantMsg("a1", [{ type: "reasoning", text: "r", state: "done" }]),
    ];
    const { result, rerender } = renderHook(
      ({ messages }) => useDeadAirPlaceholder(messages, "streaming"),
      { initialProps: { messages: collapsed } },
    );
    // Tool card arrives well within the grace window.
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS / 3);
    });
    rerender({
      messages: [
        userMsg,
        assistantMsg("a1", [
          { type: "reasoning", text: "r", state: "done" },
          { type: "tool-x", toolCallId: "tc-1", state: "input-available" },
        ]),
      ],
    });
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS * 5);
    });
    expect(result.current).toBe("hidden");
  });

  test("window (c): tool round complete with nothing after → visible after the grace delay (DEV-109 ruling)", () => {
    const messages = [
      userMsg,
      assistantMsg("a1", [
        { type: "reasoning", text: "r", state: "done" },
        { type: "tool-get_section", toolCallId: "tc-1", state: "output-available" },
      ]),
    ];
    const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
    expect(result.current).toBe("hidden");
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS);
    });
    expect(result.current).toBe("waiting");
  });

  test("window (c): errored tool result is also terminal → visible after grace", () => {
    const messages = [
      userMsg,
      assistantMsg("a1", [
        { type: "tool-get_section", toolCallId: "tc-1", state: "output-error", errorText: "x" },
      ]),
    ];
    const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS);
    });
    expect(result.current).toBe("waiting");
  });

  test("window (c) suppressed while any sibling tool part is still in flight", () => {
    const messages = [
      userMsg,
      assistantMsg("a1", [
        { type: "tool-a", toolCallId: "tc-1", state: "input-available" },
        { type: "tool-b", toolCallId: "tc-2", state: "output-available" },
      ]),
    ];
    const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS * 5);
    });
    expect(result.current).toBe("hidden");
  });

  test("tool-complete→next-part micro-gap inside the grace delay never flashes", () => {
    const toolDone = [
      userMsg,
      assistantMsg("a1", [{ type: "tool-x", toolCallId: "tc-1", state: "output-available" }]),
    ];
    const { result, rerender } = renderHook(
      ({ messages }) => useDeadAirPlaceholder(messages, "streaming"),
      { initialProps: { messages: toolDone } },
    );
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS / 3);
    });
    rerender({
      messages: [
        userMsg,
        assistantMsg("a1", [
          { type: "tool-x", toolCallId: "tc-1", state: "output-available" },
          { type: "reasoning", text: "next round", state: "streaming" },
        ]),
      ],
    });
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS * 5);
    });
    expect(result.current).toBe("hidden");
  });

  test("hidden once reply text starts (placeholder yields to the answer)", () => {
    const messages = [
      userMsg,
      assistantMsg("a1", [
        { type: "reasoning", text: "r", state: "done" },
        { type: "text", text: "answer…" },
      ]),
    ];
    const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS * 5);
    });
    expect(result.current).toBe("hidden");
  });

  test("zero-delta suppressed chip: no chip renders, so placeholder keeps covering (S-chip-08)", () => {
    // No churn: the placeholder has been up since submit and simply stays —
    // it never flashes off/on around the suppressed part.
    const messages = [
      userMsg,
      assistantMsg("a1", [{ type: "reasoning", text: "", state: "done" }]),
    ];
    const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
    expect(result.current).toBe("waiting");
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS * 5);
    });
    expect(result.current).toBe("waiting");
  });

  test("hidden at ready / error status", () => {
    const messages = [
      userMsg,
      assistantMsg("a1", [{ type: "reasoning", text: "r", state: "done" }]),
    ];
    for (const status of ["ready", "error"] as const) {
      const { result } = renderHook(() => useDeadAirPlaceholder(messages, status));
      act(() => {
        vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS * 5);
      });
      expect(result.current).toBe("hidden");
    }
  });
});
