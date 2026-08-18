import { useCallback, useEffect, useRef, useState } from "react";
import { STALL_THRESHOLD_MS } from "@/lib/timing";

/**
 * Global single stall stopwatch. Wall-clock based: `stalled` flips true
 * when `STALL_THRESHOLD_MS` elapse with no `notifyActivity()` call while
 * `active`.
 * Any stream part arrival must call `notifyActivity()` (the caller watches
 * `useChat.messages` — every part/delta arrival re-renders it). Deactivation
 * (turn end) resets the stopwatch so no stale value leaks into the next turn.
 *
 * Wall-clock (`Date.now()` delta) rather than an interval tick-counter so
 * background-tab timer throttling cannot under-count: a late-firing timeout
 * re-checks real elapsed time before flipping.
 */
export function useStallTimer(active: boolean) {
  const [stalled, setStalled] = useState(false);
  const lastActivityRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const activeRef = useRef(active);

  useEffect(() => {
    activeRef.current = active;
  }, [active]);

  const clearTimer = () => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  const scheduleCheck = useCallback(() => {
    clearTimer();
    const check = () => {
      timerRef.current = null;
      if (!activeRef.current) return;
      const elapsed = Date.now() - lastActivityRef.current;
      if (elapsed >= STALL_THRESHOLD_MS) {
        setStalled(true);
      } else {
        // The pending check is deliberately not rescheduled on activity, so
        // it fires against a deadline that has since moved — re-arm for the
        // remainder. This is the normal path while a stream is flowing; it
        // also absorbs a timeout that fires early relative to wall-clock.
        timerRef.current = setTimeout(check, STALL_THRESHOLD_MS - elapsed);
      }
    };
    timerRef.current = setTimeout(check, STALL_THRESHOLD_MS);
  }, []);

  const notifyActivity = useCallback(() => {
    lastActivityRef.current = Date.now();
    setStalled((prev) => (prev ? false : prev));
    // A check already in flight needs no rescheduling: when it fires it
    // re-arms itself for the remaining wall-clock time (see scheduleCheck).
    // Arming only when nothing is pending keeps the stream's ~20 activity
    // notifications per second from tearing down and rebuilding a timeout
    // each time.
    if (activeRef.current && timerRef.current === null) scheduleCheck();
  }, [scheduleCheck]);

  useEffect(() => {
    if (active) {
      // Turn start counts as activity: the stopwatch starts from zero and
      // no stale elapsed time from a prior (e.g. aborted) turn leaks in.
      lastActivityRef.current = Date.now();
      scheduleCheck();
    } else {
      clearTimer();
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect -- deliberate: turn-boundary reset must clear a stale stalled flag before the next paint
    setStalled((prev) => (prev ? false : prev));
    return clearTimer;
  }, [active, scheduleCheck]);

  return { stalled, notifyActivity };
}
