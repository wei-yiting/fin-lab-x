import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useReasoningTimers } from "../useReasoningTimers";
import { chipKey } from "@/lib/reasoning-chips";

function assistantMsg(id: string, parts: Array<{ type: string; [k: string]: unknown }>) {
  return { id, role: "assistant", parts };
}

describe("useReasoningTimers — Thought-for-Xs measurement (decision 2)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-28T10:00:00Z"));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  test("clock starts at first sight and freezes at the next part's arrival (first tool-start)", () => {
    const { result } = renderHook(() => useReasoningTimers());
    const reasoning = { type: "reasoning", text: "…", state: "streaming" };

    act(() => {
      result.current.observe([assistantMsg("a1", [reasoning])], true);
    });

    vi.setSystemTime(new Date("2026-07-28T10:00:03Z"));
    // Tool part arrives — the freezing render.
    act(() => {
      result.current.observe(
        [
          assistantMsg("a1", [
            { ...reasoning, state: "done" },
            { type: "tool-get_section", toolCallId: "tc-1", state: "input-available" },
          ]),
        ],
        true,
      );
    });

    // Tool executes for 12 more seconds — X must NOT include it.
    vi.setSystemTime(new Date("2026-07-28T10:00:15Z"));
    expect(result.current.getSeconds(chipKey("a1", 0))).toBe(3);
  });

  test("multi-round chips measure independently", () => {
    const { result } = renderHook(() => useReasoningTimers());
    const r1 = { type: "reasoning", text: "r1", state: "done" };
    const tool = { type: "tool-x", toolCallId: "tc-1", state: "output-available" };

    act(() => {
      result.current.observe([assistantMsg("a1", [r1])], true);
    });
    vi.setSystemTime(new Date("2026-07-28T10:00:02Z"));
    act(() => {
      result.current.observe([assistantMsg("a1", [r1, tool])], true);
    });
    // Round 2 starts 10s in, runs 5s until the text part arrives.
    vi.setSystemTime(new Date("2026-07-28T10:00:10Z"));
    const r2 = { type: "reasoning", text: "r2", state: "streaming" };
    act(() => {
      result.current.observe([assistantMsg("a1", [r1, tool, r2])], true);
    });
    vi.setSystemTime(new Date("2026-07-28T10:00:15Z"));
    act(() => {
      result.current.observe(
        [assistantMsg("a1", [r1, tool, { ...r2, state: "done" }, { type: "text", text: "a" }])],
        true,
      );
    });

    expect(result.current.getSeconds(chipKey("a1", 0))).toBe(2);
    expect(result.current.getSeconds(chipKey("a1", 2))).toBe(5);
  });

  test("abort samples at Stop (chat leaves the active pair)", () => {
    const { result } = renderHook(() => useReasoningTimers());
    const reasoning = { type: "reasoning", text: "half", state: "streaming" };

    act(() => {
      result.current.observe([assistantMsg("a1", [reasoning])], true);
    });
    vi.setSystemTime(new Date("2026-07-28T10:00:04Z"));
    // Stop: status back to ready, part still state=streaming.
    act(() => {
      result.current.observe([assistantMsg("a1", [reasoning])], false);
    });
    // Time passing after the stop must not change X.
    vi.setSystemTime(new Date("2026-07-28T10:00:30Z"));
    expect(result.current.getSeconds(chipKey("a1", 0))).toBe(4);
  });

  test("unfrozen chip reports live elapsed until the freezing event", () => {
    const { result } = renderHook(() => useReasoningTimers());
    act(() => {
      result.current.observe(
        [assistantMsg("a1", [{ type: "reasoning", text: "x", state: "streaming" }])],
        true,
      );
    });
    vi.setSystemTime(new Date("2026-07-28T10:00:07Z"));
    expect(result.current.getSeconds(chipKey("a1", 0))).toBe(7);
  });

  test("reset clears all timings (full-session clear only — handleClearSession)", () => {
    const { result } = renderHook(() => useReasoningTimers());
    act(() => {
      result.current.observe(
        [assistantMsg("a1", [{ type: "reasoning", text: "x", state: "streaming" }])],
        true,
      );
    });
    vi.setSystemTime(new Date("2026-07-28T10:00:05Z"));
    act(() => {
      result.current.reset();
    });
    // Re-observed after reset: the clock restarts from the current instant
    // (part ids reused across turns cannot inherit the old measurement).
    act(() => {
      result.current.observe(
        [assistantMsg("a1", [{ type: "reasoning", text: "y", state: "streaming" }])],
        true,
      );
    });
    expect(result.current.getSeconds(chipKey("a1", 0))).toBe(0);
  });

  test("observing an unrelated new turn's messages does not disturb an already-frozen past chip (DEV-106 review fix)", () => {
    const { result } = renderHook(() => useReasoningTimers());
    const pastReasoning = { type: "reasoning", text: "past thought", state: "done" };
    const pastText = { type: "text", text: "past answer" };

    // Turn 1 completes and freezes at 4s.
    act(() => {
      result.current.observe([assistantMsg("a1", [pastReasoning])], true);
    });
    vi.setSystemTime(new Date("2026-07-28T10:00:04Z"));
    act(() => {
      result.current.observe([assistantMsg("a1", [pastReasoning, pastText])], true);
    });
    expect(result.current.getSeconds(chipKey("a1", 0))).toBe(4);

    // Turn 2 starts (no reset() call — ChatPanel must not clear the whole
    // map on ordinary send/regenerate/retry). The still-rendered turn-1
    // message is observed again alongside the new turn's message.
    vi.setSystemTime(new Date("2026-07-28T10:00:30Z"));
    const newReasoning = { type: "reasoning", text: "new thought", state: "streaming" };
    act(() => {
      result.current.observe(
        [assistantMsg("a1", [pastReasoning, pastText]), assistantMsg("a2", [newReasoning])],
        true,
      );
    });

    // The past chip's frozen duration must be exactly what it was — not
    // reset to 0 by the new turn's observation pass.
    expect(result.current.getSeconds(chipKey("a1", 0))).toBe(4);
  });
});
