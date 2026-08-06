/**
 * Pure derivation helpers for reasoning chips (F6′ / ADR-0008 + DEV-109
 * ruling 11). Everything here derives from `useChat`'s `(status, messages)`
 * — the five allowed non-derived stores live across ChatPanel and the hooks
 * it composes (chip timing map, global stall stopwatch, expand/collapse
 * override map, placeholder grace timer, turn interruption record). See
 * `hooks/README.md` for the full budget and each store's owner.
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

export type ChipState = "streaming" | "done" | "aborted";

export function isReasoningPart(part: {
  type?: unknown;
}): part is ReasoningPartLike & { type: "reasoning" } {
  return part.type === "reasoning";
}

/**
 * Single source of truth for tool-part classification (m-1.2): mirrors AI
 * SDK 6's `isToolUIPart` (static `tool-${name}` parts + `dynamic-tool`).
 * Plain `"tool"` is not a real AI SDK UI part shape and is intentionally
 * not matched here — callers that need it must import this function rather
 * than hand-roll their own predicate.
 */
export function isToolPart(part: { type?: unknown }): boolean {
  return (
    typeof part.type === "string" && (part.type.startsWith("tool-") || part.type === "dynamic-tool")
  );
}

/**
 * Whether a part currently paints anything the user can see: a
 * non-suppressed reasoning chip, a tool card, or non-empty reply text.
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
  // Text renders only if it has visible content: AssistantMessage trims
  // trailing whitespace off the concatenated text and skips the render
  // block entirely when the result is empty (M-1.2), so a whitespace-only
  // delta must not be treated as painted content either — otherwise a
  // dead-air window ends while the screen still shows nothing new.
  if (part.type === "text") return ((part as { text?: string }).text ?? "").trim() !== "";
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
 * Zero-delta suppression (decision 3): a part that closed without ever
 * carrying a single delta renders no chip at all. A chip whose streamed
 * content happens to be whitespace-only DID stream — it stays (no
 * flash-then-vanish removal).
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
 * Expansion derivation (decision 1, Claude.ai style): only the currently
 * streaming chip is expanded — a part collapses the moment it completes or
 * the stream ends. The user's explicit toggle overrides the derivation in
 * both directions (S-chip-05).
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

/** Stable key for timer refs / override map — part ids are turn-unique but
 * reused across turns (the backend counter restarts per request), so scope
 * them by message id. */
export function chipKey(messageId: string, partIndex: number): string {
  return `${messageId}:${partIndex}`;
}
