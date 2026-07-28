import { describe, test, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AssistantMessage } from "../AssistantMessage";

describe("AssistantMessage — parts dispatch", () => {
  test("renders text part as Markdown", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: "hello **world**" }],
    };
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.getByText(/hello/)).toBeInTheDocument();
  });

  test("renders tool part as ToolCard", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        {
          type: "tool" as const,
          state: "input-available",
          toolCallId: "tc-1",
          toolName: "yfinance",
          input: {},
        },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.getByTestId("tool-card")).toBeInTheDocument();
  });

  test("renders parallel tool parts in arrival order, stable", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        {
          type: "tool" as const,
          state: "output-available",
          toolCallId: "tc-A",
          toolName: "a",
          input: {},
          output: {},
        },
        {
          type: "tool" as const,
          state: "input-available",
          toolCallId: "tc-B",
          toolName: "b",
          input: {},
        },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    const cards = screen.getAllByTestId("tool-card");
    expect(cards).toHaveLength(2);
    expect(cards[0]).toHaveAttribute("data-tool-call-id", "tc-A");
    expect(cards[1]).toHaveAttribute("data-tool-call-id", "tc-B");
  });
});

describe("AssistantMessage — aborted tools", () => {
  test('input-available tool with id in abortedTools → ToolCard data-tool-state="aborted"', () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        {
          type: "tool" as const,
          state: "input-available",
          toolCallId: "tc-aborted",
          toolName: "x",
          input: {},
        },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        abortedTools={new Set(["tc-aborted"])}
        toolProgress={{}}
      />,
    );
    expect(screen.getByTestId("tool-card")).toHaveAttribute("data-tool-state", "aborted");
  });

  test('input-streaming tool with id in abortedTools → ToolCard data-tool-state="aborted"', () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        {
          type: "tool" as const,
          state: "input-streaming",
          toolCallId: "tc-aborted-streaming",
          toolName: "x",
          input: {},
        },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        abortedTools={new Set(["tc-aborted-streaming"])}
        toolProgress={{}}
      />,
    );
    expect(screen.getByTestId("tool-card")).toHaveAttribute("data-tool-state", "aborted");
  });

  test("output-available tool not affected by abortedTools", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        {
          type: "tool" as const,
          state: "output-available",
          toolCallId: "tc-done",
          toolName: "x",
          input: {},
          output: {},
        },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isLast={false}
        abortedTools={new Set(["tc-done"])}
        toolProgress={{}}
      />,
    );
    expect(screen.getByTestId("tool-card")).toHaveAttribute("data-tool-state", "output-available");
  });
});

describe("AssistantMessage — RegenerateButton visibility", () => {
  const baseMsg = {
    id: "a1",
    role: "assistant" as const,
    parts: [{ type: "text" as const, text: "done" }],
  };

  test("isLast=true and status=ready → button visible", () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
        onRegenerate={vi.fn()}
      />,
    );
    expect(screen.getByTestId("regenerate-btn")).toBeInTheDocument();
  });

  test("isLast=true but status=streaming → button hidden", () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isLast={true}
        status="streaming"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.queryByTestId("regenerate-btn")).not.toBeInTheDocument();
  });

  test("isLast=false → button hidden regardless of status", () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isLast={false}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.queryByTestId("regenerate-btn")).not.toBeInTheDocument();
  });

  // S-regen-02: button must be hidden for every non-ready status so no second
  // POST can be issued while one is already in flight or mid-stream.
  test.each(["submitted", "streaming", "error"] as const)(
    "isLast=true but status=%s → button hidden",
    (status) => {
      render(
        <AssistantMessage
          message={baseMsg}
          isLast={true}
          status={status}
          abortedTools={new Set()}
          toolProgress={{}}
          onRegenerate={vi.fn()}
        />,
      );
      expect(screen.queryByTestId("regenerate-btn")).not.toBeInTheDocument();
    },
  );
});

