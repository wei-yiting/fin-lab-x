import { useCallback, useState } from "react";
import { chipKey, isReasoningPart } from "@/lib/reasoning-chips";
import type { ChatMessageLike } from "@/lib/reasoning-chips";

interface ChipTiming {
  startedAt: number;
  frozenMs: number | null;
}

/**
 * Client-side copy.reasoningChip.thoughtFor measurement (parts carry no
 * timestamps — ADR-0015 allows this as deliberate non-derived state).
 *
 * Semantics: a chip's clock starts when its part first appears
 * and freezes at the arrival of the round's next part — for a tool round
 * that is the first tool-start, so tool execution time is excluded; for the
 * final round it is the reply text. An abort samples at Stop (the moment
 * the stream leaves the active status pair).
 *
 * Wall-clock delta (`Date.now()`), not an interval tick-counter, so
 * background-tab timer throttling cannot distort X.
 *
 * The map lives in React state, so `getSeconds` may be called during render.
 * `observe` may not: it schedules a state update, so the consumer calls it
 * from a `useLayoutEffect`. It is idempotent, and its updater returns the
 * previous map unchanged whenever no chip was added or frozen, so React bails
 * out and re-running it after every commit cannot loop. The updater is pure
 * given the `now` sampled in the function body (never inside the updater —
 * StrictMode invokes updaters twice, and two timestamps would diverge), and
 * it never mutates a `ChipTiming`: freezing writes a new object into a cloned
 * map.
 *
 * One deliberate residual impurity: for a chip that is `done` but not yet
 * frozen (`reasoning-end` arrived, the next part has not), `getSeconds` reads
 * `Date.now()` during render. A pure alternative would need a ticking timer to
 * re-render, and the header deliberately does not tick.
 */
export function useReasoningTimers() {
  const [timings, setTimings] = useState<Map<string, ChipTiming>>(() => new Map());

  const observe = useCallback((messages: ChatMessageLike[], chatActive: boolean) => {
    const now = Date.now();
    setTimings((prev) => {
      let next: Map<string, ChipTiming> | null = null;
      for (const msg of messages) {
        if (msg.role !== "assistant") continue;
        msg.parts.forEach((part, i) => {
          if (!isReasoningPart(part)) return;
          const key = chipKey(msg.id, i);
          let timing = (next ?? prev).get(key);
          if (!timing) {
            timing = { startedAt: now, frozenMs: null };
            next ??= new Map(prev);
            next.set(key, timing);
          }
          if (timing.frozenMs === null) {
            const hasLaterPart = msg.parts.length > i + 1;
            if (hasLaterPart || !chatActive) {
              next ??= new Map(prev);
              next.set(key, { ...timing, frozenMs: now - timing.startedAt });
            }
          }
        });
      }
      return next ?? prev;
    });
  }, []);

  const getSeconds = useCallback(
    (key: string): number => {
      const timing = timings.get(key);
      if (!timing) return 0;
      const ms = timing.frozenMs ?? Date.now() - timing.startedAt;
      return Math.max(0, Math.round(ms / 1000));
    },
    [timings],
  );

  const reset = useCallback(() => {
    setTimings(new Map());
  }, []);

  return { observe, getSeconds, reset };
}
