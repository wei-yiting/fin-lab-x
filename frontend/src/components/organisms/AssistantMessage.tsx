import { memo, useMemo } from "react";
import { Markdown } from "@/components/organisms/Markdown";
import { ToolCard } from "@/components/organisms/ToolCard";
import { ReasoningChip } from "@/components/molecules/ReasoningChip";
import { Sources } from "@/components/molecules/Sources";
import { RegenerateButton } from "@/components/atoms/RegenerateButton";
import { extractSources, normalizeRefDefs, REF_DEF_LINE_RE } from "@/lib/markdown-sources";
import {
  chipKey,
  chipStateOf,
  isChipExpanded,
  isReasoningPart,
  isSuppressedChip,
  isToolPart,
} from "@/lib/reasoning-chips";
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
  /** The user stopped this turn (ruling 11) — gates Regenerate off, since
   * the backend never finalized this turn's AIMessage. */
  interrupted?: boolean;
  onRegenerate?: (messageId: string) => void;
  /** Global stall stopwatch — degraded copy consumer for streaming chip headers. */
  stalled?: boolean;
  /** Frozen "Thought for Xs" lookup keyed by chipKey (client timing map). */
  getChipSeconds?: (key: string) => number;
  /** User expand/collapse overrides — beats the tail-only derivation. */
  chipOverrides?: Map<string, boolean>;
  onToggleChip?: (key: string, currentExpanded: boolean) => void;
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
  stalled = false,
  getChipSeconds,
  chipOverrides,
  onToggleChip,
}: AssistantMessageProps) {
  const parts = message.parts;
  // Reasoning parts are chips only while their turn lives in client state —
  // the streaming chip is live only on the last message of an active stream.
  const chatActive = (status === "streaming" || status === "submitted") && isLast;

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
      .replace(REF_DEF_LINE_RE, "")
      .replace(/\n{3,}/g, "\n\n")
      .trimEnd();

    if (!isStreaming && extractedSources.length > 0) {
      cleaned = cleaned.replace(/【(\d+)】/g, "[$1]");
      const syntheticDefs = extractedSources.map((s) => `[${s.label}]: #src-${s.label}`).join("\n");
      return `${cleaned}\n\n${syntheticDefs}`;
    }

    return cleaned;
  }, [concatenatedText, extractedSources, isStreaming]);

  // A turn aborted by Stop leaves parts frozen mid-flight: a reasoning part
  // stuck in state "streaming" (no reasoning-end on the wire), a tool part
  // still in a running state, or — when Stop lands while the answer itself is
  // streaming — a text part that never received its text-end. Derived from
  // shape alone; the turn-level record is a separate signal (see the
  // Regenerate gate).
  const isAbortedTurn =
    status === "ready" &&
    parts.some(
      (p) =>
        (isReasoningPart(p) && p.state === "streaming") ||
        (isToolPart(p) && isRunningToolState(p.state as string)) ||
        (p.type === "text" && p.state === "streaming"),
    );

  // 1-based reasoning ordinal per part index (chip `data-round`).
  const chipRounds = useMemo(() => {
    let round = 0;
    return parts.map((p) => (isReasoningPart(p) ? ++round : 0));
  }, [parts]);

  return (
    <article data-testid="assistant-message" className="min-w-0">
      {parts.map((part, i) => {
        if (isReasoningPart(part)) {
          if (isSuppressedChip(part)) return null;
          const key = chipKey(message.id, i);
          const chipState = chipStateOf(part, chatActive);
          const expanded = isChipExpanded(chipState, chipOverrides?.get(key));
          return (
            <ReasoningChip
              key={key}
              chipState={chipState}
              text={part.text ?? ""}
              seconds={getChipSeconds?.(key) ?? 0}
              stalled={stalled}
              expanded={expanded}
              onToggle={() => onToggleChip?.(key, expanded)}
              round={chipRounds[i]}
            />
          );
        }

        if (isToolPart(part)) {
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
        Regenerate gating (C2.a). Regenerating replays the turn from the
        backend's checkpoint, which only holds a finalized AIMessage for a
        turn that ran to completion — so an interrupted turn 422s no matter
        how much answer text reached the client. Both signals are needed:
        the part shapes miss a Stop that lands between parts, and the
        turn-level record misses an abort that never went through Stop.
      */}
      {isLast &&
        status === "ready" &&
        onRegenerate &&
        message.parts.length > 0 &&
        !isAbortedTurn &&
        !interrupted && <RegenerateButton onRegenerate={() => onRegenerate(message.id)} />}
    </article>
  );
});
