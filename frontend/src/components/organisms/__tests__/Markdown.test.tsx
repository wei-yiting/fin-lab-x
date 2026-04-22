import { describe, test, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { Markdown } from "../Markdown";

describe("Markdown — citation vs inline link disambiguation", () => {
  test('inline link [3](url) renders as normal <a> even when a source with label "3" exists', () => {
    const sources = [
      { label: "1", url: "https://reuters.com/a", hostname: "reuters.com" },
      { label: "3", url: "https://official-source.com/article", hostname: "official-source.com" },
    ];
    const text =
      "See [3](https://blog.example.com/top-10) for ranking.\n\n" + "[1]: #src-1\n" + "[3]: #src-3";

    render(<Markdown text={text} isStreaming={false} sources={sources} />);

    // The inline link should NOT be rewritten to a RefSup — it must render as <a>
    const inlineAnchor = screen.getByRole("link", { name: "3" });
    expect(inlineAnchor).toHaveAttribute("href", "https://blog.example.com/top-10");
    expect(inlineAnchor).toHaveAttribute("target", "_blank");
    expect(inlineAnchor.getAttribute("rel")).toContain("noopener");
  });

  test("reference-style [1] with matching source renders as RefSup with source URL", () => {
    const sources = [
      { label: "1", url: "https://reuters.com/real-article", hostname: "reuters.com" },
    ];
    const text = "Growth [1].\n\n[1]: #src-1";

    render(<Markdown text={text} isStreaming={false} sources={sources} />);

    const refSup = screen.getByTestId("ref-sup");
    expect(refSup).toHaveAttribute("data-ref-label", "1");
    expect(within(refSup).getByRole("link")).toHaveAttribute(
      "href",
      "https://reuters.com/real-article",
    );
  });
});
