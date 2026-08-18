import { useEffect, useState } from "react";
import { PLACEHOLDER_GRACE_MS } from "@/lib/timing";
import {
  isReasoningPart,
  isRenderablePart,
  isToolPart,
  turnHasRenderableContent,
} from "@/lib/reasoning-chips";
import type { ChatMessageLike } from "@/lib/reasoning-chips";
import type { ChatStatus } from "@/models";

export type PlaceholderState = "hidden" | "waiting";

/** Tool part states with nothing left in flight (result or error landed). */
const TERMINAL_TOOL_STATES = new Set(["output-available", "output-error"]);

/**
 * Placeholder visibility (3 states — Hidden / Waiting / Waiting+degraded;
 * the degraded copy swap is the caller's concern via the stall stopwatch).
 *
 * Covers three dead-air windows:
 *   (a) submit → first *renderable* content. `status === "submitted"` alone
 *       ends at the stream's first wire frame (`start`), which arrives
 *       seconds before anything paints — reasoning deltas can lag
 *       `reasoning-start` by several seconds, and zero-delta reasoning
 *       blocks never paint at all — so the window extends through
 *       "streaming but nothing renderable yet". Monotonic per turn: once
 *       any content renders, parts never un-render, so this can't flash
 *       back on mid-turn (no grace delay needed).
 *   (b) chip collapse → reply text — the last *renderable* part of the
 *       streaming assistant message is a completed reasoning part, held
 *       behind a grace delay so the chip→tool micro-gap (where the tool
 *       card itself owns the feedback) never flashes the placeholder.
 *   (c) tool round complete → next content: every tool
 *       part has its result and nothing renderable has arrived after —
 *       completed tool cards are not live elements, so the wait for the
 *       next LLM call is dead air. Same grace delay as (b).
 *
 * Windows (b)/(c) look at the last *renderable* part, not the raw last
 * part: a mid-turn `reasoning-start` whose first delta is still seconds
 * away appends an invisible part, and ending the window there would drop
 * the placeholder while the screen still shows nothing new (observed in
 * manual testing during DEV-109 verification). Invisible trailing parts neither close
 * the window nor restart its grace timer.
 *
 * Never visible while a chip is streaming or a tool card is live.
 */
export function useDeadAirPlaceholder(
  messages: ChatMessageLike[],
  status: ChatStatus,
): PlaceholderState {
  // The gap that has outlived the grace delay, identified by message id +
  // index of the last renderable part (stable while invisible parts append,
  // so an arriving `reasoning-start` doesn't blink the placeholder off).
  // Stale values are harmless: they only match while the same gap is open.
  const [elapsedGapKey, setElapsedGapKey] = useState<string | null>(null);

  const last = messages.at(-1);
  const windowA =
    status === "submitted" ||
    (status === "streaming" &&
      (!last || last.role !== "assistant" || !turnHasRenderableContent(last)));

  let windowB = false;
  let windowC = false;
  let lastRenderableIndex = -1;
  if (status === "streaming" && last && last.role === "assistant" && last.parts.length > 0) {
    lastRenderableIndex = last.parts.findLastIndex(isRenderablePart);
    const anchor = lastRenderableIndex >= 0 ? last.parts[lastRenderableIndex] : undefined;
    if (anchor) {
      windowB = isReasoningPart(anchor) && anchor.state !== "streaming";
      windowC =
        isToolPart(anchor) &&
        last.parts.every(
          (part) => !isToolPart(part) || TERMINAL_TOOL_STATES.has(String(part.state)),
        );
    }
  }
  const gapKey = (windowB || windowC) && last ? `${last.id}:${lastRenderableIndex}` : null;

  useEffect(() => {
    if (gapKey === null) return;
    const timer = setTimeout(() => setElapsedGapKey(gapKey), PLACEHOLDER_GRACE_MS);
    return () => clearTimeout(timer);
  }, [gapKey]);

  if (windowA) return "waiting";
  if ((windowB || windowC) && elapsedGapKey === gapKey) return "waiting";
  return "hidden";
}
