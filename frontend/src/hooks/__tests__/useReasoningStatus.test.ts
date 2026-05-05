import { describe, test, expect, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useReasoningStatus, STALLED_THRESHOLD_MS } from "../useReasoningStatus";

describe("useReasoningStatus — initial state", () => {
  test("reasoningStatusText defaults to null", () => {
    const { result } = renderHook(() => useReasoningStatus());
    expect(result.current.reasoningStatusText).toBeNull();
  });
});

describe("useReasoningStatus — data-reasoning-status ingestion", () => {
  test("sets reasoningStatusText from part.data.text", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking about the answer" },
      });
    });

    expect(result.current.reasoningStatusText).toBe("thinking about the answer");
  });

  test("renders text verbatim without trimming or transformation", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "  spaced text  " },
      });
    });

    expect(result.current.reasoningStatusText).toBe("  spaced text  ");
  });

  test("rapid sequential data-reasoning-status events: last one wins", () => {
    const { result } = renderHook(() => useReasoningStatus());
    act(() => {
      result.current.handleData({ type: "data-reasoning-status", data: { text: "first" } });
      result.current.handleData({ type: "data-reasoning-status", data: { text: "second" } });
      result.current.handleData({ type: "data-reasoning-status", data: { text: "third" } });
    });
    expect(result.current.reasoningStatusText).toBe("third");
  });

  test("data: null is ignored (defensive)", () => {
    const { result } = renderHook(() => useReasoningStatus());
    act(() => {
      result.current.handleData({ type: "data-reasoning-status", data: null as never });
    });
    expect(result.current.reasoningStatusText).toBeNull();
  });

  test("ignores event when part.data is missing", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "valid" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("valid");

    act(() => {
      result.current.handleData({ type: "data-reasoning-status" });
    });

    expect(result.current.reasoningStatusText).toBe("valid");
  });

  test("ignores event when part.data.text is not a string", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "valid" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("valid");

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: {},
      });
    });

    expect(result.current.reasoningStatusText).toBe("valid");
  });
});

describe("useReasoningStatus — 6 clear triggers", () => {
  test("text-start clears reasoningStatusText", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("thinking");

    act(() => {
      result.current.handleData({ type: "text-start" });
    });

    expect(result.current.reasoningStatusText).toBeNull();
  });

  test("tool-input-available clears reasoningStatusText", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("thinking");

    act(() => {
      result.current.handleData({ type: "tool-input-available" });
    });

    expect(result.current.reasoningStatusText).toBeNull();
  });

  test("finish clears reasoningStatusText and sets finishedRef", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("thinking");

    act(() => {
      result.current.handleData({ type: "finish" });
    });
    expect(result.current.reasoningStatusText).toBeNull();

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "late ghost" },
      });
    });
    expect(result.current.reasoningStatusText).toBeNull();
  });

  test("error clears reasoningStatusText and sets finishedRef", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("thinking");

    act(() => {
      result.current.handleData({ type: "error" });
    });
    expect(result.current.reasoningStatusText).toBeNull();

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "late ghost" },
      });
    });
    expect(result.current.reasoningStatusText).toBeNull();
  });

  test("clearReasoningStatus clears reasoningStatusText and sets clearedRef", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("thinking");

    act(() => {
      result.current.clearReasoningStatus();
    });
    expect(result.current.reasoningStatusText).toBeNull();

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "stop ghost" },
      });
    });
    expect(result.current.reasoningStatusText).toBeNull();
  });

  test("resetForNewTurn clears reasoningStatusText and resets both refs", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "old turn" },
      });
      result.current.handleData({ type: "finish" });
    });
    expect(result.current.reasoningStatusText).toBeNull();

    act(() => {
      result.current.resetForNewTurn();
    });
    expect(result.current.reasoningStatusText).toBeNull();

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "new turn thinking" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("new turn thinking");
  });
});

