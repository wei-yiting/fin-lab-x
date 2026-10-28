import { describe, test, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AssistantMessage } from "../AssistantMessage";
import { LocaleContext } from "@/lib/locale";
import { zhTW } from "@/lib/copy";

const SEC_ID = "sec://0000320193-24-000123/1a#12";
const CHUNK_TEXT =
  "The Company depends on component and product manufacturing by outsourcing partners.";

// Tool output travels as a JSON string on the wire.
const secPart = {
  type: "tool-sec_filing_search" as const,
  state: "output-available",
  toolCallId: "call_sec",
  toolName: "sec_filing_search",
  input: {},
  output: JSON.stringify({
    fiscal_year: 2024,
    fiscal_year_end: "2024-09-28",
    groups: [
      {
        ticker: "AAPL",
        fiscal_year: 2024,
        item: "1A",
        chunks: [
          {
            source: SEC_ID,
            title: "AAPL FY2024 10-K · Item 1A · Supply chain",
            content: CHUNK_TEXT,
            score: 0.8123,
          },
        ],
      },
    ],
  }),
};

function sqlPart(toolCallId: string, extra: Record<string, unknown> = {}) {
  return {
    type: "tool-company_fundamentals_query" as const,
    state: "output-available",
    toolCallId,
    toolName: "company_fundamentals_query",
    input: {},
    output: {
      status: "ok",
      question: "AAPL gross margin FY2023-FY2024",
      sql: "SELECT …",
      columns: [
        "ticker",
        "fiscal_year",
        "gross_margin_pct",
        "gross_profit_usd",
        "total_revenue_usd",
      ],
      rows: [
        {
          ticker: "AAPL",
          fiscal_year: 2024,
          gross_margin_pct: 46.206,
          gross_profit_usd: 180_683_000_000,
          total_revenue_usd: 391_035_000_000,
        },
        {
          ticker: "AAPL",
          fiscal_year: 2023,
          gross_margin_pct: 44.131,
          gross_profit_usd: 169_148_000_000,
          total_revenue_usd: 383_285_000_000,
        },
      ],
      truncated: false,
      attempts: [],
      ...extra,
    },
  };
}

const DERIVATIONS = [
  {
    column: "gross_margin_pct",
    expression: "gross_profit_usd / total_revenue_usd * 100",
    inputs: ["gross_profit_usd", "total_revenue_usd"],
  },
];

function renderMessage(parts: Record<string, unknown>[], text: string) {
  const message = {
    id: "m1",
    role: "assistant" as const,
    parts: [...parts, { type: "text" as const, text }],
  };
  return render(
    <AssistantMessage
      message={message}
      isStreaming={false}
      abortedTools={new Set()}
      toolProgress={{}}
    />,
  );
}

const entry = (label: string) =>
  screen
    .getAllByTestId("citation-block")
    .find((el) => el.getAttribute("data-source-label") === label)!;

describe("AssistantMessage — SEC citation blocks", () => {
  const text = `Apple relies on outsourcing partners [1].\n\n[1]: ${SEC_ID}`;

  test("lists the chunk by its title, collapsed until opened", async () => {
    renderMessage([secPart], text);

    const block = entry("1");
    expect(
      within(block).getByText("AAPL FY2024 10-K · Item 1A · Supply chain"),
    ).toBeInTheDocument();
    expect(screen.queryByText(CHUNK_TEXT)).not.toBeInTheDocument();

    await userEvent.click(within(block).getByRole("button"));

    expect(within(block).getByText(CHUNK_TEXT)).toBeInTheDocument();
    expect(within(block).getByText(/FY2024 \(fiscal year ended 2024-09-28\)/)).toBeInTheDocument();
  });

  test("header toggles the block closed again", async () => {
    renderMessage([secPart], text);
    const header = within(entry("1")).getByRole("button");

    await userEvent.click(header);
    expect(header).toHaveAttribute("aria-expanded", "true");
    await userEvent.click(header);

    expect(header).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText(CHUNK_TEXT)).not.toBeInTheDocument();
  });

  test("clicking the inline [N] marker opens its block", async () => {
    renderMessage([secPart], text);

    await userEvent.click(screen.getByRole("button", { name: "Show source 1" }));

    expect(within(entry("1")).getByText(CHUNK_TEXT)).toBeInTheDocument();
  });

  test("an ID matching no tool result says so instead of disappearing", () => {
    renderMessage([secPart], `Made-up claim [1].\n\n[1]: sec://0000000000-00-000000/7#4`);

    expect(
      within(entry("1")).getByText("No matching retrieved result for this citation"),
    ).toBeInTheDocument();
  });
});

