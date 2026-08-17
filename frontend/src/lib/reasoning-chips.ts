import { hasVisibleReplyText } from "@/lib/markdown-sources";

/**
 * Pure derivation helpers shared by the streaming chat UI. Everything here
 * derives from `useChat`'s `(status, messages)` — no additional state.
 */

export interface ReasoningPartLike {
  type?: unknown;
  text?: string;
  state?: string;
}

/** Minimal structural view of a chat message shared by the chip hooks. */
export interface ChatMessageLike {
  id: string;
  role: string;
  parts: Array<{ type?: unknown; state?: unknown }>;
}

export function isReasoningPart(part: {
  type?: unknown;
}): part is ReasoningPartLike & { type: "reasoning" } {
  return part.type === "reasoning";
}

/**
 * Single source of truth for tool-part classification: mirrors AI SDK 6's
 * `isToolUIPart` (static `tool-${name}` parts + `dynamic-tool`). Plain
 * `"tool"` is not a real AI SDK UI part shape and is intentionally not
 * matched here — callers that need it must import this function rather
 * than hand-roll their own predicate.
 */
export function isToolPart(part: { type?: unknown }): boolean {
  return (
    typeof part.type === "string" && (part.type.startsWith("tool-") || part.type === "dynamic-tool")
  );
}

/**
 * Whether a part currently paints anything the user can see: a
 * non-suppressed reasoning part, a tool card, or non-empty reply text.
 * Wire frames that create parts without visible content
 * (`reasoning-start` before its first delta, `text-start`, step
 * boundaries) don't count. Single source of truth for the dead-air
 * placeholder's windows — window A uses it via
 * `turnHasRenderableContent`, windows B/C anchor on the last part
 * satisfying it.
 */
export function isRenderablePart(part: { type?: unknown; state?: unknown }): boolean {
  if (isReasoningPart(part)) return !isSuppressedChip(part);
  if (isToolPart(part)) return true;
  // Text renders only if it has visible content once run through the same
  // stripping pipeline AssistantMessage's displayText applies (whitespace,
  // reference-definition lines, source headers all normalize to nothing on
  // both sides) — otherwise a dead-air window could end while the screen
  // still shows nothing new.
  if (part.type === "text") return hasVisibleReplyText((part as { text?: string }).text ?? "");
  return false;
}

/**
 * Whether the turn has painted anything the user can see — the dead-air
 * placeholder must keep covering until something actually renders.
 */
export function turnHasRenderableContent(msg: ChatMessageLike): boolean {
  return msg.parts.some(isRenderablePart);
}

/**
 * Zero-delta suppression (decision 3): a reasoning part that closed without
 * ever carrying a single delta paints nothing. A part whose streamed content
 * happens to be whitespace-only DID stream — it stays (no flash-then-vanish
 * removal).
 */
export function isSuppressedChip(part: ReasoningPartLike): boolean {
  return (part.text ?? "") === "";
}
