import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useState, useMemo, useRef, useCallback, useEffect, useLayoutEffect } from "react";
import { useToolProgress } from "@/hooks/useToolProgress";
import { useStallTimer } from "@/hooks/useStallTimer";
import { useReasoningTimers } from "@/hooks/useReasoningTimers";
import { useDeadAirPlaceholder } from "@/hooks/useDeadAirPlaceholder";
import { isToolPart } from "@/lib/reasoning-chips";
import { ChatHeader } from "@/components/organisms/ChatHeader";
import { Composer, type ComposerHandle } from "@/components/organisms/Composer";
import { MessageList, type MessageListHandle } from "@/components/templates/MessageList";
import { EmptyState } from "@/components/organisms/EmptyState";
import { ErrorBlock } from "@/components/organisms/ErrorBlock";
import { ActivityPlaceholder } from "@/components/atoms/ActivityPlaceholder";
import { LiveStatusAnnouncer, type AnnouncedEvent } from "@/components/atoms/LiveStatusAnnouncer";
import { findOriginalUserText } from "@/lib/message-helpers";
import { classifyError } from "@/lib/error-classifier";
import { toFriendlyError } from "@/lib/error-messages";
import { ChatHttpError, statusAwareFetch } from "@/lib/chat-http";
import { isRunningToolState } from "@/models";
import type { ChatStatus, ToolCallId } from "@/models";

