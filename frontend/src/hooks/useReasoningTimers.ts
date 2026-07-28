import { useCallback, useRef } from "react";
import { chipKey, isReasoningPart } from "@/lib/reasoning-chips";

interface ChipTiming {
  startedAt: number;
  frozenMs: number | null;
}

interface MessageLike {
  id: string;
  role: string;
  parts: Array<{ type?: unknown }>;
}

/**
 * Client-side "Thought for Xs" measurement (parts carry no timestamps —
 * ADR-0006 allows this as deliberate non-derived state).
 *
 * Semantics (decision 2): a chip's clock starts when its part first appears
 * and freezes at the arrival of the round's next part — for a tool round
 * that is the first tool-start, so tool execution time is excluded; for the
 * final round it is the reply text. An abort samples at Stop (the moment
 * the stream leaves the active status pair).
 *
 * Wall-clock delta (`Date.now()`), not an interval tick-counter, so
 * background-tab timer throttling cannot distort X.
 *
 * `observe` must be called during render (it is idempotent per render):
 * freezing happens on the very render triggered by the freezing event
 * (next-part arrival / status change), so no extra re-render is needed.
 */
export function useReasoningTimers() {
  const timingsRef = useRef<Map<string, ChipTiming>>(new Map());

  const observe = useCallback((messages: MessageLike[], chatActive: boolean) => {
    const now = Date.now();
    const timings = timingsRef.current;
    for (const msg of messages) {
      if (msg.role !== "assistant") continue;
      msg.parts.forEach((part, i) => {
        if (!isReasoningPart(part)) return;
        const key = chipKey(msg.id, i);
        let timing = timings.get(key);
        if (!timing) {
          timing = { startedAt: now, frozenMs: null };
          timings.set(key, timing);
        }
        if (timing.frozenMs === null) {
          const hasLaterPart = msg.parts.length > i + 1;
          if (hasLaterPart || !chatActive) {
            timing.frozenMs = now - timing.startedAt;
          }
        }
      });
    }
  }, []);

  const getSeconds = useCallback((key: string): number => {
    const timing = timingsRef.current.get(key);
    if (!timing) return 0;
    const ms = timing.frozenMs ?? Date.now() - timing.startedAt;
    return Math.max(0, Math.round(ms / 1000));
  }, []);

  const reset = useCallback(() => {
    timingsRef.current.clear();
  }, []);

  return { observe, getSeconds, reset };
}
