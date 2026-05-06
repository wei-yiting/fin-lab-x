import { useMemo } from "react";
import { Markdown } from "@/components/organisms/Markdown";
import { ToolCard } from "@/components/organisms/ToolCard";
import { Sources } from "@/components/molecules/Sources";
import { RegenerateButton } from "@/components/atoms/RegenerateButton";
import { extractSources, normalizeRefDefs } from "@/lib/markdown-sources";
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
  /**
   * True when the user halted this turn via Stop. Drives two visual changes:
   *   - 9c: append an inline STOPPED label at the tail of the streamed text
   *     (when text was already in flight at stop time).
   *   - C2.a: hide the Regenerate button when there is no text body to keep
   *     (an empty-parts aborted bubble has nothing useful to regenerate from
   *     and the backend regenerate path errors on the missing AIMessage).
   */
  isAborted?: boolean;
  toolProgress: Record<string, string>;
  onRegenerate?: (messageId: string) => void;
}

export function AssistantMessage({
  message,
  isLast,
  status,
  abortedTools,
  isAborted = false,
  toolProgress,
  onRegenerate,
}: AssistantMessageProps) {
  // D39.b defense-in-depth: even if backend `transient: true` is broken and a
  // data-reasoning-* part lands in `parts`, never render it in the transcript.
  const parts = useMemo(
    () =>
      message.parts.filter(
        (part) => typeof part.type !== "string" || !part.type.startsWith("data-reasoning-"),
      ),
    [message.parts],
  );

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
          {/*
            C1 / mockup State 9c — inline STOPPED appended at the tail of the
            partial response text. Sits inside the .pl-3 wrapper so the label
            wraps naturally with the last text line rather than starting a new
            visual row.
          */}
          {isAborted && (
            <span className="reasoning-status-frozen-label" data-testid="text-stopped-label">
              STOPPED
            </span>
          )}
        </div>
      )}

      {!isStreaming && extractedSources.length > 0 && (
        <div className="pl-3">
          <Sources sources={extractedSources} />
        </div>
      )}

      {/*
        C2.a — Regenerate gating: hide when this turn has no text part to
        meaningfully regenerate from. Two cases:
          - empty parts (Stop-A / Stop-B mid-reasoning) — nothing rendered
          - aborted with only tool parts (Stop-C) — same: no text to keep
        Backend regenerate validation requires the messageId to match a
        finalized AIMessage in LangGraph state; mid-reasoning aborts often
        leave the checkpoint without one, so the request would 422.
      */}
      {isLast &&
        status === "ready" &&
        onRegenerate &&
        message.parts.length > 0 &&
        (!isAborted || displayText) && (
          <RegenerateButton onRegenerate={() => onRegenerate(message.id)} />
        )}
    </article>
  );
}
