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
        isStreaming={false}
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
          type: "tool-yfinance" as const,
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
        isStreaming={false}
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
          type: "tool-a" as const,
          state: "output-available",
          toolCallId: "tc-A",
          toolName: "a",
          input: {},
          output: {},
        },
        {
          type: "tool-b" as const,
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
        isStreaming={false}
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
          type: "tool-x" as const,
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
        isStreaming={false}
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
          type: "tool-x" as const,
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
        isStreaming={false}
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
          type: "tool-x" as const,
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
        isStreaming={false}
        abortedTools={new Set(["tc-done"])}
        toolProgress={{}}
      />,
    );
    expect(screen.getByTestId("tool-card")).toHaveAttribute("data-tool-state", "output-available");
  });

  // Proves the `interrupted` fallback in AssistantMessage's isAborted check
  // in isolation: a running tool resolves to "aborted" even when its id was
  // never added to abortedTools, e.g. because it arrived after ChatPanel's
  // click-time closure snapshot was already taken (M-2.1).
  test('input-available tool with interrupted=true and empty abortedTools → ToolCard data-tool-state="aborted"', () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        {
          type: "tool-x" as const,
          state: "input-available",
          toolCallId: "tc-interrupted-fallback",
          toolName: "x",
          input: {},
        },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isStreaming={false}
        interrupted
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.getByTestId("tool-card")).toHaveAttribute("data-tool-state", "aborted");
  });
});

// The memo comparator ignores toolProgress's identity and compares only the
// entries this message's tool parts read. The staleness risk of that
// special-case is missing a real update, so lock the positive path: a new
// progress value for this message's own toolCallId must re-render even when
// every other prop keeps its reference across the rerender.
describe("AssistantMessage — toolProgress memo comparator", () => {
  test("progress update for own toolCallId re-renders through the comparator", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        {
          type: "tool-x" as const,
          state: "input-available",
          toolCallId: "tc-progress",
          toolName: "x",
          input: {},
        },
      ],
    };
    const abortedTools = new Set<string>();
    const { rerender } = render(
      <AssistantMessage
        message={message}
        isStreaming={false}
        abortedTools={abortedTools}
        toolProgress={{}}
      />,
    );
    rerender(
      <AssistantMessage
        message={message}
        isStreaming={false}
        abortedTools={abortedTools}
        toolProgress={{ "tc-progress": "fetching page 2..." }}
      />,
    );
    expect(screen.getByTestId("tool-card")).toHaveTextContent("fetching page 2...");
  });
});

// The last-message + status=ready visibility rule (S-regen-02) is derived in
// MessageList and covered in MessageList.test.tsx; this component only sees
// the result — an onRegenerate prop that is present exactly when the button
// may show.
describe("AssistantMessage — RegenerateButton visibility", () => {
  const baseMsg = {
    id: "a1",
    role: "assistant" as const,
    parts: [{ type: "text" as const, text: "done" }],
  };

  test("onRegenerate provided → button visible", () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isStreaming={false}
        abortedTools={new Set()}
        toolProgress={{}}
        onRegenerate={vi.fn()}
      />,
    );
    expect(screen.getByTestId("regenerate-btn")).toBeInTheDocument();
  });

  test("onRegenerate omitted (non-last message, or transcript not ready) → hidden", () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isStreaming={false}
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.queryByTestId("regenerate-btn")).not.toBeInTheDocument();
  });

  // Regenerate replays the turn from the backend's checkpoint, which only
  // holds a finalized AIMessage for turns that ran to completion — the
  // turn-level `interrupted` flag gates the button off even when every part
  // in the message already reads "done", the case an abort mid-flight
  // (streaming part states) does not cover.
  test("interrupted turn hides Regenerate even when every part reads complete", () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isStreaming={false}
        interrupted
        abortedTools={new Set()}
        toolProgress={{}}
        onRegenerate={vi.fn()}
      />,
    );
    expect(screen.queryByTestId("regenerate-btn")).not.toBeInTheDocument();
  });
});

describe("AssistantMessage — reasoning chips", () => {
  const chipProps = {
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
    render(<AssistantMessage message={message} isStreaming={true} {...chipProps} />);
    const chip = screen.getByTestId("reasoning-chip");
    expect(chip).toHaveAttribute("data-state", "streaming");
    expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("分析 10-K 中");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("思考中…");
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
    render(<AssistantMessage message={message} isStreaming={true} {...chipProps} />);
    const chip = screen.getByTestId("reasoning-chip");
    expect(chip).toHaveAttribute("data-state", "collapsed");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("思考了 3 秒");
    expect(screen.queryByTestId("reasoning-chip-body")).not.toBeInTheDocument();
  });

  test("aborted half-chip keeps text behind a Stopped header", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [{ type: "reasoning" as const, text: "half a thought", state: "streaming" }],
    };
    render(<AssistantMessage message={message} isStreaming={false} {...chipProps} />);
    const chip = screen.getByTestId("reasoning-chip");
    expect(chip).toHaveAttribute("data-state", "collapsed");
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("已停止 — 思考了 3 秒");
  });

  test("zero-delta reasoning part renders no chip", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        { type: "reasoning" as const, text: "", state: "done" },
        { type: "text" as const, text: "answer" },
      ],
    };
    render(<AssistantMessage message={message} isStreaming={true} {...chipProps} />);
    expect(screen.queryByTestId("reasoning-chip")).not.toBeInTheDocument();
  });

  test("whitespace-streamed chip is kept, not removed after the fact", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [{ type: "reasoning" as const, text: "  \n ", state: "done" }],
    };
    render(<AssistantMessage message={message} isStreaming={true} {...chipProps} />);
    expect(screen.getByTestId("reasoning-chip")).toBeInTheDocument();
  });

  test("chips interleave with tool cards in part order", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        { type: "reasoning" as const, text: "round 1", state: "done" },
        {
          type: "tool-list_sec_sections" as const,
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
    render(<AssistantMessage message={message} isStreaming={true} {...chipProps} />);
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

  test("user override expands a collapsed chip and shows its full text", () => {
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
        isStreaming={true}
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
        isStreaming={false}
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
        isStreaming={true}
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
        isStreaming={false}
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    const refSups = screen.getAllByTestId("ref-sup");
    expect(refSups).toHaveLength(2);

    expect(screen.getByTestId("sources-block")).toBeInTheDocument();
    expect(screen.queryByText("**References**")).not.toBeInTheDocument();
  });

  // CommonMark accepts up to three leading spaces on a link reference
  // definition, so the streaming strip must cover indented definitions too —
  // otherwise the raw definition flashes on screen while the renderer paints
  // nothing.
  test.each([
    ["column-zero", ""],
    ["three-space indented", "   "],
  ])("streaming strips %s definition lines (no flicker)", (_label, indent) => {
    const streamingText =
      "NVDA 很棒 [1]。\n\n" + `${indent}[1]: https://reuters.com/report "Reuters"`;

    const msg = {
      id: "a3",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: streamingText }],
    };

    render(
      <AssistantMessage
        message={msg}
        isStreaming={true}
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
        isStreaming={false}
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
        isStreaming={false}
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );
    expect(screen.queryByText("來源：")).not.toBeInTheDocument();
    expect(screen.getByTestId("sources-block")).toBeInTheDocument();
  });
});