type PartLike = Record<string, unknown>;

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
  const [lastSSEEvent, setLastSSEEvent] = useState<AnnouncedEvent | null>(null);
  // Late-bound handle to the stall stopwatch's reset — onData is wired into
  // useChat above the stall hook in this component, so it reaches the reset
  // through a ref kept in sync by an effect below.
  const notifyActivityRef = useRef<(() => void) | null>(null);

  // AI SDK v6's onData only fires for data-* chunks. Native parts
  // (reasoning-*, text-*, tool-*) land in message.parts — the chips and
  // placeholder derive everything from (status, messages).
  const onData = useCallback(
    (dataPart: { type: string; id?: string; data: unknown }) => {
      toolProgressHandleData(dataPart);
      // Transient data-* chunks never enter message.parts, so the
      // messages-keyed reset below can't see them — but they ARE stream
      // parts and must zero the stall stopwatch (C3).
      notifyActivityRef.current?.();
    },
    [toolProgressHandleData],
  );

  const { messages, setMessages, sendMessage, regenerate, stop, status, error } = useChat({
    id: chatId,
    transport,
    onData,
    onFinish: ({ isAbort, isDisconnect, isError }) => {
      // Only the natural-completion path should trigger the SR "Response
      // complete" announcement. The three non-normal paths each have their
      // own user-visible affordance:
      //   - isAbort      → aborted chip header (Stopped — thought for Xs)
      //   - isDisconnect → status === "error" in LiveStatusAnnouncer
      //   - isError      → status === "error" in LiveStatusAnnouncer
      if (isAbort || isDisconnect || isError) return;
      setLastSSEEvent({ type: "finish" });
    },
  });
  const [abortedTools, setAbortedTools] = useState<Set<ToolCallId>>(() => new Set());
  // Turn-level interruption record (DEV-109 ruling 11): message ids whose
  // turn the user stopped. Companion to abortedTools — same capture point,
  // message-granular instead of tool-granular, so the transcript always
  // carries an explicit "Interrupted" row even when no chip or tool card
  // exists to carry the abort state (Stop during placeholder / reply text).
  const [interruptedMessages, setInterruptedMessages] = useState<Set<string>>(() => new Set());
  const lastTriggerRef = useRef<LastTrigger | null>(null);
  const messageListRef = useRef<MessageListHandle>(null);
  const composerRef = useRef<ComposerHandle>(null);

  // Four of the five allowed non-derived stores of the chips system live
  // here (the fifth, the placeholder grace timer, lives inside
  // useDeadAirPlaceholder — see hooks/README.md for the full budget):
  //   1. chip timing map (Thought-for-Xs measurement),
  //   2. global stall stopwatch,
  //   3. user expand/collapse overrides (cleared each turn — QA16),
  //   4. turn interruption record (interruptedMessages — DEV-109 ruling 11).
  const chatActive = status === "submitted" || status === "streaming";
  const { stalled, notifyActivity } = useStallTimer(chatActive);
  useEffect(() => {
    notifyActivityRef.current = notifyActivity;
  }, [notifyActivity]);
  const { observe, getSeconds, reset: resetTimers } = useReasoningTimers();
  const [chipOverrides, setChipOverrides] = useState<Map<string, boolean>>(() => new Map());

  // Any stream part / delta arrival re-renders `messages` — that is the
  // stopwatch's reset signal (C3: any part zeroes the global stall clock).
  // Layout effect, not effect: the reset must land before paint so the
  // render that introduces a new part never paints a stale degraded header
  // (reset-before-derive — QA18 / S-place-05).
  useLayoutEffect(() => {
    if (chatActive) notifyActivity();
  }, [messages, chatActive, notifyActivity]);

  // Render-time observation: freezing happens on the very render triggered
  // by the freezing event (next part arrival / status change), so chip
  // durations are consistent before paint.
  observe(messages, chatActive);

  const placeholderState = useDeadAirPlaceholder(messages, status);

  const handleToggleChip = useCallback((key: string, currentExpanded: boolean) => {
    setChipOverrides((prev) => {
      const next = new Map(prev);
      next.set(key, !currentExpanded);
      return next;
    });
  }, []);

  // Clears only the expand/collapse override map. The chip timing map is
  // deliberately NOT touched here: it's keyed by chipKey(messageId, partIndex),
  // so entries for already-completed, still-rendered messages are never
  // re-read once a new turn's message ids are in play — wiping the whole
  // map on every send/regenerate/retry corrupted already-displayed
  // "Thought for Xs" durations on unrelated past turns (DEV-106 review fix).
  const resetForNewTurn = useCallback(() => {
    setChipOverrides(new Map());
  }, []);

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
      resetForNewTurn();
      // Regenerating replaces the turn — its interruption record no longer
      // describes the new answer (the SDK may reuse the message id).
      setInterruptedMessages((prev) => {
        if (!prev.has(messageId)) return prev;
        const next = new Set(prev);
        next.delete(messageId);
        return next;
      });
      regenerate({ messageId });
    },
    [messages, regenerate, resetForNewTurn],
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
    // The aborted chip needs no capture here: the reasoning part stays in
    // message.parts with state "streaming" (no reasoning-end on the wire),
    // and the header derives "Stopped — thought for Xs" from that shape.
    // The turn-level marker anchors on the last message regardless of role:
    // a Stop before the assistant message exists (placeholder window) still
    // leaves an "Interrupted" row under the user bubble.
    const anchor = messages.at(-1);
    if (anchor) {
      setInterruptedMessages((prev) => new Set(prev).add(anchor.id));
    }
    stop();
  }, [messages, stop]);

  const handleClearSession = useCallback(() => {
    stop();
    setChatId(crypto.randomUUID());
    clearProgress();
    // The only call site where a full timing-map wipe is correct: the whole
    // transcript disappears with the new chatId, so no stale entry can leak.
    resetTimers();
    resetForNewTurn();
    setLastSSEEvent(null);
    setAbortedTools(new Set());
    setInterruptedMessages(new Set());
    lastTriggerRef.current = null;
  }, [stop, clearProgress, resetTimers, resetForNewTurn]);

  const handleRetry = useCallback(() => {
    const last = lastTriggerRef.current;
    if (!last) return;
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
        interruptedMessages={interruptedMessages}
        onRegenerate={handleRegenerate}
        placeholder={
          placeholderState === "waiting" ? <ActivityPlaceholder stalled={stalled} /> : undefined
        }
        stalled={stalled}
        getChipSeconds={getSeconds}
        chipOverrides={chipOverrides}
        onToggleChip={handleToggleChip}
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
