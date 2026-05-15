import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useState, useMemo, useRef, useCallback, useEffect, useLayoutEffect } from "react";
import { useToolProgress } from "@/hooks/useToolProgress";
import { useReasoningStatus } from "@/hooks/useReasoningStatus";
import { ChatHeader } from "@/components/organisms/ChatHeader";
import { Composer, type ComposerHandle } from "@/components/organisms/Composer";
import { MessageList, type MessageListHandle } from "@/components/templates/MessageList";
import { EmptyState } from "@/components/organisms/EmptyState";
import { ErrorBlock } from "@/components/organisms/ErrorBlock";
import { LiveStatusAnnouncer, type AnnouncedEvent } from "@/components/atoms/LiveStatusAnnouncer";
import { findOriginalUserText } from "@/lib/message-helpers";
import { classifyError } from "@/lib/error-classifier";
import { toFriendlyError } from "@/lib/error-messages";
import { ChatHttpError, statusAwareFetch } from "@/lib/chat-http";
import { isRunningToolState } from "@/models";
import type { ChatStatus, ToolCallId } from "@/models";

type PartLike = Record<string, unknown>;

function isToolPart(p: PartLike): boolean {
  const t = p.type;
  return typeof t === "string" && (t.startsWith("tool-") || t === "dynamic-tool");
}

function getToolCallId(p: PartLike): string {
  return p.toolCallId as string;
}

type LastTrigger =
  | { type: "send"; userText: string }
  | { type: "regenerate"; messageId: string; userText: string };