describe("useReasoningStatus — D31 race-condition guards", () => {
  test("clearedRef (S-rsn-11): after clearReasoningStatus, late data-reasoning-status events are ignored until resetForNewTurn", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.clearReasoningStatus();
    });

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "ghost A" },
      });
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "ghost B" },
      });
    });
    expect(result.current.reasoningStatusText).toBeNull();

    act(() => {
      result.current.resetForNewTurn();
    });

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "fresh" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("fresh");
  });

  test("finishedRef (S-rsn-12): after finish, late data-reasoning-status events are ignored", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({ type: "finish" });
    });

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "post-finish ghost" },
      });
    });
    expect(result.current.reasoningStatusText).toBeNull();
  });

  test("finishedRef set by error blocks subsequent data-reasoning-status events", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({ type: "error" });
    });

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "post-error ghost" },
      });
    });
    expect(result.current.reasoningStatusText).toBeNull();
  });
});

describe("useReasoningStatus — routing isolation", () => {
  test("non-data-reasoning-status data-* event does not affect reasoningStatusText", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("thinking");

    act(() => {
      result.current.handleData({
        type: "data-tool-progress",
        id: "tc-1",
        data: { text: "should-be-ignored" } as never,
      });
    });

    expect(result.current.reasoningStatusText).toBe("thinking");
  });

  test("unknown event type is a no-op", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });

    act(() => {
      result.current.handleData({ type: "some-unknown-event" });
    });

    expect(result.current.reasoningStatusText).toBe("thinking");
  });
});

describe("useReasoningStatus — D14 stalled modifier (10s silence)", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  test("STALLED_THRESHOLD_MS is exported as 10_000", () => {
    expect(STALLED_THRESHOLD_MS).toBe(10_000);
  });

  test("stalled defaults to false", () => {
    vi.useFakeTimers();
    vi.setSystemTime(0);
    const { result } = renderHook(() => useReasoningStatus());
    expect(result.current.stalled).toBe(false);
  });

  test("after handleData: stalled stays false at 9s, flips to true past 10s, resets on next chunk", () => {
    vi.useFakeTimers();
    vi.setSystemTime(0);
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });
    expect(result.current.stalled).toBe(false);

    act(() => {
      vi.advanceTimersByTime(9_000);
    });
    expect(result.current.stalled).toBe(false);

    act(() => {
      vi.advanceTimersByTime(2_000);
    });
    expect(result.current.stalled).toBe(true);

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking more" },
      });
    });
    expect(result.current.stalled).toBe(false);
    expect(result.current.reasoningStatusText).toBe("thinking more");
  });

  test("interval is cleaned up on unmount (no timer leaks)", () => {
    vi.useFakeTimers();
    vi.setSystemTime(0);
    const { result, unmount } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });
    expect(vi.getTimerCount()).toBeGreaterThan(0);

    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });

  test("stalled clears when text is cleared (e.g. by finish)", () => {
    vi.useFakeTimers();
    vi.setSystemTime(0);
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "thinking" },
      });
    });
    act(() => {
      vi.advanceTimersByTime(11_000);
    });
    expect(result.current.stalled).toBe(true);

    act(() => {
      result.current.handleData({ type: "finish" });
    });
    expect(result.current.reasoningStatusText).toBeNull();
    expect(result.current.stalled).toBe(false);
  });
});

describe("useReasoningStatus — resetForNewTurn idempotency", () => {
  test("calling resetForNewTurn twice is safe and still allows fresh ingestion", () => {
    const { result } = renderHook(() => useReasoningStatus());

    act(() => {
      result.current.handleData({ type: "finish" });
      result.current.resetForNewTurn();
      result.current.resetForNewTurn();
    });

    expect(result.current.reasoningStatusText).toBeNull();

    act(() => {
      result.current.handleData({
        type: "data-reasoning-status",
        data: { text: "after double reset" },
      });
    });
    expect(result.current.reasoningStatusText).toBe("after double reset");
  });
});
