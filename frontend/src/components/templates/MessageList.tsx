import { useRef, useMemo, useImperativeHandle, forwardRef, Fragment, type ReactNode } from "react";
import { UserMessage } from "@/components/atoms/UserMessage";
import { InterruptedMarker } from "@/components/atoms/InterruptedMarker";
import { AssistantMessage } from "@/components/organisms/AssistantMessage";
import { useFollowBottom } from "@/hooks/useFollowBottom";
import type { ChatStatus } from "@/models";

interface MessageListMessage {
  id: string;
  role: string;
  parts: Record<string, unknown>[];
}

interface MessageListProps {
  messages: MessageListMessage[];
  status: ChatStatus;
  toolProgress: Record<string, string>;
  abortedTools: Set<string>;
  /** Message ids whose turn the user interrupted (DEV-109 ruling 11) — an
   * "Interrupted" row renders right under each. */
  interruptedMessages?: Set<string>;
  onRegenerate: (id: string) => void;
  /** Rendered below the transcript during the dead-air windows. */
  placeholder?: ReactNode;
  emptyContent?: ReactNode;
  errorContent?: ReactNode;
}

export interface MessageListHandle {
  forceFollowBottom: () => void;
}

export const MessageList = forwardRef<MessageListHandle, MessageListProps>(function MessageList(
  {
    messages,
    status,
    toolProgress,
    abortedTools,
    interruptedMessages,
    onRegenerate,
    placeholder,
    emptyContent,
    errorContent,
  },
  ref,
) {
  const viewportRef = useRef<HTMLDivElement>(null);
  // The placeholder mounts on its own grace timer — in windows B/C that is
  // 300ms *after* the `messages` change that opened the gap, so `messages`
  // alone would not re-run the follow-bottom effect and the placeholder
  // could be appended below the fold for exactly the dead-air period it
  // exists to cover. Fold its visibility into the trigger. A boolean, not
  // the node: `placeholder` is a fresh ReactNode on every parent render.
  // `shouldFollowBottom` still gates the scroll, so a user who scrolled up
  // is never yanked back down.
  const hasPlaceholder = placeholder != null;
  const scrollTrigger = useMemo(() => ({ messages, hasPlaceholder }), [messages, hasPlaceholder]);
  const { shouldFollowBottom, handleScroll, forceFollowBottom } = useFollowBottom(
    viewportRef,
    scrollTrigger,
  );

  useImperativeHandle(ref, () => ({ forceFollowBottom }), [forceFollowBottom]);

  if (messages.length === 0 && !placeholder) {
    return (
      <div
        data-testid="message-list"
        data-status={status}
        className="flex flex-1 flex-col overflow-hidden"
      >
        {emptyContent}
      </div>
    );
  }

  const maskGradient = "linear-gradient(to bottom, transparent 0, black 60px)";
  return (
    <div
      data-testid="message-list"
      data-status={status}
      className="flex flex-1 flex-col overflow-hidden"
    >
      <div
        ref={viewportRef}
        data-testid="message-list-viewport"
        data-at-bottom={shouldFollowBottom ? "true" : "false"}
        onScroll={handleScroll}
        className="min-h-0 flex-1 overflow-y-auto"
        style={{ maskImage: maskGradient, WebkitMaskImage: maskGradient }}
      >
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-4 px-16 pt-[76px] pb-4">
          {messages.map((msg, i) => {
            const interrupted = interruptedMessages?.has(msg.id) ?? false;
            if (msg.role === "user") {
              const textPart = msg.parts.find((p) => p.type === "text");
              return (
                <Fragment key={msg.id}>
                  <UserMessage content={(textPart?.text as string) ?? ""} />
                  {interrupted && <InterruptedMarker />}
                </Fragment>
              );
            }
            if (msg.role === "assistant") {
              const isLast = i === messages.length - 1;
              // (isLast, status) → primitive props here, instead of raw
              // `status` inside AssistantMessage: earlier messages derive the
              // same values for every status, so passing status raw would
              // break their memoization on each transition of the streaming
              // turn.
              const isStreaming = isLast && status === "streaming";
              return (
                <Fragment key={msg.id}>
                  <AssistantMessage
                    message={msg as unknown as Parameters<typeof AssistantMessage>[0]["message"]}
                    isStreaming={isStreaming}
                    abortedTools={abortedTools}
                    toolProgress={toolProgress}
                    interrupted={interrupted}
                    // Regenerate exists only on the last message of a ready
                    // transcript (S-regen-02) — and this callback closes over
                    // `messages`, so its identity changes on every delta.
                    // Handing it to any other message would break that
                    // message's memoization for a button it never shows.
                    onRegenerate={isLast && status === "ready" ? onRegenerate : undefined}
                  />
                  {interrupted && <InterruptedMarker />}
                </Fragment>
              );
            }
            return null;
          })}
          {errorContent}
          {placeholder}
        </div>
      </div>
    </div>
  );
});
