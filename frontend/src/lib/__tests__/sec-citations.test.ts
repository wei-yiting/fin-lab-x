import { describe, test, expect } from "vitest";
import { buildSecEvidenceRegistry, resolveSecSources } from "../sec-citations";
import type { SourceRef } from "@/models";

const TOOL_OUTPUT = {
  language_directive_pre: "[LANGUAGE DIRECTIVE] ...",
  fiscal_year: 2024,
  fiscal_year_source: "latest",
  total_chunks: 2,
  groups: [
    {
      ticker: "AAPL",
      fiscal_year: 2024,
      item: "Item 1A",
      prelude:
        "Excerpts from AAPL FY2024 10-K, Item 1A (Risk Factors) — 2 passage(s) in document order.",
      edgar_url:
        "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
      chunks: [
        {
          n: 1,
          source: "sec://0000320193-24-000123/1a#5",
          title: "AAPL FY2024 10-K · Item 1A · Competition",
          subsection: "Competition",
          content: "Competition is intense.",
          score: 0.83,
        },
        {
          n: 2,
          source: "sec://0000320193-24-000123/1a#12",
          title: "AAPL FY2024 10-K · Item 1A",
          content: "Flat item chunk.",
          score: 0.7,
        },
      ],
    },
  ],
  language_directive_post: "[LANGUAGE DIRECTIVE] ...",
};

function toolPart(output: unknown, overrides: Record<string, unknown> = {}) {
  return {
    type: "tool-sec_filing_search",
    toolCallId: "call-1",
    state: "output-available",
    input: { query: "q", ticker: "AAPL" },
    output,
    ...overrides,
  };
}

describe("buildSecEvidenceRegistry", () => {
  test("indexes chunks by stable ID from an object output", () => {
    const registry = buildSecEvidenceRegistry([toolPart(TOOL_OUTPUT)]);
    const info = registry.get("sec://0000320193-24-000123/1a#5");
    expect(info).toBeDefined();
    expect(info!.ticker).toBe("AAPL");
    expect(info!.fiscalYear).toBe(2024);
    expect(info!.item).toBe("Item 1A");
    expect(info!.subsection).toBe("Competition");
    expect(info!.excerpt).toBe("Competition is intense.");
    expect(info!.title).toBe("AAPL FY2024 10-K · Item 1A · Competition");
    expect(info!.edgarUrl).toContain("https://www.sec.gov/");
  });

  test("parses a JSON-string output (production wire shape)", () => {
    const registry = buildSecEvidenceRegistry([toolPart(JSON.stringify(TOOL_OUTPUT))]);
    expect(registry.get("sec://0000320193-24-000123/1a#12")?.excerpt).toBe("Flat item chunk.");
  });

  test("subsection stays undefined for FlatItem chunks", () => {
    const registry = buildSecEvidenceRegistry([toolPart(TOOL_OUTPUT)]);
    expect(registry.get("sec://0000320193-24-000123/1a#12")?.subsection).toBeUndefined();
  });

  test("ignores parts from other tools, non-finished states, and bad JSON", () => {
    const parts = [
      toolPart(TOOL_OUTPUT, { type: "tool-finnhub_stock_quote" }),
      toolPart(TOOL_OUTPUT, { state: "input-available" }),
      toolPart("not json {"),
      { type: "text", text: "hello" },
    ];
    expect(buildSecEvidenceRegistry(parts).size).toBe(0);
  });

  test("accepts dynamic-tool parts named sec_filing_search", () => {
    const parts = [toolPart(TOOL_OUTPUT, { type: "dynamic-tool", toolName: "sec_filing_search" })];
    expect(buildSecEvidenceRegistry(parts).size).toBe(2);
  });
});

describe("resolveSecSources", () => {
  const registry = buildSecEvidenceRegistry([toolPart(TOOL_OUTPUT)]);

  test("resolves a sec:// ref against the registry; metadata overrides model title", () => {
    const sources: SourceRef[] = [
      {
        label: "1",
        url: "sec://0000320193-24-000123/1a#5",
        title: "Model-written title to ignore",
        hostname: "",
      },
    ];
    const resolved = resolveSecSources(sources, registry);
    expect(resolved).toHaveLength(1);
    expect(resolved[0].title).toBe("AAPL FY2024 10-K · Item 1A · Competition");
    expect(resolved[0].url).toContain("https://www.sec.gov/");
    expect(resolved[0].sec?.excerpt).toBe("Competition is intense.");
  });

  test("drops citations whose ID is not in any tool result (fabricated ID)", () => {
    const sources: SourceRef[] = [
      { label: "1", url: "sec://0000000000-00-000000/7#99", hostname: "" },
    ];
    expect(resolveSecSources(sources, registry)).toHaveLength(0);
  });

  test("passes non-sec web sources through untouched", () => {
    const web: SourceRef = {
      label: "2",
      url: "https://reuters.com/x",
      title: "Reuters",
      hostname: "reuters.com",
    };
    const resolved = resolveSecSources([web], registry);
    expect(resolved).toEqual([web]);
  });

  test("falls back to an in-page anchor when the group has no EDGAR URL", () => {
    const noUrl = JSON.parse(JSON.stringify(TOOL_OUTPUT));
    noUrl.groups[0].edgar_url = null;
    const reg = buildSecEvidenceRegistry([toolPart(noUrl)]);
    const resolved = resolveSecSources(
      [{ label: "3", url: "sec://0000320193-24-000123/1a#5", hostname: "" }],
      reg,
    );
    expect(resolved[0].url).toBe("#src-3");
    expect(resolved[0].sec?.edgarUrl).toBeUndefined();
  });
});
