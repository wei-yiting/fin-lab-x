import { useChat } from "@ai-sdk/react"
import { DefaultChatTransport } from "ai"
import { useState, useMemo, useRef, useCallback, useEffect } from "react"
import { useToolProgress } from "@/hooks/useToolProgress"
import { ChatHeader } from "@/components/organisms/ChatHeader"
import { Composer, type ComposerHandle } from "@/components/organisms/Composer"
import { MessageList, type MessageListHandle } from "@/components/templates/MessageList"
import { EmptyState } from "@/components/organisms/EmptyState"
import { ErrorBlock } from "@/components/organisms/ErrorBlock"
import { findOriginalUserText } from "@/lib/message-helpers"
import { classifyError } from "@/lib/error-classifier"
import { toFriendlyError } from "@/lib/error-messages"
import { statusAwareFetch } from "@/lib/status-aware-fetch"
import { ChatHttpError } from "@/lib/chat-http-error"
import { isRunningToolState } from "@/models"
import type { ChatStatus, ToolCallId } from "@/models"

type PartLike = Record<string, unknown>

function isToolPart(p: PartLike): boolean {
  const t = p.type
  return typeof t === "string" && (t.startsWith("tool-") || t === "dynamic-tool")
}

function getToolCallId(p: PartLike): string {
  return p.toolCallId as string
}

type LastTrigger =
  | { type: "send"; userText: string }
  | { type: "regenerate"; messageId: string; userText: string }

export function ChatPanel() {
  const [chatId, setChatId] = useState(() => crypto.randomUUID())
  const transport = useMemo(
    () => new DefaultChatTransport({
      api: "/api/v1/chat",
      fetch: statusAwareFetch,
    }),
    [],
  )
  const { toolProgress, handleData, clearProgress } = useToolProgress()
  const { messages, setMessages, sendMessage, regenerate, stop, status, error } = useChat({
    id: chatId,
    transport,
    onData: handleData,
  })
  const [abortedTools, setAbortedTools] = useState<Set<ToolCallId>>(() => new Set())
  const lastTriggerRef = useRef<LastTrigger | null>(null)
  const messageListRef = useRef<MessageListHandle>(null)
  const composerRef = useRef<ComposerHandle>(null)

  const handleSend = useCallback((text: string) => {
    lastTriggerRef.current = { type: "send", userText: text }
    messageListRef.current?.forceFollowBottom()
    sendMessage({ text })
  }, [sendMessage])

  const handleRegenerate = useCallback((messageId: string) => {
    const userText = findOriginalUserText(messages, messageId)
    lastTriggerRef.current = { type: "regenerate", messageId, userText }
    regenerate({ messageId })
  }, [messages, regenerate])

  const handleStop = useCallback(() => {
    const lastMsg = messages.at(-1)
    const runningIds: ToolCallId[] = []
    if (lastMsg && lastMsg.role === "assistant") {
      for (const p of lastMsg.parts) {
        const part = p as PartLike
        if (isToolPart(part) && isRunningToolState(part.state as string)) {
          runningIds.push(getToolCallId(part))
        }
      }
    }
    if (runningIds.length) {
      setAbortedTools(prev => new Set([...prev, ...runningIds]))
    }
    stop()
  }, [messages, stop])

  const handleClearSession = useCallback(() => {
    stop()
    setChatId(crypto.randomUUID())
    clearProgress()
    setAbortedTools(new Set())
    lastTriggerRef.current = null
  }, [stop, clearProgress])

  const handleRetry = useCallback(() => {
    const last = lastTriggerRef.current
    if (!last) return
    // Two failure shapes end up here:
    //   1) Pre-stream failure — messages is [user₀]. Last message is the user turn.
    //      Drop the trailing user and re-send the text (regenerate({messageId}) would
    //      try to remove a non-existent assistant and throw).
    //   2) Mid-stream SSE error — messages is [user₀, assistant(partial)]. Route through
    //      regenerate({messageId}) so the SDK slices off the failed assistant turn and
    //      re-runs the same user turn. Plain sendMessage({text}) here would append a
    //      duplicate user message.
    const lastMsg = messages.at(-1)
    if (lastMsg && lastMsg.role === "assistant") {
      lastTriggerRef.current = { type: "regenerate", messageId: lastMsg.id, userText: last.userText }
      regenerate({ messageId: lastMsg.id })
      return
    }
    lastTriggerRef.current = { type: "send", userText: last.userText }
    setMessages(msgs => msgs.slice(0, -1))
    sendMessage({ text: last.userText })
  }, [messages, regenerate, setMessages, sendMessage])

  // Mid-stream error → mark running tools as aborted (deferred to avoid cascading render)
  useEffect(() => {
    const lastMsg = messages.at(-1)
    if (!lastMsg || lastMsg.role !== "assistant") return
    const parts = lastMsg.parts as PartLike[]
    if (!parts.some((p) => p.type === "error")) return
    const ids = parts
      .filter((p) => isToolPart(p) && isRunningToolState((p as PartLike).state as string))
      .map((p) => getToolCallId(p))
    if (ids.length) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- deliberate: mid-stream error detection must update aborted set
      setAbortedTools(prev => {
        const merged = new Set([...prev, ...ids])
        return merged.size !== prev.size ? merged : prev
      })
    }
  }, [messages])

  const showPreStreamError = status === "error" && error
  const preStreamFriendly = showPreStreamError
    ? toFriendlyError({
        source: error instanceof TypeError ? "network" : "pre-stream-http",
        status: error instanceof ChatHttpError ? error.status : undefined,
        rawMessage: error?.message,
      })
    : null
  const preStreamErrorClass = showPreStreamError ? classifyError(error) : ""

  const dataTestProps = import.meta.env.DEV ? { "data-chat-id": chatId } : {}

  return (
    <div data-testid="chat-panel" {...dataTestProps} className="flex h-screen flex-col bg-background">
      <ChatHeader onClear={handleClearSession} messagesEmpty={messages.length === 0} />
      <MessageList
        ref={messageListRef}
        messages={messages as unknown as Parameters<typeof MessageList>[0]["messages"]}
        status={status as ChatStatus}
        toolProgress={toolProgress}
        abortedTools={abortedTools}
        onRegenerate={handleRegenerate}
        emptyContent={
          !showPreStreamError ? (
            <EmptyState onPickPrompt={(text) => { composerRef.current?.setValue(text); composerRef.current?.focus() }} />
          ) : undefined
        }
        errorContent={
          showPreStreamError && preStreamFriendly ? (
            <ErrorBlock
              friendly={preStreamFriendly}
              onRetry={handleRetry}
              source="pre-stream"
              errorClass={preStreamErrorClass}
            />
          ) : undefined
        }
      />
      <Composer
        ref={composerRef}
        sendMessage={({ text }) => handleSend(text)}
        stop={handleStop}
        status={status as ChatStatus}
      />
    </div>
  )
}