describe("AssistantMessage — aborted turn (derived from part shapes)", () => {
  test("aborted WITH text keeps Regenerate (there is something to regenerate from)", () => {
    // Aborted turn shape: a reasoning part stuck in state "streaming" at
    // status "ready" (no reasoning-end reached the wire).
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        { type: "reasoning" as const, text: "half a thought", state: "streaming" },
        { type: "text" as const, text: "partial answer" },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
        onRegenerate={vi.fn()}
      />,
    );
    expect(screen.getByText(/partial answer/)).toBeInTheDocument();
    expect(screen.getByTestId("regenerate-btn")).toBeInTheDocument();
  });

  test("aborted with only a tool part (no text) hides Regenerate (C2.a)", () => {
    // Stop-C: aborted mid-tool with no text body — the backend regenerate
    // path 422s on the missing finalized AIMessage, so the button is gated off.
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        {
          type: "tool" as const,
          state: "input-available",
          toolCallId: "tc-1",
          toolName: "x",
          input: {},
        },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isLast={true}
        status="ready"
        abortedTools={new Set(["tc-1"])}
        toolProgress={{}}
        onRegenerate={vi.fn()}
      />,
    );
    expect(screen.queryByTestId("regenerate-btn")).not.toBeInTheDocument();
  });
});

describe("AssistantMessage — reasoning chips (F6′)", () => {
  const chipProps = {
    isLast: true,
    abortedTools: new Set<string>(),
    toolProgress: {},
    getChipSeconds: () => 3,
    chipOverrides: new Map<string, boolean>(),
    onToggleChip: vi.fn(),
  };

  test("streaming reasoning part renders an expanded streaming chip with its text", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [{ type: "reasoning" as const, text: "分析 10-K 中", state: "streaming" }],
    };
    render(<AssistantMessage message={message} status="streaming" {...chipProps} />);
    const chip = screen.getByTestId("reasoning-chip");
    expect(chip).toHaveAttribute("data-state", "streaming");
    expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("分析 10-K 中");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("Thinking…");
  });

  test("done reasoning part collapses to Thought for Xs", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        { type: "reasoning" as const, text: "done thinking", state: "done" },
        { type: "text" as const, text: "answer" },
      ],
    };
    render(<AssistantMessage message={message} status="streaming" {...chipProps} />);
    const chip = screen.getByTestId("reasoning-chip");
    expect(chip).toHaveAttribute("data-state", "collapsed");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("Thought for 3s");
    expect(screen.queryByTestId("reasoning-chip-body")).not.toBeInTheDocument();
  });

  test("aborted half-chip keeps text behind a Stopped header (S-chip-07)", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [{ type: "reasoning" as const, text: "half a thought", state: "streaming" }],
    };
    render(<AssistantMessage message={message} status="ready" {...chipProps} />);
    const chip = screen.getByTestId("reasoning-chip");
    expect(chip).toHaveAttribute("data-state", "collapsed");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent(
      "Stopped — thought for 3s",
    );
  });

  test("zero-delta reasoning part renders no chip (S-chip-08 ghost suppression)", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        { type: "reasoning" as const, text: "", state: "done" },
        { type: "text" as const, text: "answer" },
      ],
    };
    render(<AssistantMessage message={message} status="streaming" {...chipProps} />);
    expect(screen.queryByTestId("reasoning-chip")).not.toBeInTheDocument();
  });

  test("whitespace-streamed chip is kept, not removed after the fact (S-chip-08)", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [{ type: "reasoning" as const, text: "  \n ", state: "done" }],
    };
    render(<AssistantMessage message={message} status="streaming" {...chipProps} />);
    expect(screen.getByTestId("reasoning-chip")).toBeInTheDocument();
  });

  test("chips interleave with tool cards in part order (S-chip-06)", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        { type: "reasoning" as const, text: "round 1", state: "done" },
        {
          type: "tool" as const,
          state: "output-available",
          toolCallId: "tc-1",
          toolName: "list_sec_sections",
          input: {},
          output: {},
        },
        { type: "reasoning" as const, text: "round 2", state: "done" },
        { type: "text" as const, text: "answer" },
      ],
    };
    render(<AssistantMessage message={message} status="streaming" {...chipProps} />);
    const article = screen.getByTestId("assistant-message");
    const rendered = Array.from(
      article.querySelectorAll("[data-testid='reasoning-chip'], [data-testid='tool-card']"),
    );
    expect(rendered.map((el) => el.getAttribute("data-testid"))).toEqual([
      "reasoning-chip",
      "tool-card",
      "reasoning-chip",
    ]);
    // data-round is the chip's 1-based ordinal within the message.
    expect(rendered[0]).toHaveAttribute("data-round", "1");
    expect(rendered[2]).toHaveAttribute("data-round", "2");
  });

  test("user override expands a collapsed chip and shows its full text (S-chip-05)", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        { type: "reasoning" as const, text: "full reasoning text", state: "done" },
        { type: "text" as const, text: "answer" },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        status="streaming"
        {...chipProps}
        chipOverrides={new Map([["a1:0", true]])}
      />,
    );
    const chip = screen.getByTestId("reasoning-chip");
    expect(chip).toHaveAttribute("data-state", "expanded");
    expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("full reasoning text");
  });
});

