import { describe, test, expect, afterEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReasoningChip } from "../ReasoningChip";

const baseProps = {
  text: "reasoning body text",
  seconds: 3,
  stalled: false,
  expanded: false,
  onToggle: vi.fn(),
  round: 1,
};

describe("ReasoningChip — header per state", () => {
  test("streaming shows Thinking… and the body window", () => {
    render(<ReasoningChip {...baseProps} chipState="streaming" expanded={true} />);
    expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-state", "streaming");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("思考中…");
    expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("reasoning body text");
  });

  test("streaming + stalled swaps the degraded copy into the header", () => {
    render(<ReasoningChip {...baseProps} chipState="streaming" expanded={true} stalled={true} />);
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("仍在處理中…");
  });

  test("done shows Thought for Xs; stalled does not leak into collapsed headers", () => {
    render(<ReasoningChip {...baseProps} chipState="done" stalled={true} />);
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("思考了 3 秒");
  });

  test("aborted shows Stopped — thought for Xs", () => {
    render(<ReasoningChip {...baseProps} chipState="aborted" />);
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("已停止 — 思考了 3 秒");
  });
});

describe("ReasoningChip — body and interaction", () => {
  test("collapsed hides the body; expanded shows the full text", () => {
    const { rerender } = render(<ReasoningChip {...baseProps} chipState="done" />);
    expect(screen.queryByTestId("reasoning-chip-body")).not.toBeInTheDocument();

    rerender(<ReasoningChip {...baseProps} chipState="done" expanded={true} />);
    expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-state", "expanded");
    expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("reasoning body text");
  });

  test("clicking the header fires onToggle", () => {
    const onToggle = vi.fn();
    render(<ReasoningChip {...baseProps} chipState="done" onToggle={onToggle} />);
    fireEvent.click(screen.getByTestId("reasoning-chip-header"));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  test("body renders raw pre-wrap text — newlines preserved, no markdown parsing", () => {
    render(
      <ReasoningChip
        {...baseProps}
        chipState="streaming"
        expanded={true}
        text={"line1\n\n**not bold**"}
      />,
    );
    const body = screen.getByTestId("reasoning-chip-body");
    expect(body.textContent).toBe("line1\n\n**not bold**");
    expect(body.querySelector("strong")).toBeNull();
    expect(body).toHaveClass("whitespace-pre-wrap");
  });

  test("header carries aria-live=polite (minimal SR surface)", () => {
    render(<ReasoningChip {...baseProps} chipState="streaming" expanded={true} />);
    expect(screen.getByTestId("reasoning-chip-header")).toHaveAttribute("aria-live", "polite");
  });

  test("header's accessible name carries the live copy plus the toggle action", () => {
    const { rerender } = render(
      <ReasoningChip {...baseProps} chipState="streaming" expanded={true} />,
    );
    expect(screen.getByRole("button", { name: "思考中… — 收合推理過程" })).toBeVisible();

    rerender(<ReasoningChip {...baseProps} chipState="streaming" expanded={true} stalled={true} />);
    expect(screen.getByRole("button", { name: "仍在處理中… — 收合推理過程" })).toBeVisible();

    rerender(<ReasoningChip {...baseProps} chipState="done" />);
    expect(screen.getByRole("button", { name: "思考了 3 秒 — 展開推理過程" })).toBeVisible();
  });
});

// The DOM contract (docs/frontend_dom_contract.md) declares `data-state`,
// `data-round` and `aria-expanded` stable: `data-state` tracks the part
// lifecycle, `aria-expanded` tracks body visibility, and the two are decoupled.
describe("ReasoningChip — DOM contract attributes", () => {
  test("streaming + expanded: data-state=streaming, aria-expanded=true", () => {
    render(<ReasoningChip {...baseProps} chipState="streaming" expanded={true} />);
    expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-state", "streaming");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("reasoning-chip-body")).toBeInTheDocument();
  });

  test("an explicit collapse wins over a still-streaming part", () => {
    render(<ReasoningChip {...baseProps} chipState="streaming" expanded={false} />);
    expect(screen.queryByTestId("reasoning-chip-body")).not.toBeInTheDocument();
    expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-state", "streaming");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveAttribute("aria-expanded", "false");
  });

  test("done + collapsed: data-state=collapsed, aria-expanded=false", () => {
    render(<ReasoningChip {...baseProps} chipState="done" />);
    expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-state", "collapsed");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveAttribute("aria-expanded", "false");
  });

  test("done + expanded: data-state=expanded, aria-expanded=true", () => {
    render(<ReasoningChip {...baseProps} chipState="done" expanded={true} />);
    expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-state", "expanded");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveAttribute("aria-expanded", "true");
  });

  test("data-round carries the chip's 1-based ordinal within its message", () => {
    const { rerender } = render(<ReasoningChip {...baseProps} chipState="done" round={1} />);
    expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-round", "1");

    rerender(<ReasoningChip {...baseProps} chipState="done" round={3} />);
    expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-round", "3");
  });
});

describe("ReasoningChip — streaming window pinning", () => {
  const proto = HTMLElement.prototype;
  let scrollHeight = 0;

  // jsdom has no layout: scrollHeight always reads 0 and scrollTop is a no-op,
  // so both are shadowed on the prototype for the duration of these tests.
  function stubScrollMetrics(height: number) {
    scrollHeight = height;
    Object.defineProperty(proto, "scrollHeight", {
      configurable: true,
      get: () => scrollHeight,
    });
    Object.defineProperty(proto, "scrollTop", { configurable: true, writable: true, value: 0 });
  }

  afterEach(() => {
    Reflect.deleteProperty(proto, "scrollHeight");
    Reflect.deleteProperty(proto, "scrollTop");
  });

  test("pins the streaming window to its newest line as text grows", () => {
    stubScrollMetrics(120);
    const { rerender } = render(
      <ReasoningChip {...baseProps} chipState="streaming" expanded={true} text="line 1" />,
    );
    expect(screen.getByTestId("reasoning-chip-body").scrollTop).toBe(120);

    scrollHeight = 260;
    rerender(
      <ReasoningChip
        {...baseProps}
        chipState="streaming"
        expanded={true}
        text={"line 1\nline 2"}
      />,
    );
    expect(screen.getByTestId("reasoning-chip-body").scrollTop).toBe(260);
  });

  test("re-expanding a collapsed streaming chip re-pins to the bottom", () => {
    stubScrollMetrics(300);
    const { rerender } = render(
      <ReasoningChip {...baseProps} chipState="streaming" expanded={false} />,
    );
    expect(screen.queryByTestId("reasoning-chip-body")).not.toBeInTheDocument();

    rerender(<ReasoningChip {...baseProps} chipState="streaming" expanded={true} />);
    expect(screen.getByTestId("reasoning-chip-body").scrollTop).toBe(300);
  });
});
