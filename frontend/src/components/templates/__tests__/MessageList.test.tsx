import { describe, test, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageList } from "../MessageList";

describe("MessageList — ReasoningIndicator visibility", () => {
  test("transient data-tool-progress does not hide ReasoningIndicator", () => {
    const { rerender } = render(
      <MessageList
        messages={[{ id: "u1", role: "user", parts: [{ type: "text", text: "q" }] }]}
        status="streaming"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
      />,
    );

    expect(screen.getByTestId("reasoning-indicator")).toBeInTheDocument();

    rerender(
      <MessageList
        messages={[{ id: "u1", role: "user", parts: [{ type: "text", text: "q" }] }]}
        status="streaming"
        toolProgress={{ "tc-1": "fetching..." }}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
      />,
    );

    expect(screen.getByTestId("reasoning-indicator")).toBeInTheDocument();
    expect(screen.queryByTestId("tool-card")).not.toBeInTheDocument();
  });

  test("empty messages with ready status renders empty content", () => {
    render(
      <MessageList
        messages={[]}
        status="ready"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
        emptyContent={<div data-testid="empty-state">Empty</div>}
      />,
    );

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });
});

describe("MessageList — errorContent slot", () => {
  test("status=error with errorContent renders the error slot inside viewport", () => {
    render(
      <MessageList
        messages={[{ id: "u1", role: "user", parts: [{ type: "text", text: "q" }] }]}
        status="error"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
        errorContent={<div data-testid="error-slot-fixture">Oops</div>}
      />,
    );

    expect(screen.getByTestId("error-slot-fixture")).toBeInTheDocument();
    expect(screen.getByTestId("message-list")).toHaveAttribute("data-status", "error");
  });

  test("errorContent not provided at status=error still renders messages without crashing", () => {
    render(
      <MessageList
        messages={[{ id: "u1", role: "user", parts: [{ type: "text", text: "q" }] }]}
        status="error"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
      />,
    );

    expect(screen.getByTestId("message-list")).toHaveAttribute("data-status", "error");
    expect(screen.getByText("q")).toBeInTheDocument();
  });
});
