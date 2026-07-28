import { useEffect, useState } from "react";
import { PLACEHOLDER_GRACE_MS } from "@/lib/timing";
import { isReasoningPart, isSuppressedChip, turnHasRenderableContent } from "@/lib/reasoning-chips";
import type { ChatMessageLike } from "@/lib/reasoning-chips";
import type { ChatStatus } from "@/models";

export type PlaceholderState = "hidden" | "waiting";

/**
 * Placeholder visibility (F6′, 3 states — Hidden / Waiting / Waiting+degraded;
 * the degraded copy swap is the caller's concern via the stall stopwatch).
 *
 * Covers exactly the two dead-air windows (decision C1):
 *   (a) submit → first *renderable* content. `status === "submitted"` alone
 *       ends at the stream's first wire frame (`start`), which arrives
 *       seconds before anything paints — reasoning deltas can lag
 *       `reasoning-start` by several seconds, and zero-delta reasoning
 *       blocks never paint at all — so the window extends through
 *       "streaming but nothing renderable yet". Monotonic per turn: once
 *       any content renders, parts never un-render, so this can't flash
 *       back on mid-turn (no grace delay needed).
 *   (b) chip collapse → reply text — last part of the streaming assistant
 *       message is a completed reasoning part with nothing after it, held
 *       behind a grace delay so the chip→tool micro-gap (decision 5: tool
 *       card owns that feedback) never flashes the placeholder.
 *
 * Never visible while a chip is streaming or a tool card is live.
 */
export function useDeadAirPlaceholder(
  messages: ChatMessageLike[],
  status: ChatStatus,
  graceMs: number = PLACEHOLDER_GRACE_MS,
): PlaceholderState {
  // The gap that has outlived the grace delay, identified by message id +
  // part count. Stale values are harmless: they only match while the exact
  // same gap is still open.
  const [elapsedGapKey, setElapsedGapKey] = useState<string | null>(null);

  const last = messages.at(-1);
  const windowA =
    status === "submitted" ||
    (status === "streaming" &&
      (!last || last.role !== "assistant" || !turnHasRenderableContent(last)));

  let windowB = false;
  if (status === "streaming" && last && last.role === "assistant" && last.parts.length > 0) {
    const lastPart = last.parts.at(-1)!;
    windowB =
      isReasoningPart(lastPart) && lastPart.state !== "streaming" && !isSuppressedChip(lastPart);
  }
  const gapKey = windowB && last ? `${last.id}:${last.parts.length}` : null;

  useEffect(() => {
    if (gapKey === null || graceMs <= 0) return;
    const timer = setTimeout(() => setElapsedGapKey(gapKey), graceMs);
    return () => clearTimeout(timer);
  }, [gapKey, graceMs]);

  if (windowA) return "waiting";
  if (windowB && (graceMs <= 0 || elapsedGapKey === gapKey)) return "waiting";
  return "hidden";
}
