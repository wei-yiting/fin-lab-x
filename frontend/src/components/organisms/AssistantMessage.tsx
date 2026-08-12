import { memo, useMemo } from "react";
import { Markdown } from "@/components/organisms/Markdown";
import { ToolCard } from "@/components/organisms/ToolCard";
import { Sources } from "@/components/molecules/Sources";
import { RegenerateButton } from "@/components/atoms/RegenerateButton";
import { extractSources, normalizeRefDefs } from "@/lib/markdown-sources";
import { isRunningToolState } from "@/models";
import type { ExtractedSources } from "@/models";

type MessagePart = Record<string, unknown>;

function isToolPart(part: MessagePart): boolean {
  const t = part.type;
  return typeof t === "string" && (t === "tool" || t.startsWith("tool-") || t === "dynamic-tool");
}

/** Shared empty-sources reference — see the note at its use site. */
const NO_SOURCES: ExtractedSources = [];

interface AssistantMessageMessage {
  id: string;
  role: "system" | "user" | "assistant";
  parts: MessagePart[];
}

interface AssistantMessageProps {
  message: AssistantMessageMessage;
  /** True only for the last message while the stream is still writing it —
   * derived in MessageList from (isLast, status). Deriving it there keeps
   * this prop a primitive, so settled messages stay memo-stable across
   * status transitions instead of re-rendering on every one. */
  isStreaming: boolean;
  abortedTools: Set<string>;
  toolProgress: Record<string, string>;
  /** The user stopped this turn (DEV-109 ruling 11) — gates Regenerate off,
   * since the backend never finalized this turn's AIMessage. */
  interrupted?: boolean;
  /** Present only when Regenerate may render: MessageList passes it for the
   * last message of a ready transcript and omits it otherwise (S-regen-02).
   * That placement also protects memoization — the handler closes over
   * `messages` and changes identity on every delta, so handing it to a
   * message that can never show the button would only break its memo. */
  onRegenerate?: (messageId: string) => void;
}

/**
 * Memo comparator. Every prop is shallow-compared except `toolProgress`:
 * ChatPanel rebuilds that Record on each data-tool-progress event, so its
 * identity changes even when nothing this message reads has changed —
 * comparing it by reference would re-render every settled message in the
 * transcript on every progress event. Instead, compare exactly the entries
 * this message's tool parts read.
 *
 * Props are iterated generically, so a prop added later is shallow-compared
 * by default — only `toolProgress` is special-cased.
 */
function arePropsEqual(
  prev: Readonly<AssistantMessageProps>,
  next: Readonly<AssistantMessageProps>,
): boolean {
  const keys = new Set([...Object.keys(prev), ...Object.keys(next)]) as Set<
    keyof AssistantMessageProps
  >;
  for (const key of keys) {
    if (key === "toolProgress") continue;
    if (!Object.is(prev[key], next[key])) return false;
  }
  if (prev.toolProgress === next.toolProgress) return true;
  // `message` was reference-equal above, so its tool parts enumerate every
  // toolProgress entry this render can possibly read.
  for (const part of next.message.parts) {
    if (!isToolPart(part)) continue;
    const id = part.toolCallId as string;
    if (prev.toolProgress[id] !== next.toolProgress[id]) return false;
  }
  return true;
}

// Memoized so a delta on the streaming message does not re-render every
// other message in the transcript. The props are primitives or references
// the call site keeps stable across unrelated renders; the one exception,
// `toolProgress`, is absorbed by the comparator above. <Markdown> carries
// its own memoization as a second line of defense.
export const AssistantMessage = memo(function AssistantMessage({
  message,
  isStreaming,
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
        if (isToolPart(part)) {
          const toolCallId = part.toolCallId as string;
          // abortedTools is a click-time snapshot of `handleStop`'s render
          // closure (ChatPanel), which can miss a tool call that arrived
          // inside the `experimental_throttle` window right before Stop was
          // clicked (M-2.1). `interrupted` is read fresh on every render, so
          // OR-ing it in catches that tool once its running state finally
          // renders — the stream is aborted, so it can never resolve any
          // other way. Additive only: abortedTools/handleStop still drive the
          // separate mid-stream-error path and must keep working unchanged.
          const isAborted =
            (abortedTools.has(toolCallId) || interrupted) &&
            isRunningToolState(part.state as string);
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
        The last-message + status=ready visibility rule lives in MessageList,
        which only passes onRegenerate when both hold.
      */}
      {onRegenerate && !interrupted && (
        <RegenerateButton onRegenerate={() => onRegenerate(message.id)} />
      )}
    </article>
  );
}, arePropsEqual);
