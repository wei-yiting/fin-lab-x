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

describe("AssistantMessage — SEC citation resolution", () => {
  const SEC_OUTPUT = JSON.stringify({
    language_directive_pre: "x",
    fiscal_year: 2024,
    fiscal_year_source: "latest",
    total_chunks: 1,
    groups: [
      {
        ticker: "AAPL",
        fiscal_year: 2024,
        item: "Item 1A",
        prelude: "Excerpts from AAPL FY2024 10-K, Item 1A — 1 passage(s).",
        edgar_url: "https://www.sec.gov/Archives/edgar/data/320193/x/aapl.htm",
        chunks: [
          {
            n: 1,
            source: "sec://0000320193-24-000123/1a#5",
            title: "AAPL FY2024 10-K · Item 1A · Competition",
            subsection: "Competition",
            content: "Competition is intense.",
            score: 0.83,
          },
        ],
      },
    ],
    language_directive_post: "x",
  });

  const secToolPart = {
    type: "tool-sec_filing_search" as const,
    state: "output-available",
    toolCallId: "tc-sec-1",
    input: { query: "competition", ticker: "AAPL" },
    output: SEC_OUTPUT,
  };

  test("resolves [N] against the same message's tool result into a SEC source entry", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        secToolPart,
        {
          type: "text" as const,
          text: "Competition is fierce [1].\n\n[1]: sec://0000320193-24-000123/1a#5",
        },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isLast
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );

    expect(screen.getByTestId("ref-sup")).toHaveAttribute("data-ref-label", "1");
    expect(screen.getByTestId("sources-block")).toBeInTheDocument();
    expect(screen.getByTestId("sec-source-group")).toHaveTextContent("AAPL FY2024 10-K · Item 1A");
    expect(screen.getByText("Competition is intense.")).toBeInTheDocument();
  });

  test("drops a citation whose sec ID does not exist in any tool result", () => {
    const message = {
      id: "a1",
      role: "assistant" as const,
      parts: [
        secToolPart,
        {
          type: "text" as const,
          text: "Fabricated claim [1].\n\n[1]: sec://9999999999-99-999999/7#42",
        },
      ],
    };
    render(
      <AssistantMessage
        message={message}
        isLast
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />,
    );

    expect(screen.queryByTestId("sources-block")).not.toBeInTheDocument();
    expect(screen.queryByTestId("ref-sup")).not.toBeInTheDocument();
  });
});