export function ChatPanel() {
  const [chatId, setChatId] = useState(() => crypto.randomUUID());
  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: "/api/v1/chat",
        fetch: statusAwareFetch,
      }),
    [],
  );
  const { toolProgress, handleData: toolProgressHandleData, clearProgress } = useToolProgress();
  const {
    reasoningStatusText,
    stalled: reasoningStalled,
    handleData: handleReasoningData,
    hideReasoningStatus,
    resetForNewTurn,
  } = useReasoningStatus();
  const [lastSSEEvent, setLastSSEEvent] = useState<AnnouncedEvent | null>(null);

  // AI SDK v6's onData only fires for data-* chunks (gated by isDataUIMessageChunk
  // in node_modules/ai/dist/index.mjs:5765). Generic SSE events (start, tool-*,
  // finish, error) reach onFinish / onError / status state instead — never here.
  // We still forward every chunk to toolProgress + reasoning handlers because
  // those care about data-tool-progress / data-reasoning-status which DO arrive.
  const onData = useCallback(
    (dataPart: { type: string; id?: string; data: unknown }) => {
      toolProgressHandleData(dataPart);
      handleReasoningData(dataPart as Parameters<typeof handleReasoningData>[0]);
    },
    [toolProgressHandleData, handleReasoningData],
  );

  const { messages, setMessages, sendMessage, regenerate, stop, status, error } = useChat({
    id: chatId,
    transport,
    onData,
    onFinish: ({ isAbort }) => {
      // AI SDK v6 routes the SSE `finish` chunk through onFinish, not onData.
      // The payload tells us *why* the stream ended: a natural finish, a
      // user-initiated stop() (isAbort), a network disconnect, or an error.
      //
      // Always latch finishedRef via handleReasoningData so any late
      // reasoning chunks buffered behind the SSE close are dropped — that
      // contract holds regardless of abort vs. natural completion.
      handleReasoningData({ type: "finish" });
      // Only the natural-completion path should trigger the SR "Response
      // complete" announcement. User-stop has its own UI affordance (the
      // frozen STOPPED indicator on the aborted assistant bubble); reading
      // "Response complete" after a user-initiated abort would be wrong.
      // isDisconnect / isError surface via status === "error" in
      // LiveStatusAnnouncer, so we also skip them here.
      if (isAbort) return;
      setLastSSEEvent({ type: "finish" });
    },
    onError: () => {
      // AI SDK v6 routes the SSE `error` chunk through onError, not onData.
      // Latch finishedRef so any late reasoning events are dropped. The
      // status === "error" path in LiveStatusAnnouncer handles the announcement.
      handleReasoningData({ type: "error" });
    },
  });
  const [abortedTools, setAbortedTools] = useState<Set<ToolCallId>>(() => new Set());
  // C1: per-message abort marker. The reasoning indicator hosts the STOPPED
  // label and is ephemeral by design (not part of message.parts) — to keep
  // the abort signal across the rest of the chat we capture the in-flight
  // reasoning text at stop time and hold it in React state. Map by message
  // id so prior aborted bubbles stay marked when later turns coexist.
  // `frozenReasoningText` is null when the user stops before any reasoning
  // text arrived (Stop-A or pure-tool aborts) — the renderer falls back to
  // the text-less STOPPED label.
  const [abortedMessages, setAbortedMessages] = useState<
    Map<string, { frozenReasoningText: string | null }>
  >(() => new Map());
  const lastTriggerRef = useRef<LastTrigger | null>(null);
  const messageListRef = useRef<MessageListHandle>(null);
  const composerRef = useRef<ComposerHandle>(null);

  const handleSend = useCallback(
    (text: string) => {
      lastTriggerRef.current = { type: "send", userText: text };
      messageListRef.current?.forceFollowBottom();
      resetForNewTurn();
      setLastSSEEvent(null);
      sendMessage({ text });
    },
    [sendMessage, resetForNewTurn],
  );

  const handleRegenerate = useCallback(
    (messageId: string) => {
      const userText = findOriginalUserText(messages, messageId);
      lastTriggerRef.current = { type: "regenerate", messageId, userText };
      regenerate({ messageId });
    },
    [messages, regenerate],
  );

  const handleStop = useCallback(() => {
    const lastMsg = messages.at(-1);
    const runningIds: ToolCallId[] = [];
    if (lastMsg && lastMsg.role === "assistant") {
      for (const p of lastMsg.parts) {
        const part = p as PartLike;
        if (isToolPart(part) && isRunningToolState(part.state as string)) {
          runningIds.push(getToolCallId(part));
        }
      }
    }
    if (runningIds.length) {
      setAbortedTools((prev) => new Set([...prev, ...runningIds]));
    }
    // Mark this message as aborted and capture the in-flight reasoning text
    // so MessageList can render a frozen indicator with STOPPED for it.
    if (lastMsg && lastMsg.role === "assistant") {
      const captured = reasoningStatusText;
      setAbortedMessages((prev) => {
        const next = new Map(prev);
        next.set(lastMsg.id, { frozenReasoningText: captured });
        return next;
      });
    }
    // hide (not clear) — clearReasoningStatus would latch clearedRef and
    // prevent the next turn from showing reasoning at all.
    hideReasoningStatus();
    stop();
  }, [messages, stop, hideReasoningStatus, reasoningStatusText]);

  const handleClearSession = useCallback(() => {
    stop();
    setChatId(crypto.randomUUID());
    clearProgress();
    resetForNewTurn();
    setLastSSEEvent(null);
    setAbortedTools(new Set());
    setAbortedMessages(new Map());
    lastTriggerRef.current = null;
  }, [stop, clearProgress, resetForNewTurn]);

  const handleRetry = useCallback(() => {
    const last = lastTriggerRef.current;
    if (!last) return;
    // Reset reasoning state so finishedRef (latched by the prior `error` /
    // `finish`) does not block data-reasoning-status events on the retried
    // turn, and so LiveStatusAnnouncer drops the stale finish announcement.
    resetForNewTurn();
    setLastSSEEvent(null);
    // Two failure shapes end up here:
    //   1) Pre-stream failure — messages is [user₀]. Last message is the user turn.
    //      Drop the trailing user and re-send the text (regenerate({messageId}) would
    //      try to remove a non-existent assistant and throw).
    //   2) Mid-stream SSE error — messages is [user₀, assistant(partial)]. Route through
    //      regenerate({messageId}) so the SDK slices off the failed assistant turn and
    //      re-runs the same user turn. Plain sendMessage({text}) here would append a
    //      duplicate user message.
    const lastMsg = messages.at(-1);
    if (lastMsg && lastMsg.role === "assistant") {
      lastTriggerRef.current = {
        type: "regenerate",
        messageId: lastMsg.id,
        userText: last.userText,
      };
      regenerate({ messageId: lastMsg.id });
      return;
    }
    lastTriggerRef.current = { type: "send", userText: last.userText };
    setMessages((msgs) => msgs.slice(0, -1));
    sendMessage({ text: last.userText });
  }, [messages, regenerate, setMessages, sendMessage, resetForNewTurn]);

  // Bug B / E auto-hide: AI SDK v6 does not route generic SSE events
  // (text-start, tool-input-available) through onData, so the reasoning
  // hook cannot clear its text on those events directly. Watch the
  // messages array instead and clear when a new visible part lands.
  //
  // Trigger condition is "parts.length increased", NOT "last part is
  // text/tool". Tool state transitions (input-streaming → output-available)
  // and the post-tool synthesis gap leave parts.length unchanged, so they
  // must NOT wipe — otherwise the synthesizing reasoning chunks (which
  // arrive while last part is a completed tool) get clobbered the moment
  // they set text and trigger a re-render.
  //
  // Use a ref to compare against the previous render: when assistant
  // messageId changes, reset count to 0 so the first real part on a new
  // turn correctly counts as "new". layoutEffect (not effect) so the
  // clear happens before paint and the user never sees stale reasoning
  // text alongside a freshly streamed text part.
  const prevAssistantRef = useRef<{ id: string | null; partsCount: number }>({
    id: null,
    partsCount: 0,
  });
  useLayoutEffect(() => {
    const lastMsg = messages.at(-1);
    if (!lastMsg || lastMsg.role !== "assistant") {
      prevAssistantRef.current = { id: null, partsCount: 0 };
      return;
    }
    const prev = prevAssistantRef.current;
    const sameMessage = prev.id === lastMsg.id;
    const prevCount = sameMessage ? prev.partsCount : 0;
    const currCount = (lastMsg.parts as PartLike[]).length;
    prevAssistantRef.current = { id: lastMsg.id, partsCount: currCount };
    if (currCount > prevCount) {
      hideReasoningStatus();
    }
  }, [messages, hideReasoningStatus]);

  // When useChat enters error state, mark any running tools on the last assistant message as aborted.
  // AI SDK v6 routes SSE `error` chunks to onError/status=error, not message.parts, so we cannot
  // detect mid-stream errors by inspecting message parts — we must watch `status` instead.
  useEffect(() => {
    if (status !== "error") return;
    const lastMsg = messages.at(-1);
    if (!lastMsg || lastMsg.role !== "assistant") return;
    const parts = lastMsg.parts as PartLike[];
    const ids = parts
      .filter((p) => isToolPart(p) && isRunningToolState((p as PartLike).state as string))
      .map((p) => getToolCallId(p));
    if (ids.length) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- deliberate: mid-stream error detection must update aborted set
      setAbortedTools((prev) => {
        const merged = new Set([...prev, ...ids]);
        return merged.size !== prev.size ? merged : prev;
      });
    }
  }, [status, messages]);

  const showError = status === "error" && error;
  // A mid-stream SSE error is one that arrives after the stream has already
  // produced an assistant message with content. HTTP-layer errors (ChatHttpError)
  // are always pre-stream even if a previous assistant turn happens to exist.
  const lastMsg = messages.at(-1);
  const isMidStreamError =
    showError &&
    !(error instanceof ChatHttpError) &&
    !(error instanceof TypeError) &&
    lastMsg?.role === "assistant" &&
    Array.isArray(lastMsg.parts) &&
    lastMsg.parts.length > 0;

  const errorFriendly = showError
    ? toFriendlyError(
        isMidStreamError
          ? { source: "mid-stream-sse", rawMessage: error?.message }
          : {
              source: error instanceof TypeError ? "network" : "pre-stream-http",
              status: error instanceof ChatHttpError ? error.status : undefined,
              rawMessage: error?.message,
            },
      )
    : null;
  const errorBlockSource: "pre-stream" | "mid-stream" = isMidStreamError
    ? "mid-stream"
    : "pre-stream";
  const errorClass = isMidStreamError ? "mid-stream" : showError ? classifyError(error) : "";

  return (
    <div
      data-testid="chat-panel"
      data-chat-id={chatId}
      className="relative flex h-screen flex-col bg-background"
    >
      <ChatHeader onClear={handleClearSession} messagesEmpty={messages.length === 0} />
      <MessageList
        ref={messageListRef}
        messages={messages as unknown as Parameters<typeof MessageList>[0]["messages"]}
        status={status as ChatStatus}
        toolProgress={toolProgress}
        abortedTools={abortedTools}
        abortedMessages={abortedMessages}
        onRegenerate={handleRegenerate}
        reasoningStatusText={reasoningStatusText}
        reasoningStalled={reasoningStalled}
        emptyContent={
          !showError ? (
            <EmptyState
              onPickPrompt={(text) => {
                composerRef.current?.setValue(text);
                composerRef.current?.focus();
              }}
            />
          ) : undefined
        }
        errorContent={
          errorFriendly ? (
            <ErrorBlock
              friendly={errorFriendly}
              onRetry={handleRetry}
              source={errorBlockSource}
              errorClass={errorClass}
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
      <LiveStatusAnnouncer status={status as ChatStatus} lastEvent={lastSSEEvent} />
    </div>
  );
}
