import { useCallback, useRef, useState } from "react";

export type ReasoningStatusDataPart = {
  type: string;
  id?: string;
  data?: { text?: string };
};

export function useReasoningStatus() {
  const [reasoningStatusText, setText] = useState<string | null>(null);
  // D31 guards: refs (not state) so synchronous handleData can short-circuit
  // without waiting for a re-render after clear/finish.
  const clearedRef = useRef(false);
  const finishedRef = useRef(false);

  const handleData = useCallback((part: ReasoningStatusDataPart) => {
    if (clearedRef.current || finishedRef.current) return;

    switch (part.type) {
      case "data-reasoning-status": {
        if (typeof part.data?.text === "string") {
          setText(part.data.text);
        }
        return;
      }
      case "text-start":
      case "tool-input-available": {
        setText(null);
        return;
      }
      case "finish":
      case "error": {
        setText(null);
        finishedRef.current = true;
        return;
      }
      default:
        return;
    }
  }, []);

  const clearReasoningStatus = useCallback(() => {
    setText(null);
    clearedRef.current = true;
  }, []);

  const resetForNewTurn = useCallback(() => {
    setText(null);
    clearedRef.current = false;
    finishedRef.current = false;
  }, []);

  return {
    reasoningStatusText,
    handleData,
    clearReasoningStatus,
    resetForNewTurn,
  };
}
