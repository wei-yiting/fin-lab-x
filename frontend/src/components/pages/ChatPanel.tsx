import { useChat } from "@ai-sdk/react"
import { DefaultChatTransport } from "ai"
import { useState, useMemo, useRef, useCallback, useEffect } from "react"
import { useToolProgress } from "@/hooks/useToolProgress"
import { useFollowBottom } from "@/hooks/useFollowBottom"
import { ChatHeader } from "@/components/organisms/ChatHeader"
import { Composer, type ComposerHandle } from "@/components/organisms/Composer"
import { MessageList } from "@/components/templates/MessageList"
import { EmptyState } from "@/components/organisms/EmptyState"
import { ErrorBlock } from "@/components/organisms/ErrorBlock"
import { findOriginalUserText } from "@/lib/message-helpers"
import { classifyError } from "@/lib/error-classifier"
import { toFriendlyError } from "@/lib/error-messages"
import { statusAwareFetch } from "@/lib/status-aware-fetch"
import { ChatHttpError } from "@/lib/chat-http-error"
import type { ChatStatus, ToolCallId } from "@/models"

const PRE_STREAM_4XX: ReadonlySet<string> = new Set(['pre-stream-422', 'pre-stream-404', 'pre-stream-409'])

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
      prepareSendMessagesRequest: ({ id, messages: msgs, trigger, messageId: msgId }) => {
        if (trigger === "regenerate-message") {
          return { body: { id, trigger: "regenerate", messageId: msgId } }
        }
        const lastUserMsg = [...msgs].reverse().find(m => m.role === "user")
        const text = lastUserMsg
          ? lastUserMsg.parts?.find((p: Record<string, unknown>) => p.type === "text")?.text ?? ""
          : ""
        return { body: { id, message: text } }
      },
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
  const scrollAnchorRef = useRef<HTMLDivElement>(null)
  const { forceFollowBottom } = useFollowBottom(scrollAnchorRef)
  const composerRef = useRef<ComposerHandle>(null)

  const handleSend = useCallback((text: string) => {
    lastTriggerRef.current = { type: "send", userText: text }
    forceFollowBottom()
    sendMessage({ text })
  }, [sendMessage, forceFollowBottom])

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
        if (isToolPart(part) && part.state === "input-available") {
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
    const errClass = classifyError(error)
    if (last.type === "regenerate" && PRE_STREAM_4XX.has(errClass)) {
      lastTriggerRef.current = { type: "send", userText: last.userText }
      setMessages(msgs => msgs.slice(0, -1))
      sendMessage({ text: last.userText })
      return
    }
    if (last.type === "send") {
      setMessages(msgs => msgs.slice(0, -1))
      sendMessage({ text: last.userText })
      return
    }
    if (last.type === "regenerate") {
      regenerate({ messageId: last.messageId })
    }
  }, [error, setMessages, sendMessage, regenerate])

  // Mid-stream error → mark running tools as aborted (deferred to avoid cascading render)
  useEffect(() => {
    const lastMsg = messages.at(-1)
    if (!lastMsg || lastMsg.role !== "assistant") return
    const parts = lastMsg.parts as PartLike[]
    if (!parts.some((p) => p.type === "error")) return
    const ids = parts
      .filter((p) => isToolPart(p) && p.state === "input-available")
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
        messages={messages as unknown as Parameters<typeof MessageList>[0]["messages"]}
        status={status as ChatStatus}
        toolProgress={toolProgress}
        abortedTools={abortedTools}
        onRegenerate={handleRegenerate}
        emptyContent={
          !showPreStreamError ? (
            <EmptyState onPickPrompt={(text) => composerRef.current?.setValue(text)} />
          ) : undefined
        }
      />
      {showPreStreamError && preStreamFriendly && (
        <div className="px-4">
          <ErrorBlock
            friendly={preStreamFriendly}
            onRetry={handleRetry}
            source="pre-stream"
            errorClass={preStreamErrorClass}
          />
        </div>
      )}
      <Composer
        ref={composerRef}
        sendMessage={({ text }) => handleSend(text)}
        stop={handleStop}
        status={status as ChatStatus}
      />
    </div>
  )
}
