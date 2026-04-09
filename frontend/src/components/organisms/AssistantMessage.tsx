import { useMemo } from "react"
import { Markdown } from "@/components/organisms/Markdown"
import { ToolCard } from "@/components/organisms/ToolCard"
import { ErrorBlock } from "@/components/organisms/ErrorBlock"
import { Sources } from "@/components/molecules/Sources"
import { RegenerateButton } from "@/components/atoms/RegenerateButton"
import { extractSources } from "@/lib/markdown-sources"
import { toFriendlyError } from "@/lib/error-messages"
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
}

export function AssistantMessage({
  message,
  isLast,
  status,
  abortedTools,
  toolProgress,
  onRegenerate,
}: AssistantMessageProps) {
  const parts = message.parts

  const concatenatedText = parts
    .filter((p) => p.type === "text")
    .map((p) => p.text as string)
    .join("")

  const isStreaming = status === "streaming" && isLast

  const extractedSources = useMemo(
    () => (isStreaming ? [] : extractSources(concatenatedText)),
    [isStreaming, concatenatedText],
  )

  const displayText = useMemo(
    () =>
      extractedSources.length > 0
        ? concatenatedText.replace(/^\[[0-9]+\]:\s+\S+.*$/gm, "").replace(/\n{3,}/g, "\n\n")
        : concatenatedText,
    [concatenatedText, extractedSources.length],
  )

  return (
    <article data-testid="assistant-message">
      {displayText && (
        <Markdown text={displayText} isStreaming={isStreaming} sources={extractedSources} />
      )}

      {parts.map((part, i) => {
        if (part.type === "tool" || (typeof part.type === "string" && part.type.startsWith("tool-")) || part.type === "dynamic-tool") {
          const toolCallId = part.toolCallId as string
          const isAborted = abortedTools.has(toolCallId) && part.state === "input-available"
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
              onRetry={() => {}}
              source="mid-stream"
              errorClass="mid-stream"
            />
          )
        }

        return null
      })}

      {extractedSources.length > 0 && <Sources sources={extractedSources} />}

      {isLast && status === "ready" && onRegenerate && (
        <RegenerateButton onRegenerate={() => onRegenerate(message.id)} />
      )}
    </article>
  )
}
