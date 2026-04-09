import { useMemo } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { RefSup } from "@/components/atoms/RefSup"
import { Cursor } from "@/components/atoms/Cursor"
import type { ExtractedSources } from "@/models"

export function Markdown({
  text,
  isStreaming,
  sources,
}: {
  text: string
  isStreaming: boolean
  sources: ExtractedSources
}) {
  const labelToSource = useMemo(
    () => new Map(sources.map((s) => [s.label, s])),
    [sources],
  )

  return (
    <div className="prose prose-invert max-w-none text-sm leading-relaxed text-foreground prose-headings:text-foreground prose-strong:text-foreground prose-code:rounded prose-code:bg-muted/50 prose-code:px-1 prose-code:py-0.5 prose-code:font-mono prose-code:text-[var(--chat-fg-secondary)] prose-pre:bg-muted/50 prose-a:text-[var(--chat-brand-accent)] prose-a:no-underline hover:prose-a:underline">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => {
            const childText = String(children)
            if (labelToSource.has(childText)) {
              return <RefSup label={childText} href={`#src-${childText}`} />
            }
            return (
              <a href={href} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            )
          },
        }}
      >
        {text}
      </ReactMarkdown>
      {isStreaming && <Cursor />}
    </div>
  )
}
