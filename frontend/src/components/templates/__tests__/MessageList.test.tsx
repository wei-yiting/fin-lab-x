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
        reasoningStatusText={null}
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
        reasoningStatusText={null}
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
        reasoningStatusText={null}
        emptyContent={<div data-testid="empty-state">Empty</div>}
      />,
    );

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });
});

describe("MessageList — aborted message frozen indicator", () => {
  test("aborted assistant with no text part renders frozen indicator with captured reasoning + STOPPED", () => {
    render(
      <MessageList
        messages={[
          { id: "u1", role: "user", parts: [{ type: "text", text: "q" }] },
          { id: "a1", role: "assistant", parts: [] },
        ]}
        status="ready"
        toolProgress={{}}
        abortedTools={new Set()}
        abortedMessages={new Map([["a1", { frozenReasoningText: "分析中" }]])}
        onRegenerate={vi.fn()}
        reasoningStatusText={null}
      />,
    );

    expect(screen.getByTestId("reasoning-indicator")).toBeInTheDocument();
    expect(screen.getByText("分析中")).toBeInTheDocument();
    expect(screen.getByText("STOPPED")).toBeInTheDocument();
  });

  test("aborted assistant WITH a text part does NOT render the sibling frozen indicator", () => {
    // 9c: when partial text exists, AssistantMessage appends the inline STOPPED
    // label itself, so MessageList must not also emit a frozen sibling.
    render(
      <MessageList
        messages={[
          { id: "u1", role: "user", parts: [{ type: "text", text: "q" }] },
          { id: "a1", role: "assistant", parts: [{ type: "text", text: "partial" }] },
        ]}
        status="ready"
        toolProgress={{}}
        abortedTools={new Set()}
        abortedMessages={new Map([["a1", { frozenReasoningText: "ignored" }]])}
        onRegenerate={vi.fn()}
        reasoningStatusText={null}
      />,
    );

    expect(screen.queryByTestId("reasoning-indicator")).not.toBeInTheDocument();
    expect(screen.getByTestId("text-stopped-label")).toHaveTextContent("STOPPED");
    expect(screen.queryByText("ignored")).not.toBeInTheDocument();
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
        reasoningStatusText={null}
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
        reasoningStatusText={null}
      />,
    );

    expect(screen.getByTestId("message-list")).toHaveAttribute("data-status", "error");
    expect(screen.getByText("q")).toBeInTheDocument();
  });
});
