import { useRef, useImperativeHandle, forwardRef, type ReactNode } from "react";
import { UserMessage } from "@/components/atoms/UserMessage";
import { AssistantMessage } from "@/components/organisms/AssistantMessage";
import { ReasoningIndicator } from "@/components/atoms/ReasoningIndicator";
import { shouldShowReasoningIndicator } from "@/lib/reasoning-indicator-logic";
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
  onRegenerate: (id: string) => void;
  emptyContent?: ReactNode;
  errorContent?: ReactNode;
}

export interface MessageListHandle {
  forceFollowBottom: () => void;
}

export const MessageList = forwardRef<MessageListHandle, MessageListProps>(function MessageList(
  { messages, status, toolProgress, abortedTools, onRegenerate, emptyContent, errorContent },
  ref,
) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const { shouldFollowBottom, handleScroll, forceFollowBottom } = useFollowBottom(
    viewportRef,
    messages,
  );

  useImperativeHandle(ref, () => ({ forceFollowBottom }), [forceFollowBottom]);

  const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null;
  const showReasoning = shouldShowReasoningIndicator({
    status,
    lastMessage: lastMessage as Parameters<typeof shouldShowReasoningIndicator>[0]["lastMessage"],
  });

  if (messages.length === 0 && !showReasoning) {
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
            if (msg.role === "user") {
              const textPart = msg.parts.find((p) => p.type === "text");
              return <UserMessage key={msg.id} content={(textPart?.text as string) ?? ""} />;
            }
            if (msg.role === "assistant") {
              const isLast = i === messages.length - 1;
              return (
                <AssistantMessage
                  key={msg.id}
                  message={msg as unknown as Parameters<typeof AssistantMessage>[0]["message"]}
                  isLast={isLast}
                  status={status}
                  abortedTools={abortedTools}
                  toolProgress={toolProgress}
                  onRegenerate={onRegenerate}
                />
              );
            }
            return null;
          })}
          {errorContent}
          {showReasoning && <ReasoningIndicator />}
        </div>
      </div>
    </div>
  );
});
