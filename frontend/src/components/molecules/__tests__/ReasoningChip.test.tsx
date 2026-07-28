import { describe, test, expect, vi } from "vitest";
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
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("Thinking…");
    expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("reasoning body text");
  });

  test("streaming + stalled swaps the degraded copy into the header (C4)", () => {
    render(<ReasoningChip {...baseProps} chipState="streaming" expanded={true} stalled={true} />);
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("Still working…");
  });

  test("done shows Thought for Xs; stalled does not leak into collapsed headers", () => {
    render(<ReasoningChip {...baseProps} chipState="done" stalled={true} />);
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("Thought for 3s");
  });

  test("aborted shows Stopped — thought for Xs (decision 6)", () => {
    render(<ReasoningChip {...baseProps} chipState="aborted" />);
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent(
      "Stopped — thought for 3s",
    );
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

  test("header carries aria-live=polite (decision 8 minimal SR surface)", () => {
    render(<ReasoningChip {...baseProps} chipState="streaming" expanded={true} />);
    expect(screen.getByTestId("reasoning-chip-header")).toHaveAttribute("aria-live", "polite");
  });
});
