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
      useFollowBottom(ref as React.RefObject<HTMLElement | null>),
    );
    act(() => result.current.handleScroll());
    expect(result.current.shouldFollowBottom).toBe(true);
  });

  test("shouldFollowBottom=false when more than 100px from bottom", () => {
    const ref = { current: makeContainer(0, 1000, 150) };
    const { result } = renderHook(() =>
      useFollowBottom(ref as React.RefObject<HTMLElement | null>),
    );
    act(() => result.current.handleScroll());
    expect(result.current.shouldFollowBottom).toBe(false);
  });

  test("forceFollowBottom() sets flag true regardless of position", () => {
    const ref = { current: makeContainer(0, 1000, 150) };
    const { result } = renderHook(() =>
      useFollowBottom(ref as React.RefObject<HTMLElement | null>),
    );
    act(() => result.current.handleScroll());
    expect(result.current.shouldFollowBottom).toBe(false);

    act(() => result.current.forceFollowBottom());
    expect(result.current.shouldFollowBottom).toBe(true);
  });
});
