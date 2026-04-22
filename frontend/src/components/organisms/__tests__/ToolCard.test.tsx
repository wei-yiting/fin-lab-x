import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ToolCard } from "../ToolCard";

describe("ToolCard — visual state via data-tool-state attribute", () => {
  const baseToolPart = {
    type: "tool" as const,
    toolCallId: "tc-1",
    toolName: "yfinance_quote",
    input: { ticker: "AAPL" },
  };

  test('input-streaming → data-tool-state="input-streaming", running status dot', () => {
    render(<ToolCard part={{ ...baseToolPart, state: "input-streaming" }} isAborted={false} />);
    const card = screen.getByTestId("tool-card");
    expect(card).toHaveAttribute("data-tool-state", "input-streaming");
    expect(screen.getByTestId("status-dot")).toHaveAttribute("data-status-state", "running");
  });

  test('input-available → data-tool-state="input-available", running status dot', () => {
    render(<ToolCard part={{ ...baseToolPart, state: "input-available" }} isAborted={false} />);
    const card = screen.getByTestId("tool-card");
    expect(card).toHaveAttribute("data-tool-state", "input-available");
    expect(card).toHaveAttribute("data-tool-call-id", "tc-1");
    expect(screen.getByTestId("status-dot")).toHaveAttribute("data-status-state", "running");
  });

  test('output-available → data-tool-state="output-available", success status dot', () => {
    render(
      <ToolCard
        part={{ ...baseToolPart, state: "output-available", output: { price: 1045 } }}
        isAborted={false}
      />,
    );
    const card = screen.getByTestId("tool-card");
    expect(card).toHaveAttribute("data-tool-state", "output-available");
    expect(screen.getByTestId("status-dot")).toHaveAttribute("data-status-state", "success");
  });

  test('output-error → data-tool-state="output-error" + friendly error inline', () => {
    render(
      <ToolCard
        part={{ ...baseToolPart, state: "output-error", errorText: "API rate limit exceeded" }}
        isAborted={false}
      />,
    );
    expect(screen.getByTestId("tool-card")).toHaveAttribute("data-tool-state", "output-error");
    expect(screen.getByTestId("status-dot")).toHaveAttribute("data-status-state", "error");
    expect(screen.getByText(/Too many requests/)).toBeInTheDocument();
    expect(screen.queryByText("API rate limit exceeded")).not.toBeInTheDocument();
  });

  test('isAborted=true with input-available → data-tool-state="aborted", aborted status dot', () => {
    render(<ToolCard part={{ ...baseToolPart, state: "input-available" }} isAborted={true} />);
    const card = screen.getByTestId("tool-card");
    expect(card).toHaveAttribute("data-tool-state", "aborted");
    expect(screen.getByTestId("status-dot")).toHaveAttribute("data-status-state", "aborted");
  });

  test('isAborted=true with input-streaming → data-tool-state="aborted"', () => {
    render(<ToolCard part={{ ...baseToolPart, state: "input-streaming" }} isAborted={true} />);
    const card = screen.getByTestId("tool-card");
    expect(card).toHaveAttribute("data-tool-state", "aborted");
    expect(screen.getByTestId("status-dot")).toHaveAttribute("data-status-state", "aborted");
  });
});

test("TC-comp-toolcard-02: expanded state stable across parent re-render with same toolCallId", async () => {
  const user = userEvent.setup();
  const { rerender } = render(
    <ToolCard
      part={{
        type: "tool",
        toolCallId: "tc-stable",
        toolName: "yfinance",
        state: "input-available",
        input: {},
      }}
      isAborted={false}
    />,
  );

  await user.click(screen.getByTestId("tool-card-expand"));
  expect(screen.getByTestId("tool-input-json")).toBeInTheDocument();

  rerender(
    <ToolCard
      part={{
        type: "tool",
        toolCallId: "tc-stable",
        toolName: "yfinance",
        state: "output-available",
        input: {},
        output: { price: 100 },
      }}
      isAborted={false}
    />,
  );

  expect(screen.getByTestId("tool-input-json")).toBeInTheDocument();
});
