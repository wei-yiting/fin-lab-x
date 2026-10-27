import type { SSEStreamFixture } from "./types";

const SEC_ID = "sec://0000320193-24-000123/1a#12";

// Tool output is a JSON string on the production wire — mirror that here.
const secOutput = JSON.stringify({
  fiscal_year: 2024,
  fiscal_year_end: "2024-09-28",
  fiscal_year_source: "latest",
  total_chunks: 1,
  groups: [
    {
      ticker: "AAPL",
      fiscal_year: 2024,
      item: "1A",
      chunks: [
        {
          source: SEC_ID,
          title: "AAPL FY2024 10-K · Item 1A · Supply chain",
          subsection: "Supply chain",
          content:
            "The Company depends on component and product manufacturing and logistical services provided by outsourcing partners, many of which are located outside of the U.S. Substantially all of the Company's manufacturing is performed in whole or in part by outsourcing partners located primarily in China mainland, India, Japan, South Korea, Taiwan and Vietnam, and a significant concentration of this manufacturing is currently performed by a small number of outsourcing partners, often in single locations.",
          score: 0.8123,
        },
      ],
    },
  ],
});

const sqlOutput = JSON.stringify({
  status: "ok",
  question: "AAPL annual gross margin, fiscal years 2022-2024",
  sql: "SELECT ticker, fiscal_year, gross_margin_pct, gross_profit_usd, total_revenue_usd FROM annual_metrics WHERE ticker = 'AAPL' ORDER BY fiscal_year DESC",
  columns: ["ticker", "fiscal_year", "gross_margin_pct", "gross_profit_usd", "total_revenue_usd"],
  rows: [
    {
      ticker: "AAPL",
      fiscal_year: 2024,
      gross_margin_pct: 46.206,
      gross_profit_usd: 180683000000,
      total_revenue_usd: 391035000000,
    },
    {
      ticker: "AAPL",
      fiscal_year: 2023,
      gross_margin_pct: 44.131,
      gross_profit_usd: 169148000000,
      total_revenue_usd: 383285000000,
    },
    {
      ticker: "AAPL",
      fiscal_year: 2022,
      gross_margin_pct: 43.31,
      gross_profit_usd: 170782000000,
      total_revenue_usd: 394328000000,
    },
  ],
  truncated: false,
  attempts: [],
  tables: ["annual_metrics"],
  derivations: [
    {
      column: "gross_margin_pct",
      expression: "gross_profit_usd / total_revenue_usd * 100",
      inputs: ["gross_profit_usd", "total_revenue_usd"],
    },
  ],
});

const fixture: SSEStreamFixture = {
  description:
    "SEC chunk + text_to_sql result + web citation + one unresolved ID, cited as expandable blocks",
  scenarios: ["DEV-229"],
  chunks: [
    { data: { type: "start", messageId: "asst-evidence-1" } },
    {
      data: {
        type: "tool-input-available",
        toolCallId: "call_sec",
        toolName: "sec_filing_search",
        input: { query: "supply chain concentration", ticker: "AAPL" },
      },
    },
    {
      delayMs: 100,
      data: { type: "tool-output-available", toolCallId: "call_sec", output: secOutput },
    },
    {
      data: {
        type: "tool-input-available",
        toolCallId: "call_sql",
        toolName: "text_to_sql",
        input: { question: "AAPL annual gross margin, fiscal years 2022-2024" },
      },
    },
    {
      delayMs: 100,
      data: { type: "tool-output-available", toolCallId: "call_sql", output: sqlOutput },
    },
    { data: { type: "text-start", id: "t1" } },
    {
      data: {
        type: "text-delta",
        id: "t1",
        delta:
          "Apple's FY2024 10-K (fiscal year ended 2024-09-28) says most manufacturing is done by outsourcing partners concentrated in Asia [1]. ",
      },
    },
    {
      data: {
        type: "text-delta",
        id: "t1",
        delta:
          "Gross margin still rose to 46.2% in FY2024, from 44.1% in FY2023 and 43.3% in FY2022 [2]. Analysts tie part of that to services mix [3]. Supplier diversification is also underway [4].\n\n",
      },
    },
    {
      data: {
        type: "text-delta",
        id: "t1",
        delta: `[1]: ${SEC_ID}\n[2]: sql://call_sql\n[3]: https://reuters.com/apple-margins "Reuters: Apple margins"\n[4]: sec://0000320193-24-000123/7#4\n`,
      },
    },
    { data: { type: "text-end", id: "t1" } },
    { data: { type: "finish" } },
  ],
};
export default fixture;
