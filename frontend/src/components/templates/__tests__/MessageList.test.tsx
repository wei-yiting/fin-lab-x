import { describe, test, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageList } from "../MessageList";

describe("MessageList — placeholder slot", () => {
  test("renders the placeholder node when provided", () => {
    render(
      <MessageList
        messages={[{ id: "u1", role: "user", parts: [{ type: "text", text: "q" }] }]}
        status="submitted"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
        placeholder={<div data-testid="activity-placeholder">Thinking…</div>}
      />,
    );

    expect(screen.getByTestId("activity-placeholder")).toBeInTheDocument();
  });

  test("no placeholder node renders nothing extra", () => {
    render(
      <MessageList
        messages={[{ id: "u1", role: "user", parts: [{ type: "text", text: "q" }] }]}
        status="streaming"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
      />,
    );

    expect(screen.queryByTestId("activity-placeholder")).not.toBeInTheDocument();
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

describe("MessageList — chip context threading", () => {
  test("reasoning parts render as chips via AssistantMessage", () => {
    render(
      <MessageList
        messages={[
          { id: "u1", role: "user", parts: [{ type: "text", text: "q" }] },
          {
            id: "a1",
            role: "assistant",
            parts: [{ type: "reasoning", text: "思考中", state: "streaming" }],
          },
        ]}
        status="streaming"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
        getChipSeconds={() => 0}
        chipOverrides={new Map()}
        onToggleChip={vi.fn()}
      />,
    );

    expect(screen.getByTestId("reasoning-chip")).toBeInTheDocument();
    expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-state", "streaming");
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
