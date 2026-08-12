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

// S-regen-02: the Regenerate visibility rule — last assistant message AND
// status=ready — is derived here and handed to AssistantMessage as the
// presence/absence of onRegenerate, so no second POST can be issued while a
// turn is in flight or mid-stream.
describe("MessageList — Regenerate visibility (S-regen-02)", () => {
  const transcript = [
    { id: "u1", role: "user", parts: [{ type: "text", text: "q1" }] },
    { id: "a1", role: "assistant", parts: [{ type: "text", text: "answer one" }] },
    { id: "u2", role: "user", parts: [{ type: "text", text: "q2" }] },
    { id: "a2", role: "assistant", parts: [{ type: "text", text: "answer two" }] },
  ];

  test("status=ready → exactly one Regenerate button, on the last message", () => {
    render(
      <MessageList
        messages={transcript}
        status="ready"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
      />,
    );
    const buttons = screen.getAllByTestId("regenerate-btn");
    expect(buttons).toHaveLength(1);
    expect(buttons[0].closest('[data-testid="assistant-message"]')).toHaveTextContent("answer two");
  });

  test.each(["submitted", "streaming", "error"] as const)(
    "status=%s → no Regenerate button anywhere",
    (status) => {
      render(
        <MessageList
          messages={transcript}
          status={status}
          toolProgress={{}}
          abortedTools={new Set()}
          onRegenerate={vi.fn()}
        />,
      );
      expect(screen.queryByTestId("regenerate-btn")).not.toBeInTheDocument();
    },
  );
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
