import { memo, useMemo, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkParse from "remark-parse";
import { unified } from "unified";
import type { Root } from "mdast";
import type { Components } from "react-markdown";
import { RefSup } from "@/components/atoms/RefSup";
import { Cursor } from "@/components/atoms/Cursor";
import { markdownSourcesPlugin } from "@/lib/markdown-sources";
import { cn } from "@/lib/utils";
import type { ExtractedSources } from "@/models";

// Sentinel that the streaming Markdown renderer appends to the raw text
// so that ReactMarkdown's `p` element override can swap it for a real
// <Cursor /> inline with the final paragraph. Rendering <Cursor/> as a
// sibling of <ReactMarkdown> (the previous approach) put the cursor on
// the next line because ReactMarkdown emits a block <p>.
const CURSOR_MARKER = "⌧CURSOR⌧";

// Module-scope so every render passes the *same* reference — a fresh object
// literal here would defeat the block memoization below.
const MARKDOWN_COMPONENTS: Components = {
  a: ({ href, children, ...props }) => {
    const attrs = props as Record<string, unknown>;
    if (attrs["data-citation"] === "true") {
      const label = attrs["data-source-label"] as string;
      return <RefSup label={label} href={href ?? "#"} />;
    }
    return (
      <a href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    );
  },
  p: ({ children }) => <p>{replaceCursorMarker(children)}</p>,
  li: ({ children }) => <li>{replaceCursorMarker(children)}</li>,
};

// While streaming, citations are inactive by construction (AssistantMessage
// holds `sources` empty until the turn completes), so the sources plugin has
// nothing to resolve and is left out — which also keeps this array a stable
// module constant.
const STREAMING_PLUGINS = [remarkGfm];

// Lexer only — no gfm, no plugins, no hast/React conversion. Used purely to
// find top-level block boundaries, which is an order of magnitude cheaper
// than the full render pipeline it lets us skip.
const blockLexer = unified().use(remarkParse);

/**
 * Split markdown into its top-level blocks, using remark's own lexer so that
 * fenced code, tables, and loose lists stay intact (a naive blank-line split
 * would tear a code block apart at its internal blank lines).
 *
 * Positions come from the mdast nodes, so each returned string is a verbatim
 * slice of the input — concatenating them back is lossless apart from the
 * whitespace between blocks, which markdown does not render anyway.
 */
function splitIntoBlocks(markdown: string): string[] {
  const tree = blockLexer.parse(markdown) as Root;
  const blocks: string[] = [];
  for (const node of tree.children) {
    const start = node.position?.start.offset;
    const end = node.position?.end.offset;
    if (start === undefined || end === undefined) continue;
    blocks.push(markdown.slice(start, end));
  }
  // An unclosed fence early in the text yields one giant block; that is a
  // correct (if unhelpful) split. An empty result means nothing renderable
  // was lexed — fall back to the raw string rather than rendering nothing.
  return blocks.length > 0 ? blocks : [markdown];
}

/**
 * One already-complete block of a streaming message. Memoized on `content`
 * alone: as more deltas arrive only the final block's string changes, so
 * every block before it keeps its previous render instead of re-running
 * ReactMarkdown's parse → mdast → hast → React-element pipeline.
 */
const MarkdownBlock = memo(function MarkdownBlock({ content }: { content: string }) {
  return (
    <ReactMarkdown remarkPlugins={STREAMING_PLUGINS} components={MARKDOWN_COMPONENTS}>
      {content}
    </ReactMarkdown>
  );
});

/**
 * Reply-text renderer with two modes.
 *
 * **Streaming** — the text is split into top-level blocks and each is
 * rendered by a memoized child. Without this, every delta re-parses the
 * whole message from the first character: for an N-character answer arriving
 * in D deltas the cost is O(N·D), which is what makes a long answer visibly
 * stutter near its end. Splitting reduces the per-delta cost to the size of
 * the block still being written.
 *
 * **Complete** — a single parse of the whole document. Citations are
 * resolved here and must stay whole-document: CommonMark scopes link
 * *reference* resolution to the document, so `[1]` in one block and its
 * definition in another would not pair up if the blocks were parsed
 * separately.
 */
export const Markdown = memo(function Markdown({
  text,
  isStreaming,
  sources,
}: {
  text: string;
  isStreaming: boolean;
  sources: ExtractedSources;
}) {
  const markdownText = isStreaming ? `${text}${CURSOR_MARKER}` : text;

  const blocks = useMemo(
    () => (isStreaming ? splitIntoBlocks(markdownText) : null),
    [isStreaming, markdownText],
  );

  const completePlugins = useMemo(() => [remarkGfm, markdownSourcesPlugin(sources)], [sources]);

  return (
    <div
      className={cn(
        "prose prose-invert max-w-none text-sm leading-[1.75] text-foreground prose-headings:text-foreground prose-strong:text-foreground prose-code:rounded prose-code:bg-muted/50 prose-code:px-1 prose-code:py-0.5 prose-code:font-mono prose-code:text-[var(--chat-fg-secondary)] prose-pre:bg-muted/50 prose-a:text-[var(--chat-brand-accent)] prose-a:no-underline hover:prose-a:underline",
        isStreaming && "streaming-shimmer",
      )}
    >
      {blocks ? (
        // Index keys are stable here: streaming only ever appends, so a
        // given index keeps its block until the text stops growing.
        blocks.map((block, i) => <MarkdownBlock key={i} content={block} />)
      ) : (
        <ReactMarkdown remarkPlugins={completePlugins} components={MARKDOWN_COMPONENTS}>
          {markdownText}
        </ReactMarkdown>
      )}
    </div>
  );
});

function replaceCursorMarker(node: ReactNode): ReactNode {
  if (typeof node === "string") {
    if (!node.includes(CURSOR_MARKER)) return node;
    const [before, ...rest] = node.split(CURSOR_MARKER);
    return (
      <>
        {before}
        <Cursor />
        {rest.join(CURSOR_MARKER)}
      </>
    );
  }
  if (Array.isArray(node)) {
    return node.map((child, i) => (
      <span key={i} style={{ display: "contents" }}>
        {replaceCursorMarker(child)}
      </span>
    ));
  }
  return node;
}
