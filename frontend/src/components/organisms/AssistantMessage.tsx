import { useMemo } from "react"
import { Markdown } from "@/components/organisms/Markdown"
import { ToolCard } from "@/components/organisms/ToolCard"
import { ErrorBlock } from "@/components/organisms/ErrorBlock"
import { Sources } from "@/components/molecules/Sources"
import { RegenerateButton } from "@/components/atoms/RegenerateButton"
import { extractSources, normalizeRefDefs } from "@/lib/markdown-sources"
import { toFriendlyError } from "@/lib/error-messages"
import { isRunningToolState } from "@/models"
import type { ChatStatus } from "@/models"

type MessagePart = Record<string, unknown>

type AssistantMessageMessage = {
  id: string
  role: "system" | "user" | "assistant"
  parts: MessagePart[]
}

type AssistantMessageProps = {
  message: AssistantMessageMessage
  isLast: boolean
  status?: ChatStatus
  abortedTools: Set<string>
  toolProgress: Record<string, string>
  onRegenerate?: (messageId: string) => void
  onRetry?: () => void
}

export function AssistantMessage({
  message,
  isLast,
  status,
  abortedTools,
  toolProgress,
  onRegenerate,
  onRetry,
}: AssistantMessageProps) {
  const parts = message.parts

  const concatenatedText = parts
    .filter((p) => p.type === "text")
    .map((p) => p.text as string)
    .join("")

  const isStreaming = status === "streaming" && isLast

  const extractedSources = useMemo(
    () => (isStreaming ? [] : extractSources(concatenatedText)),
    [concatenatedText, isStreaming],
  )

  const displayText = useMemo(() => {
    // Normalize bullet-prefixed ref defs and strip source headers,
    // then strip definition lines — always, even during streaming, to prevent flickering
    let cleaned = normalizeRefDefs(concatenatedText)
      .replace(/^\[(\d+)\]:?\s+\S+.*$/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .trimEnd()

    if (!isStreaming && extractedSources.length > 0) {
      cleaned = cleaned.replace(/【(\d+)】/g, "[$1]")
      const syntheticDefs = extractedSources
        .map((s) => `[${s.label}]: #src-${s.label}`)
        .join("\n")
      return `${cleaned}\n\n${syntheticDefs}`
    }

    return cleaned
  }, [concatenatedText, extractedSources, isStreaming])

  return (
    <article data-testid="assistant-message" className="min-w-0">
      {parts.map((part, i) => {
        if (part.type === "tool" || (typeof part.type === "string" && part.type.startsWith("tool-")) || part.type === "dynamic-tool") {
          const toolCallId = part.toolCallId as string
          const isAborted = abortedTools.has(toolCallId) && isRunningToolState(part.state as string)
          return (
            <ToolCard
              key={toolCallId ?? i}
              part={part as Parameters<typeof ToolCard>[0]["part"]}
              isAborted={isAborted}
              progressText={toolProgress[toolCallId]}
            />
          )
        }

        if (part.type === "error") {
          const errorText = (part.errorText ?? part.error ?? "") as string
          const friendly = toFriendlyError({
            source: "mid-stream-sse",
            rawMessage: errorText,
          })
          return (
            <ErrorBlock
              key={`error-${i}`}
              friendly={friendly}
              onRetry={onRetry ?? (() => {})}
              source="mid-stream"
              errorClass="mid-stream"
            />
          )
        }

        return null
      })}

      {displayText && (
        <div className="pl-3">
          <Markdown text={displayText} isStreaming={isStreaming} sources={extractedSources} />
        </div>
      )}

      {!isStreaming && extractedSources.length > 0 && (
        <div className="pl-3">
          <Sources sources={extractedSources} />
        </div>
      )}

      {isLast && status === "ready" && onRegenerate && (
        <RegenerateButton onRegenerate={() => onRegenerate(message.id)} />
      )}
    </article>
  )
}