describe("AssistantMessage — citation rendering", () => {
  const commonMarkText =
    "Analysis shows growth [1] and stability [2].\n\n" +
    '[1]: https://reuters.com/report "Reuters Report"\n' +
    "[2]: https://bloomberg.com/article";

  const commonMarkMsg = {
    id: "a1",
    role: "assistant" as const,
    parts: [{ type: "text" as const, text: commonMarkText }],
  };

  test("CommonMark citations render as RefSup after streaming", () => {
    render(
      <AssistantMessage
        message={commonMarkMsg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    const refSups = screen.getAllByTestId("ref-sup");
    expect(refSups).toHaveLength(2);
    expect(refSups[0]).toHaveAttribute("data-ref-label", "1");
    expect(refSups[1]).toHaveAttribute("data-ref-label", "2");

    expect(screen.getByTestId("sources-block")).toBeInTheDocument();
    expect(screen.getByText("Reuters Report")).toBeInTheDocument();
    expect(screen.getByText("bloomberg.com")).toBeInTheDocument();
  });

  test("no RefSup or Sources block during streaming", () => {
    render(
      <AssistantMessage
        message={commonMarkMsg}
        isLast={true}
        status="streaming"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.queryByTestId("ref-sup")).not.toBeInTheDocument();
    expect(screen.queryByTestId("sources-block")).not.toBeInTheDocument();
  });

  test("fallback format — [N] URL + full-width【N】inline", () => {
    const fallbackText =
      "最新報導顯示成長【1】，Bloomberg 確認趨勢【2】。\n\n" +
      "**References**\n" +
      "[1] https://reuters.com/report\n" +
      "[2] https://bloomberg.com/analysis";

    const fallbackMsg = {
      id: "a2",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: fallbackText }],
    };

    render(
      <AssistantMessage
        message={fallbackMsg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    const refSups = screen.getAllByTestId("ref-sup");
    expect(refSups).toHaveLength(2);

    expect(screen.getByTestId("sources-block")).toBeInTheDocument();
    expect(screen.queryByText("**References**")).not.toBeInTheDocument();
  });

  test("streaming strips definition lines (no flicker)", () => {
    const streamingText = "NVDA 很棒 [1]。\n\n" + '[1]: https://reuters.com/report "Reuters"';

    const msg = {
      id: "a3",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: streamingText }],
    };

    render(
      <AssistantMessage
        message={msg}
        isLast={true}
        status="streaming"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.queryByText(/reuters\.com\/report/)).not.toBeInTheDocument();
    expect(screen.queryByTestId("sources-block")).not.toBeInTheDocument();
  });

  test("bullet-prefixed ref defs render Sources block", () => {
    const bulletText = "NVDA news [1].\n\n" + '- [1]: https://reuters.com/nvda "Reuters NVDA"';

    const msg = {
      id: "a4",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: bulletText }],
    };

    render(
      <AssistantMessage
        message={msg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.getByTestId("sources-block")).toBeInTheDocument();
    expect(screen.queryByText(/- \[1\]/)).not.toBeInTheDocument();
  });

  test("Chinese source header stripped", () => {
    const cnText = "報告內容 [1]。\n\n" + "來源：\n" + '[1]: https://reuters.com/report "Reuters"';

    const msg = {
      id: "a5",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: cnText }],
    };

    render(
      <AssistantMessage
        message={msg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.queryByText("來源：")).not.toBeInTheDocument();
    expect(screen.getByTestId("sources-block")).toBeInTheDocument();
  });
});
