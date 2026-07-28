/**
 * Pure derivation helpers for reasoning chips (F6′ / ADR-0006).
 * Everything here derives from `useChat`'s `(status, messages)` — the only
 * allowed non-derived stores live in ChatPanel (chip timing map, global
 * stall stopwatch, expand/collapse override map).
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
