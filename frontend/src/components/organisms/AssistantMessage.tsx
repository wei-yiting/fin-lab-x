import { memo, useMemo } from "react";
import { Markdown } from "@/components/organisms/Markdown";
import { ToolCard } from "@/components/organisms/ToolCard";
import { Sources } from "@/components/molecules/Sources";
import { RegenerateButton } from "@/components/atoms/RegenerateButton";
import { extractSources, normalizeRefDefs } from "@/lib/markdown-sources";
import { isRunningToolState } from "@/models";
import type { ChatStatus, ExtractedSources } from "@/models";

type MessagePart = Record<string, unknown>;

/** Shared empty-sources reference — see the note at its use site. */
const NO_SOURCES: ExtractedSources = [];

interface AssistantMessageMessage {
  id: string;
  role: "system" | "user" | "assistant";
  parts: MessagePart[];
}

interface AssistantMessageProps {
  message: AssistantMessageMessage;
  isLast: boolean;
  status?: ChatStatus;
  abortedTools: Set<string>;
  toolProgress: Record<string, string>;
  /** The user stopped this turn (DEV-109 ruling 11) — gates Regenerate off,
   * since the backend never finalized this turn's AIMessage. */
  interrupted?: boolean;
  onRegenerate?: (messageId: string) => void;
}

// Memoized so a delta on the streaming message does not re-render every
// other message in the transcript. This only pays off while the remaining
// props keep their references across unrelated renders, which is a standing
// constraint on the call site, not a property of this file: `onRegenerate`
// in particular closes over `messages` and therefore changes identity on
// every delta, so MessageList passes it only to the message that can
// actually use it. Adding a prop here that is rebuilt per render silently
// reverts this component to unmemoized — <Markdown> carries its own
// memoization for exactly that reason.
export const AssistantMessage = memo(function AssistantMessage({
  message,
  isLast,
  status,
  abortedTools,
  toolProgress,
  interrupted = false,
  onRegenerate,
}: AssistantMessageProps) {
  const parts = message.parts;

  const concatenatedText = parts
    .filter((p) => p.type === "text")
    .map((p) => p.text as string)
    .join("");

  const isStreaming = status === "streaming" && isLast;

  // NOTE the shared constant: returning a fresh `[]` here would hand
  // <Markdown> a new `sources` reference on every delta (this useMemo re-runs
  // each time `concatenatedText` grows), which would in turn rebuild its
  // plugin array and defeat the block memoization downstream.
  const extractedSources = useMemo(
    () => (isStreaming ? NO_SOURCES : extractSources(concatenatedText)),
    [concatenatedText, isStreaming],
  );

  const displayText = useMemo(() => {
    // Normalize bullet-prefixed ref defs and strip source headers,
    // then strip definition lines — always, even during streaming, to prevent flickering
    let cleaned = normalizeRefDefs(concatenatedText)
      .replace(/^\[(\d+)\]:?\s+\S+.*$/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .trimEnd();

    if (!isStreaming && extractedSources.length > 0) {
      cleaned = cleaned.replace(/【(\d+)】/g, "[$1]");
      const syntheticDefs = extractedSources.map((s) => `[${s.label}]: #src-${s.label}`).join("\n");
      return `${cleaned}\n\n${syntheticDefs}`;
    }

    return cleaned;
  }, [concatenatedText, extractedSources, isStreaming]);

  return (
    <article data-testid="assistant-message" className="min-w-0">
      {parts.map((part, i) => {
        if (
          part.type === "tool" ||
          (typeof part.type === "string" && part.type.startsWith("tool-")) ||
          part.type === "dynamic-tool"
        ) {
          const toolCallId = part.toolCallId as string;
          const isAborted =
            abortedTools.has(toolCallId) && isRunningToolState(part.state as string);
          return (
            <ToolCard
              key={toolCallId ?? i}
              toolPart={part as unknown as Parameters<typeof ToolCard>[0]["toolPart"]}
              isAborted={isAborted}
              progressText={toolProgress[toolCallId]}
            />
          );
        }

        return null;
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

      {/*
        Regenerate gating: Regenerating replays the turn from the backend's
        checkpoint, which only holds a finalized AIMessage for a turn that
        ran to completion — so an interrupted turn 422s no matter how much
        answer text reached the client. `interrupted` is the turn-level
        record (DEV-109 ruling 11), captured unconditionally on every Stop.
      */}
      {isLast && status === "ready" && onRegenerate && !interrupted && (
        <RegenerateButton onRegenerate={() => onRegenerate(message.id)} />
      )}
    </article>
  );
});
