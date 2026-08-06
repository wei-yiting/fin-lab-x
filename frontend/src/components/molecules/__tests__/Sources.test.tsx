import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Sources } from "../Sources";

describe("Sources molecule", () => {
  test("renders entries with title when present, hostname when missing", () => {
    const extractedSources = [
      { label: "1", url: "https://reuters.com/x", title: "Reuters X", hostname: "reuters.com" },
      { label: "2", url: "https://bloomberg.com/y", title: undefined, hostname: "bloomberg.com" },
    ];
    render(<Sources sources={extractedSources} />);

    expect(screen.getByText("Reuters X")).toBeInTheDocument();
    expect(screen.getByText("bloomberg.com")).toBeInTheDocument();
  });

  test('SourceLink has anchor id="src-{label}" for in-page jump', () => {
    const extractedSources = [{ label: "3", url: "https://x.com", title: "X", hostname: "x.com" }];
    render(<Sources sources={extractedSources} />);
    expect(screen.getByTestId("source-link")).toHaveAttribute("id", "src-3");
  });

  test("source with javascript: URL is filtered out, block does not render", () => {
    const evilSources = [{ label: "1", url: "javascript:alert(1)", title: "Evil", hostname: "" }];
    render(<Sources sources={evilSources} />);

    expect(screen.queryByTestId("sources-block")).not.toBeInTheDocument();
  });
});

describe("Sources — SEC evidence entries", () => {
  const sec = (label: string, over: Record<string, unknown> = {}) => ({
    label,
    url: "https://www.sec.gov/Archives/edgar/data/320193/x/aapl.htm",
    title: `AAPL FY2024 10-K · Item 1A`,
    hostname: "www.sec.gov",
    sec: {
      id: `sec://0000320193-24-000123/1a#${label}`,
      ticker: "AAPL",
      fiscalYear: 2024,
      item: "Item 1A",
      subsection: "Competition",
      title: "AAPL FY2024 10-K · Item 1A · Competition",
      excerpt: `Excerpt body ${label}`,
      edgarUrl: "https://www.sec.gov/Archives/edgar/data/320193/x/aapl.htm",
      ...over,
    },
  });

  test("aggregates same (ticker, year, item) citations into one group entry", () => {
    render(<Sources sources={[sec("1"), sec("2")]} />);

    const groups = screen.getAllByTestId("sec-source-group");
    expect(groups).toHaveLength(1);
    expect(groups[0]).toHaveTextContent("AAPL FY2024 10-K · Item 1A");
    expect(groups[0]).toHaveTextContent("[1]");
    expect(groups[0]).toHaveTextContent("[2]");
  });

  test("different items produce separate group entries", () => {
    render(<Sources sources={[sec("1"), sec("2", { item: "Item 7", id: "sec://a/7#2" })]} />);
    expect(screen.getAllByTestId("sec-source-group")).toHaveLength(2);
  });

  test("shows expandable chunk excerpts", () => {
    render(<Sources sources={[sec("1")]} />);
    expect(screen.getByText("Excerpt body 1")).toBeInTheDocument();
    expect(screen.getByTestId("sec-source-excerpt")).toBeInTheDocument();
  });

  test("renders the EDGAR filing link", () => {
    render(<Sources sources={[sec("1")]} />);
    const link = screen.getByRole("link", { name: /EDGAR/i });
    expect(link).toHaveAttribute(
      "href",
      "https://www.sec.gov/Archives/edgar/data/320193/x/aapl.htm",
    );
  });

  test("omits the EDGAR link when the group has none", () => {
    render(<Sources sources={[sec("1", { edgarUrl: undefined })]} />);
    expect(screen.queryByRole("link", { name: /EDGAR/i })).not.toBeInTheDocument();
  });

  test("keeps per-label anchors for in-page citation jumps", () => {
    const { container } = render(<Sources sources={[sec("1"), sec("2")]} />);
    expect(container.querySelector("#src-1")).not.toBeNull();
    expect(container.querySelector("#src-2")).not.toBeNull();
  });
});
