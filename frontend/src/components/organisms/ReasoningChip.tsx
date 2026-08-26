import { useLayoutEffect, useRef } from "react";
import { chipHeaderLabel } from "@/lib/reasoning-chips";
import type { ChipState } from "@/lib/reasoning-chips";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { copy } from "@/lib/copy";

interface ReasoningChipProps {
  chipState: ChipState;
  text: string;
  /** "Thought for Xs" seconds — frozen upstream. */
  seconds: number;
  /**
   * Whether the global stall stopwatch has fired: a streaming chip's header
   * swaps to the degraded "Still working…" copy while it is true.
   */
  stalled: boolean;
  expanded: boolean;
  onToggle: () => void;
  /** 1-based ordinal of this chip within its message (test hook). */
  round: number;
}

/**
 * One reasoning part = one chip (ADR-0015). While streaming: full text in a
 * ~4-line pinned-bottom window (newest text visible, older scrolled away).
 * Collapsed: "Thought for Xs" header; aborted half-chips keep their text
 * behind a "Stopped — thought for Xs" header. Body is raw
 * `white-space: pre-wrap` (never markdown) so half-streamed markup can't
 * re-parse and jitter per delta; `overflow-wrap: anywhere` keeps the
 * pinned-scroll math valid for CJK/long tokens.
 *
 * Body visibility follows `expanded` alone, so an explicit collapse wins even
 * over a still-streaming part. `data-state` therefore tracks the part
 * lifecycle (`streaming` while the part is live, regardless of visibility)
 * while `aria-expanded` tracks visibility — the two are deliberately
 * decoupled.
 */
export function ReasoningChip({
  chipState,
  text,
  seconds,
  stalled,
  expanded,
  onToggle,
  round,
}: ReasoningChipProps) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const streaming = chipState === "streaming";
  const showBody = expanded;

  // Pin the newest text to the bottom of the streaming window before paint.
  // Only meaningful while the window is actually rendered; re-expanding a
  // streaming chip re-runs this and re-pins to the bottom.
  useLayoutEffect(() => {
    if (!streaming || !showBody) return;
    const el = bodyRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [text, streaming, showBody]);

  const dataState = streaming ? "streaming" : expanded ? "expanded" : "collapsed";
  const headerLabel = chipHeaderLabel(chipState, seconds, streaming && stalled);

  return (
    <div
      data-testid="reasoning-chip"
      data-state={dataState}
      data-round={round}
      className="mt-1 mb-4 rounded-lg border border-border bg-card"
    >
      <button
        type="button"
        data-testid="reasoning-chip-header"
        aria-expanded={showBody}
        aria-live="polite"
        aria-label={copy.reasoningChip.toggleAriaLabel(headerLabel, showBody)}
        onClick={onToggle}
        className={cn(
          "flex w-full items-center gap-1.5 px-3 py-2 text-left text-sm",
          streaming ? "text-foreground" : "text-muted-foreground",
        )}
      >
        <ChevronRight
          aria-hidden="true"
          className={cn("size-3.5 shrink-0 transition-transform", showBody && "rotate-90")}
        />
        <span className={cn(streaming && "streaming-shimmer")}>{headerLabel}</span>
      </button>
      {showBody && (
        <div
          ref={bodyRef}
          data-testid="reasoning-chip-body"
          className={cn(
            "px-3 pb-2 text-sm text-muted-foreground",
            "whitespace-pre-wrap [overflow-wrap:anywhere]",
            streaming && "reasoning-chip-window overflow-y-auto",
          )}
        >
          {text}
        </div>
      )}
    </div>
  );
}
