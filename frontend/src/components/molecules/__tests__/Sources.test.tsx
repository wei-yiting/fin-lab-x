import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Sources } from "../Sources";

describe("Sources molecule", () => {
  test("TC-comp-sources-01: renders entries with title when present, hostname when missing", () => {
    const extractedSources = [
      { label: "1", url: "https://reuters.com/x", title: "Reuters X", hostname: "reuters.com" },
      { label: "2", url: "https://bloomberg.com/y", title: undefined, hostname: "bloomberg.com" },
    ];
    render(<Sources sources={extractedSources} />);

    expect(screen.getByText("Reuters X")).toBeInTheDocument();
    expect(screen.getByText("bloomberg.com")).toBeInTheDocument();
  });

  test('TC-comp-sources-01: SourceLink has anchor id="src-{label}" for in-page jump', () => {
    const extractedSources = [{ label: "3", url: "https://x.com", title: "X", hostname: "x.com" }];
    render(<Sources sources={extractedSources} />);
    expect(screen.getByTestId("source-link")).toHaveAttribute("id", "src-3");
  });

  test("TC-comp-sources-02: source with javascript: URL is filtered out, block does not render", () => {
    const evilSources = [{ label: "1", url: "javascript:alert(1)", title: "Evil", hostname: "" }];
    render(<Sources sources={evilSources} />);

    expect(screen.queryByTestId("sources-block")).not.toBeInTheDocument();
  });
});
