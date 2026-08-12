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
  test("javascript: URL has href stripped, anchor text preserved", () => {
    // Anchor with empty/stripped href loses the `link` ARIA role, so we locate by text
    // and assert the sanitization invariant directly.
    const text = "Visit [bad site](javascript:alert('xss')) now.";
    render(<Markdown text={text} isStreaming={false} sources={[]} />);

    const anchor = screen.getByText("bad site").closest("a");
    expect(anchor).not.toBeNull();
    expect(anchor!.getAttribute("href") ?? "").not.toMatch(/^javascript:/i);
  });

  test("mailto: URL in inline link is preserved as-is", () => {
    const text = "Contact [mail link](mailto:x@y.com).";
    render(<Markdown text={text} isStreaming={false} sources={[]} />);

    const anchor = screen.getByRole("link", { name: "mail link" });
    expect(anchor).toHaveAttribute("href", "mailto:x@y.com");
  });

  test("safe https link renders with target=_blank + rel noopener noreferrer", () => {
    const text = "Read [safe](https://example.com).";
    render(<Markdown text={text} isStreaming={false} sources={[]} />);

    const anchor = screen.getByRole("link", { name: "safe" });
    expect(anchor).toHaveAttribute("href", "https://example.com");
    expect(anchor).toHaveAttribute("target", "_blank");
    expect(anchor).toHaveAttribute("rel", "noopener noreferrer");
  });

  test("mixed links — javascript: sanitized, others preserved", () => {
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

// While streaming, the text is rendered as separately-memoized top-level
// blocks so that an arriving delta only re-parses the block still being
// written. Splitting is where that optimization can go wrong, so these lock
// the structures a naive blank-line split would tear apart, plus the
// property that matters to the reader: streaming and completed renders show
// the same content.
describe("Markdown — streaming block splitting", () => {
  test("fenced code block survives its own internal blank lines", () => {
    const text = "Intro.\n\n```python\ndef a():\n\n    return 1\n```\n\nAfter.";

    render(<Markdown text={text} isStreaming sources={[]} />);

    // One <pre>, not one per side of the blank line.
    const blocks = document.querySelectorAll("pre");
    expect(blocks).toHaveLength(1);
    expect(blocks[0].textContent).toContain("def a():");
    expect(blocks[0].textContent).toContain("return 1");
  });

  test("GFM table stays a single table", () => {
    const text =
      "Comparison:\n\n| Metric | NVDA | AMD |\n| --- | --- | --- |\n| P/E | 32.1 | 122.3 |\n| P/S | 20.2 | 19.1 |\n\nDone.";

    render(<Markdown text={text} isStreaming sources={[]} />);

    expect(document.querySelectorAll("table")).toHaveLength(1);
    expect(screen.getByRole("columnheader", { name: "Metric" })).toBeInTheDocument();
    expect(document.querySelectorAll("tbody tr")).toHaveLength(2);
  });

  test("loose list (blank lines between items) stays one list", () => {
    const text = "Points:\n\n- first\n\n- second\n\n- third";

    render(<Markdown text={text} isStreaming sources={[]} />);

    expect(document.querySelectorAll("ul")).toHaveLength(1);
    expect(document.querySelectorAll("li")).toHaveLength(3);
  });

  test("streaming render produces the same visible structure as the completed render", () => {
    const text =
      "# Heading\n\nA paragraph with **bold** text.\n\n- item one\n- item two\n\n> a quote\n\nFinal words.";

    // Element tag + trimmed text, which is what a reader perceives. Raw
    // textContent would not match: rendering the document as one pass leaves
    // the newline between two block elements as a text node, while rendering
    // block-by-block does not. Both display identically — block elements
    // already break the line — so the difference is not a regression.
    const outline = (root: HTMLElement) =>
      Array.from(root.querySelectorAll("h1,h2,h3,p,li,blockquote,pre,table")).map(
        (el) => `${el.tagName}:${(el.textContent ?? "").trim()}`,
      );

    const streaming = render(<Markdown text={text} isStreaming sources={[]} />);
    const streamedOutline = outline(streaming.container);
    const streamedText = streaming.container.textContent ?? "";
    streaming.unmount();

    const complete = render(<Markdown text={text} isStreaming={false} sources={[]} />);

    expect(streamedOutline).toEqual(outline(complete.container));
    // The cursor sentinel must always be swapped for the real element.
    expect(streamedText).not.toContain("CURSOR");
  });

  test("cursor renders once, at the end of the last block", () => {
    const text = "First para.\n\nSecond para.";

    const { container } = render(<Markdown text={text} isStreaming sources={[]} />);

    const cursors = container.querySelectorAll('[data-testid="cursor"]');
    expect(cursors).toHaveLength(1);
    const paragraphs = container.querySelectorAll("p");
    expect(paragraphs[paragraphs.length - 1].contains(cursors[0])).toBe(true);
  });
});
