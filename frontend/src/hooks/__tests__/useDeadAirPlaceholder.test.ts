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

  test("zero-delta suppressed chip does not trigger placeholder churn (S-chip-08)", () => {
    const messages = [
      userMsg,
      assistantMsg("a1", [{ type: "reasoning", text: "", state: "done" }]),
    ];
    const { result } = renderHook(() => useDeadAirPlaceholder(messages, "streaming"));
    act(() => {
      vi.advanceTimersByTime(PLACEHOLDER_GRACE_MS * 5);
    });
    expect(result.current).toBe("hidden");
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
