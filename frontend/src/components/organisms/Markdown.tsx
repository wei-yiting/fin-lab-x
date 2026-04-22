import { useMemo, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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

export function Markdown({
  text,
  isStreaming,
  sources,
}: {
  text: string;
  isStreaming: boolean;
  sources: ExtractedSources;
}) {
  const remarkPlugins = useMemo(() => [remarkGfm, markdownSourcesPlugin(sources)], [sources]);

  const markdownText = isStreaming ? `${text}${CURSOR_MARKER}` : text;

  return (
    <div
      className={cn(
        "prose prose-invert max-w-none text-sm leading-[1.75] text-foreground prose-headings:text-foreground prose-strong:text-foreground prose-code:rounded prose-code:bg-muted/50 prose-code:px-1 prose-code:py-0.5 prose-code:font-mono prose-code:text-[var(--chat-fg-secondary)] prose-pre:bg-muted/50 prose-a:text-[var(--chat-brand-accent)] prose-a:no-underline hover:prose-a:underline",
        isStreaming && "streaming-shimmer",
      )}
    >
      <ReactMarkdown
        remarkPlugins={remarkPlugins}
        components={{
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
        }}
      >
        {markdownText}
      </ReactMarkdown>
    </div>
  );
}

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
