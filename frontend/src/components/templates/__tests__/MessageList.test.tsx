import { describe, test, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { ReactNode } from "react";
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

// M-1.1: in dead-air windows B/C the placeholder mounts on a 300ms grace
// timer, i.e. in a render where `messages` did NOT change. If the follow-
// bottom trigger watched `messages` alone, the placeholder would be
// appended below the fold of a tall transcript and the user would see
// nothing during exactly the period it exists to cover.
describe("MessageList — follow-bottom when the placeholder mounts", () => {
  // Same array identity across rerenders → the `messages` half of the
  // trigger is provably unchanged, so only placeholder visibility can drive
  // the scroll.
  const messages = [
    { id: "u1", role: "user", parts: [{ type: "text", text: "q" }] },
    { id: "a1", role: "assistant", parts: [{ type: "text", text: "a long answer" }] },
  ];

  function renderList(placeholder?: ReactNode) {
    return (
      <MessageList
        messages={messages}
        status="streaming"
        toolProgress={{}}
        abortedTools={new Set()}
        onRegenerate={vi.fn()}
        placeholder={placeholder}
      />
    );
  }

  // jsdom has no layout: give the viewport measurable scroll metrics and a
  // plain writable scrollTop so the hook's assignment is observable.
  function stubViewportMetrics(el: HTMLElement) {
    Object.defineProperty(el, "scrollTop", { value: 0, writable: true, configurable: true });
    Object.defineProperty(el, "scrollHeight", { value: 2000, writable: true, configurable: true });
    Object.defineProperty(el, "clientHeight", { value: 300, writable: true, configurable: true });
  }

  test("placeholder appears without a messages change → viewport follows to the bottom", () => {
    const { rerender } = render(renderList());
    const viewport = screen.getByTestId("message-list-viewport");
    stubViewportMetrics(viewport);

    rerender(renderList(<div data-testid="activity-placeholder">Thinking</div>));

    expect(screen.getByTestId("activity-placeholder")).toBeInTheDocument();
    expect(viewport.scrollTop).toBe(2000);
  });

  test("user scrolled up → placeholder mount does not yank the viewport down", () => {
    const { rerender } = render(renderList());
    const viewport = screen.getByTestId("message-list-viewport");
    stubViewportMetrics(viewport);

    // 2000 - 0 - 300 = 1700px from the bottom → past the 100px follow threshold.
    fireEvent.scroll(viewport);
    expect(viewport).toHaveAttribute("data-at-bottom", "false");

    rerender(renderList(<div data-testid="activity-placeholder">Thinking</div>));

    expect(viewport.scrollTop).toBe(0);
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
