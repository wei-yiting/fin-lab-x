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
    expect(inlineAnchor).toHaveAttribute("rel", "noopener noreferrer");
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

describe("Markdown — URL sanitization (inline body links)", () => {
  test("TC-comp-markdown-xss-01: javascript: URL has href stripped, anchor text preserved", () => {
    // Anchor with empty/stripped href loses the `link` ARIA role, so we locate by text
    // and assert the sanitization invariant directly.
    const text = "Visit [bad site](javascript:alert('xss')) now.";
    render(<Markdown text={text} isStreaming={false} sources={[]} />);

    const anchor = screen.getByText("bad site").closest("a");
    expect(anchor).not.toBeNull();
    expect(anchor!.getAttribute("href") ?? "").not.toMatch(/^javascript:/i);
  });

  test("TC-comp-markdown-xss-02: mailto: URL in inline link is preserved as-is", () => {
    const text = "Contact [mail link](mailto:x@y.com).";
    render(<Markdown text={text} isStreaming={false} sources={[]} />);

    const anchor = screen.getByRole("link", { name: "mail link" });
    expect(anchor).toHaveAttribute("href", "mailto:x@y.com");
  });

  test("TC-comp-markdown-xss-03: safe https link renders with target=_blank + rel noopener noreferrer", () => {
    const text = "Read [safe](https://example.com).";
    render(<Markdown text={text} isStreaming={false} sources={[]} />);

    const anchor = screen.getByRole("link", { name: "safe" });
    expect(anchor).toHaveAttribute("href", "https://example.com");
    expect(anchor).toHaveAttribute("target", "_blank");
    expect(anchor).toHaveAttribute("rel", "noopener noreferrer");
  });

  test("TC-comp-markdown-xss-04: mixed links — javascript: sanitized, others preserved", () => {
    const text =
      "Bad [bad](javascript:alert('xss')), mail [mail link](mailto:x@y.com), safe [safe](https://example.com).";
    render(<Markdown text={text} isStreaming={false} sources={[]} />);

    const badAnchor = screen.getByText("bad").closest("a");
    expect(badAnchor!.getAttribute("href") ?? "").not.toMatch(/^javascript:/i);
    expect(screen.getByRole("link", { name: "mail link" })).toHaveAttribute(
      "href",
      "mailto:x@y.com",
    );
    expect(screen.getByRole("link", { name: "safe" })).toHaveAttribute(
      "href",
      "https://example.com",
    );
  });
});
