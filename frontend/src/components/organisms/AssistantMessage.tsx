import { useMemo } from "react";
import { Markdown } from "@/components/organisms/Markdown";
import { ToolCard } from "@/components/organisms/ToolCard";
import { ReasoningChip } from "@/components/molecules/ReasoningChip";
import { Sources } from "@/components/molecules/Sources";
import { RegenerateButton } from "@/components/atoms/RegenerateButton";
import { extractSources, normalizeRefDefs } from "@/lib/markdown-sources";
import {
  chipKey,
  chipStateOf,
  isChipExpanded,
  isReasoningPart,
  isSuppressedChip,
} from "@/lib/reasoning-chips";
import type { ReasoningPartLike } from "@/lib/reasoning-chips";
import { isRunningToolState } from "@/models";
import type { ChatStatus } from "@/models";

type MessagePart = Record<string, unknown>;

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
  onRegenerate?: (messageId: string) => void;
  /** Global stall stopwatch — degraded copy consumer for streaming chip headers. */
  stalled?: boolean;
  /** Frozen "Thought for Xs" lookup keyed by chipKey (client timing map). */
  getChipSeconds?: (key: string) => number;
  /** User expand/collapse overrides — beats the tail-only derivation. */
  chipOverrides?: Map<string, boolean>;
  onToggleChip?: (key: string, currentExpanded: boolean) => void;
}

function isToolPartType(part: MessagePart): boolean {
  return (
    part.type === "tool" ||
    (typeof part.type === "string" && part.type.startsWith("tool-")) ||
    part.type === "dynamic-tool"
  );
}

export function AssistantMessage({
  message,
  isLast,
  status,
  abortedTools,
  toolProgress,
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

  const extractedSources = useMemo(
    () => (isStreaming ? [] : extractSources(concatenatedText)),
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

  // A turn aborted by Stop leaves parts frozen mid-flight: a reasoning part
  // stuck in state "streaming" (no reasoning-end on the wire) or a tool part
  // still in a running state once the chat is back to "ready". Derived — no
  // per-message abort bookkeeping.
  const isAbortedTurn =
    status === "ready" &&
    parts.some(
      (p) =>
        (isReasoningPart(p) && (p as ReasoningPartLike).state === "streaming") ||
        (isToolPartType(p) && isRunningToolState(p.state as string)),
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
          const rPart = part as ReasoningPartLike;
          if (isSuppressedChip(rPart)) return null;
          const key = chipKey(message.id, i);
          const chipState = chipStateOf(rPart, chatActive);
          const expanded = isChipExpanded(chipState, chipOverrides?.get(key));
          return (
            <ReasoningChip
              key={key}
              chipState={chipState}
              text={rPart.text ?? ""}
              seconds={getChipSeconds?.(key) ?? 0}
              stalled={stalled}
              expanded={expanded}
              onToggle={() => onToggleChip?.(key, expanded)}
              round={chipRounds[i]}
            />
          );
        }

        if (isToolPartType(part)) {
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
        C2.a — Regenerate gating: hide when this turn has no text body to
        meaningfully regenerate from (mid-reasoning / mid-tool aborts).
        Backend regenerate validation requires the messageId to match a
        finalized AIMessage in LangGraph state; aborted turns without text
        often leave the checkpoint without one, so the request would 422.
      */}
      {isLast &&
        status === "ready" &&
        onRegenerate &&
        message.parts.length > 0 &&
        (!isAbortedTurn || displayText) && (
          <RegenerateButton onRegenerate={() => onRegenerate(message.id)} />
        )}
    </article>
  );
}
