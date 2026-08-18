import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useStallTimer } from "../useStallTimer";
import { STALL_THRESHOLD_MS } from "@/lib/timing";

describe("useStallTimer — global stall stopwatch", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  test("default threshold is 10s (locked by this test)", () => {
    expect(STALL_THRESHOLD_MS).toBe(10_000);
  });

  test("flips stalled=true after the threshold with no activity", () => {
    const { result } = renderHook(() => useStallTimer(true));
    expect(result.current.stalled).toBe(false);

    act(() => {
      vi.advanceTimersByTime(STALL_THRESHOLD_MS);
    });
    expect(result.current.stalled).toBe(true);
  });

  test("activity before the threshold resets the stopwatch (8s delta case)", () => {
    const { result } = renderHook(() => useStallTimer(true));

    act(() => {
      vi.advanceTimersByTime(8_000);
    });
    act(() => {
      result.current.notifyActivity();
    });
    // 8s later the original deadline has passed but the reset holds.
    act(() => {
      vi.advanceTimersByTime(8_000);
    });
    expect(result.current.stalled).toBe(false);
    // Full threshold after the reset → stalled.
    act(() => {
      vi.advanceTimersByTime(STALL_THRESHOLD_MS - 8_000);
    });
    expect(result.current.stalled).toBe(true);
  });

  test("activity clears an already-stalled state", () => {
    const { result } = renderHook(() => useStallTimer(true));
    act(() => {
      vi.advanceTimersByTime(STALL_THRESHOLD_MS);
    });
    expect(result.current.stalled).toBe(true);

    act(() => {
      result.current.notifyActivity();
    });
    expect(result.current.stalled).toBe(false);
  });

  test("deactivation (turn end) resets; a new turn starts from zero", () => {
    const { result, rerender } = renderHook(({ active }) => useStallTimer(active), {
      initialProps: { active: true },
    });
    act(() => {
      vi.advanceTimersByTime(STALL_THRESHOLD_MS + 4_000);
    });
    expect(result.current.stalled).toBe(true);

    // Abort → ready
    rerender({ active: false });
    expect(result.current.stalled).toBe(false);

    // Immediate new turn: no stale 14s leaks in.
    rerender({ active: true });
    act(() => {
      vi.advanceTimersByTime(STALL_THRESHOLD_MS - 1_000);
    });
    expect(result.current.stalled).toBe(false);
    act(() => {
      vi.advanceTimersByTime(1_000);
    });
    expect(result.current.stalled).toBe(true);
  });

  test("sustained activity never stalls (re-arm path, 1s deltas over 30s)", () => {
    const { result } = renderHook(() => useStallTimer(true));
    for (let i = 0; i < 30; i++) {
      act(() => {
        vi.advanceTimersByTime(1_000);
      });
      act(() => {
        result.current.notifyActivity();
      });
      expect(result.current.stalled).toBe(false);
    }
    // Activity stops → the stopwatch still reaches the threshold.
    act(() => {
      vi.advanceTimersByTime(STALL_THRESHOLD_MS);
    });
    expect(result.current.stalled).toBe(true);
  });

  test("activity does not rebuild an already-pending check", () => {
    const clearSpy = vi.spyOn(globalThis, "clearTimeout");
    const { result } = renderHook(() => useStallTimer(true));
    clearSpy.mockClear();

    act(() => {
      for (let i = 0; i < 20; i++) result.current.notifyActivity();
    });

    // The pending check re-arms itself against the wall clock, so no
    // teardown/rebuild churn per stream delta.
    expect(clearSpy).not.toHaveBeenCalled();
    clearSpy.mockRestore();
  });

  test("inactive hook never stalls", () => {
    const { result } = renderHook(() => useStallTimer(false));
    act(() => {
      vi.advanceTimersByTime(STALL_THRESHOLD_MS * 3);
    });
    expect(result.current.stalled).toBe(false);
  });
});
