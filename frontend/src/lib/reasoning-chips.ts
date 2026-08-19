import { isReasoningUIPart, isToolUIPart } from "ai";
import type { UIDataTypes, UIMessagePart, UITools } from "ai";
import { hasVisibleReplyText } from "@/lib/markdown-sources";

/**
 * Cast target at the delegation boundary below. The local predicates keep
 * structural parameter types so the hooks — and their plain-object test
 * fixtures — type-check without constructing full SDK parts, while the SDK
 * guards they delegate to only ever read `part.type`.
 */
type AnyUIPart = UIMessagePart<UIDataTypes, UITools>;

/**
 * Pure derivation helpers shared by the streaming chat UI. Everything here
 * derives from `useChat`'s `(status, messages)` — no additional state.
 */

export interface ReasoningPartLike {
  type?: unknown;
  text?: string;
  state?: string;
}

/** Lifecycle a reasoning chip's header renders from. */
export type ChipState = "streaming" | "done" | "aborted";

/** Minimal structural view of a chat message shared by the chip hooks. */
export interface ChatMessageLike {
  id: string;
  role: string;
  parts: Array<{ type?: unknown; state?: unknown }>;
}

/** Reasoning-part classification, delegated to AI SDK 6's `isReasoningUIPart`. */
export function isReasoningPart(part: {
  type?: unknown;
}): part is ReasoningPartLike & { type: "reasoning" } {
  return isReasoningUIPart(part as AnyUIPart);
}

/**
 * Tool-part classification, delegated to AI SDK 6's `isToolUIPart` (static
 * `tool-${name}` parts + `dynamic-tool`) so the SDK owns the rules and this
 * module cannot drift from them when a new part shape lands. The `typeof`
 * guard keeps the predicate total for the structurally-typed parts the hooks
 * pass, whose `type` may be absent — the SDK guard assumes a string.
 *
 * Single tool predicate for the chat UI — `AssistantMessage` imports this
 * one rather than hand-rolling its own. Plain `"tool"` is not a real AI SDK
 * UI part shape and is intentionally not matched.
 */
export function isToolPart(part: { type?: unknown }): boolean {
  if (typeof part.type !== "string") return false;
  return isToolUIPart(part as AnyUIPart);
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
 * Zero-delta suppression: a reasoning part that closed without
 * ever carrying a single delta paints nothing. A part whose streamed content
 * happens to be whitespace-only DID stream — it stays (no flash-then-vanish
 * removal).
 */
export function isSuppressedChip(part: ReasoningPartLike): boolean {
  return (part.text ?? "") === "";
}

/**
 * Abort-vs-finish detection falls out of the native part shape: an abort
 * closes the wire with no `reasoning-end`, so the part's `state` stays
 * `"streaming"` while the chat-level status has left the active pair.
 * An errored round whose `reasoning-end` did arrive is `state === "done"`
 * and keeps the clean header.
 */
export function chipStateOf(part: ReasoningPartLike, chatActive: boolean): ChipState {
  if (part.state === "streaming") {
    return chatActive ? "streaming" : "aborted";
  }
  return "done";
}

/**
 * Expansion derivation (Claude.ai style): only the currently streaming chip
 * is expanded — a part collapses the moment it completes or the stream ends.
 * The user's explicit toggle overrides the derivation in both directions.
 */
export function isChipExpanded(chipState: ChipState, override: boolean | undefined): boolean {
  return override ?? chipState === "streaming";
}

export function chipHeaderLabel(chipState: ChipState, seconds: number, stalled: boolean): string {
  if (chipState === "streaming") {
    return stalled ? "Still working…" : "Thinking…";
  }
  if (chipState === "aborted") {
    return `Stopped — thought for ${seconds}s`;
  }
  return `Thought for ${seconds}s`;
}

/** Stable key for the timer and override maps — part ids are turn-unique but
 * reused across turns (the backend counter restarts per request), so scope
 * them by message id. */
export function chipKey(messageId: string, partIndex: number): string {
  return `${messageId}:${partIndex}`;
}
