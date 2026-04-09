import { useRef, useEffect, type ReactNode } from "react"
import { ScrollArea } from "@/components/primitives/scroll-area"
import { UserMessage } from "@/components/molecules/UserMessage"
import { AssistantMessage } from "@/components/organisms/AssistantMessage"
import { TypingIndicator } from "@/components/atoms/TypingIndicator"
import { shouldShowTypingIndicator } from "@/lib/typing-indicator-logic"
import { useFollowBottom } from "@/hooks/useFollowBottom"
import type { ChatStatus } from "@/models"

type MessageListMessage = {
  id: string
  role: string
  parts: Record<string, unknown>[]
}

type MessageListProps = {
  messages: MessageListMessage[]
  status: ChatStatus
  toolProgress: Record<string, string>
  abortedTools: Set<string>
  onRegenerate: (id: string) => void
  emptyContent?: ReactNode
}

export function MessageList({
  messages,
  status,
  toolProgress,
  abortedTools,
  onRegenerate,
  emptyContent,
}: MessageListProps) {
  const viewportRef = useRef<HTMLDivElement>(null)
  const { shouldFollowBottom, handleScroll } = useFollowBottom(viewportRef)

  useEffect(() => {
    if (shouldFollowBottom && viewportRef.current) {
      viewportRef.current.scrollTop = viewportRef.current.scrollHeight
    }
  }, [messages, shouldFollowBottom])

  const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null
  const showTyping = shouldShowTypingIndicator({
    status,
    lastMessage: lastMessage as Parameters<typeof shouldShowTypingIndicator>[0]["lastMessage"],
  })

  if (messages.length === 0 && !showTyping) {
    return (
      <div data-testid="message-list" data-status={status} className="flex flex-1 flex-col overflow-hidden">
        {emptyContent}
      </div>
    )
  }

  return (
    <div data-testid="message-list" data-status={status} className="flex flex-1 flex-col overflow-hidden">
      <ScrollArea className="flex-1">
        <div
          ref={viewportRef}
          data-testid="message-list-viewport"
          onScroll={handleScroll}
          className="flex flex-col gap-4 p-4"
        >
          {messages.map((msg, i) => {
            if (msg.role === "user") {
              const textPart = msg.parts.find((p) => p.type === "text")
              return (
                <UserMessage
                  key={msg.id}
                  content={(textPart?.text as string) ?? ""}
                />
              )
            }
            if (msg.role === "assistant") {
              return (
                <AssistantMessage
                  key={msg.id}
                  message={msg as unknown as Parameters<typeof AssistantMessage>[0]["message"]}
                  isLast={i === messages.length - 1}
                  status={status}
                  abortedTools={abortedTools}
                  toolProgress={toolProgress}
                  onRegenerate={onRegenerate}
                />
              )
            }
            return null
          })}
          {showTyping && <TypingIndicator />}
        </div>
      </ScrollArea>
    </div>
  )
}
