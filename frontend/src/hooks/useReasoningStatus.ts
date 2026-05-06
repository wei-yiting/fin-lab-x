import { useCallback, useEffect, useRef, useState } from "react";

export const STALLED_THRESHOLD_MS = 10_000;

export type ReasoningStatusDataPart = {
  type: string;
  id?: string;
  data?: { text?: string };
};

export function useReasoningStatus() {
  const [reasoningStatusText, setText] = useState<string | null>(null);
  const [stalled, setStalled] = useState(false);
  // D31 guards: refs (not state) so synchronous handleData can short-circuit
  // without waiting for a re-render after clear/finish.
  const clearedRef = useRef(false);
  const finishedRef = useRef(false);
  // D14: track wall-clock time of the most recent reasoning chunk so the
  // polling interval can flip stalled true after STALLED_THRESHOLD_MS of silence.
  const lastUpdateAtRef = useRef<number>(0);

  const handleData = useCallback((part: ReasoningStatusDataPart) => {
    if (clearedRef.current || finishedRef.current) return;

    // AI SDK v6 only routes `data-*` chunks through onData. Other SSE events
    // (text-start, tool-input-available) historically had branches here but
    // never fired — they are dispatched via the messages array now and
    // observed by ChatPanel's layoutEffect that calls hideReasoningStatus().
    switch (part.type) {
      case "data-reasoning-status": {
        if (typeof part.data?.text === "string") {
          setText(part.data.text);
          lastUpdateAtRef.current = Date.now();
          setStalled(false);
        }
        return;
      }
      case "finish":
      case "error": {
        setText(null);
        setStalled(false);
        finishedRef.current = true;
        return;
      }
      default:
        return;
    }
  }, []);

  // Two cleanup verbs with different guard semantics:
  //
  //   hideReasoningStatus(): blank the indicator without latching the
  //     clearedRef guard. Use mid-turn — when text/tool parts appear and the
  //     previous LLM call's reasoning is now stale. The next reasoning chunk
  //     for the next LLM call is allowed back through handleData.
  //
  //   clearReasoningStatus(): same blank PLUS latch clearedRef so any
  //     in-flight buffered SSE events that arrive after the clear are
  //     silently dropped. Use only when the user explicitly clears the
  //     conversation (D31 race protection).
  const hideReasoningStatus = useCallback(() => {
    setText(null);
    setStalled(false);
  }, []);

  const clearReasoningStatus = useCallback(() => {
    setText(null);
    setStalled(false);
    clearedRef.current = true;
  }, []);

  const resetForNewTurn = useCallback(() => {
    setText(null);
    setStalled(false);
    clearedRef.current = false;
    finishedRef.current = false;
  }, []);

  // Only poll while there is reasoning text to watch. Idle state would burn a
  // wakeup every second for nothing; gating on `reasoningStatusText` keeps the
  // interval scoped to the active streaming window.
  useEffect(() => {
    if (reasoningStatusText === null) return;
    const id = setInterval(() => {
      if (Date.now() - lastUpdateAtRef.current > STALLED_THRESHOLD_MS) {
        setStalled(true);
      }
    }, 1_000);
    return () => clearInterval(id);
  }, [reasoningStatusText]);

  return {
    reasoningStatusText,
    stalled,
    handleData,
    hideReasoningStatus,
    clearReasoningStatus,
    resetForNewTurn,
  };
}