describe("AssistantMessage — company_fundamentals_query citation blocks", () => {
  const text = "Apple's FY2024 gross margin was 46.2% [1].\n\n[1]: sql://call_sql";

  test("shows provenance, formula, raw values and per-row substitution", async () => {
    renderMessage(
      [sqlPart("call_sql", { tables: ["annual_metrics"], derivations: DERIVATIONS })],
      text,
    );
    const block = entry("1");

    await userEvent.click(within(block).getByRole("button"));

    expect(
      within(block).getByText(/yfinance → FinLab-X DuckDB fundamentals store/),
    ).toBeInTheDocument();
    expect(within(block).getByText(/annual_metrics/)).toBeInTheDocument();
    expect(
      within(block).getByText("gross_margin_pct = gross_profit_usd ÷ total_revenue_usd × 100"),
    ).toBeInTheDocument();
    expect(within(block).getByRole("table")).toHaveTextContent("$391.04B");
    expect(
      within(block).getByText("AAPL · 2024: 46.2% = $180.68B ÷ $391.04B × 100"),
    ).toBeInTheDocument();
    expect(within(block).queryByText(/SELECT/)).not.toBeInTheDocument();
  });

  test("without derivations it falls back to the result table alone", async () => {
    renderMessage([sqlPart("call_sql")], text);
    const block = entry("1");

    await userEvent.click(within(block).getByRole("button"));

    expect(within(block).getByRole("table")).toHaveTextContent("44.1%");
    expect(within(block).queryByTestId("citation-substitution")).not.toBeInTheDocument();
  });

  test("a failed query is not citable", () => {
    renderMessage([sqlPart("call_sql", { status: "failed", rows: [] })], text);

    expect(
      within(entry("1")).getByText("No matching retrieved result for this citation"),
    ).toBeInTheDocument();
  });

  test("labels follow the zh-TW UI language", async () => {
    const message = {
      id: "m1",
      role: "assistant" as const,
      parts: [sqlPart("call_sql", { derivations: DERIVATIONS }), { type: "text" as const, text }],
    };
    render(
      <LocaleContext.Provider value={{ locale: "zh-TW", copy: zhTW, setLocale: () => {} }}>
        <AssistantMessage
          message={message}
          isStreaming={false}
          abortedTools={new Set()}
          toolProgress={{}}
        />
      </LocaleContext.Provider>,
    );

    await userEvent.click(within(entry("1")).getByRole("button"));

    expect(screen.getByText("公式")).toBeInTheDocument();
    expect(screen.getByText("代入")).toBeInTheDocument();
  });
});

describe("AssistantMessage — mixed citation list", () => {
  test("SEC, SQL and web citations share one list in [N] order", () => {
    const text =
      "Risk [1], margin [2], news [3].\n\n" +
      `[1]: ${SEC_ID}\n` +
      "[2]: sql://call_sql\n" +
      '[3]: https://reuters.com/apple "Reuters on Apple"';
    renderMessage([secPart, sqlPart("call_sql")], text);

    const sources = within(screen.getByTestId("sources-block"));
    const labels = sources
      .getAllByRole("listitem")
      .map((li) => li.getAttribute("data-source-label"));
    expect(labels).toEqual(["1", "2", "3"]);
    expect(sources.getByRole("link", { name: /Reuters on Apple/ })).toHaveAttribute(
      "href",
      "https://reuters.com/apple",
    );
  });

  test("a web [N] marker still opens the page", () => {
    renderMessage([], 'News [1].\n\n[1]: https://reuters.com/apple "Reuters"');

    expect(within(screen.getByTestId("ref-sup")).getByRole("link")).toHaveAttribute(
      "href",
      "https://reuters.com/apple",
    );
  });
});
