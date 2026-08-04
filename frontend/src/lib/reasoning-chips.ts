/**
 * Pure derivation helpers for reasoning chips (F6′ / ADR-0008).
 * Everything here derives from `useChat`'s `(status, messages)` — the four
 * allowed non-derived stores live in ChatPanel and useDeadAirPlaceholder
 * (chip timing map, global stall stopwatch, expand/collapse override map,
 * placeholder grace timer).
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

export function isToolPart(part: { type?: unknown }): boolean {
  return (
    part.type === "tool" ||
    part.type === "dynamic-tool" ||
    (typeof part.type === "string" && part.type.startsWith("tool-"))
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
  if (part.type === "text") return ((part as { text?: string }).text ?? "") !== "";
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
