import type React from "react";
import { describe, test, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useFollowBottom } from "../useFollowBottom";

describe("useFollowBottom — 100px threshold smart tracking", () => {
  function makeContainer(scrollTop: number, scrollHeight: number, clientHeight: number) {
    const div = document.createElement("div");
    Object.defineProperty(div, "scrollTop", { value: scrollTop, writable: true });
    Object.defineProperty(div, "scrollHeight", { value: scrollHeight, writable: true });
    Object.defineProperty(div, "clientHeight", { value: clientHeight, writable: true });
    return div;
  }

  test("shouldFollowBottom=true when within 100px of bottom", () => {
    const ref = { current: makeContainer(800, 1000, 150) };
    const { result } = renderHook(() =>
      useFollowBottom(ref as React.RefObject<HTMLElement | null>, []),
    );
    act(() => result.current.handleScroll());
    expect(result.current.shouldFollowBottom).toBe(true);
  });

  test("shouldFollowBottom=false when more than 100px from bottom", () => {
    const ref = { current: makeContainer(0, 1000, 150) };
    const { result } = renderHook(() =>
      useFollowBottom(ref as React.RefObject<HTMLElement | null>, []),
    );
    act(() => result.current.handleScroll());
    expect(result.current.shouldFollowBottom).toBe(false);
  });

  test("forceFollowBottom() sets flag true regardless of position", () => {
    const ref = { current: makeContainer(0, 1000, 150) };
    const { result } = renderHook(() =>
      useFollowBottom(ref as React.RefObject<HTMLElement | null>, []),
    );
    act(() => result.current.handleScroll());
    expect(result.current.shouldFollowBottom).toBe(false);

    act(() => result.current.forceFollowBottom());
    expect(result.current.shouldFollowBottom).toBe(true);
  });

  test("scrolls container to bottom when scrollTrigger changes while shouldFollowBottom=true", () => {
    const container = makeContainer(800, 1000, 150);
    const ref = { current: container };
    const { result, rerender } = renderHook(
      ({ trigger }) => useFollowBottom(ref as React.RefObject<HTMLElement | null>, trigger),
      { initialProps: { trigger: 1 } },
    );
    // After initial mount, the effect already ran once. Mutate scrollHeight
    // to simulate new content and rerender with a new trigger.
    Object.defineProperty(container, "scrollHeight", { value: 2000, writable: true });
    rerender({ trigger: 2 });
    expect(container.scrollTop).toBe(2000);
    expect(result.current.shouldFollowBottom).toBe(true);
  });
});
