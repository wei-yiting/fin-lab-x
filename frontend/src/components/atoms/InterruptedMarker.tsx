import { copy } from "@/lib/copy";

/**
 * Turn-level interruption marker: every user-initiated
 * Stop leaves an explicit copy.interruptedMarker.label row at the cut
 * point, Claude Code-style — regardless of whether a chip
 * (copy.reasoningChip.stoppedThoughtFor) or tool card
 * (copy.toolStatus.aborted) also carries abort state. Without it, a Stop
 * landing on the placeholder or mid-answer leaves no trace, and a
 * truncated answer reads as a complete one.
 */
export function InterruptedMarker() {
  return (
    <div
      data-testid="interrupted-marker"
      className="flex items-center gap-2 text-xs text-muted-foreground"
    >
      <span
        aria-hidden="true"
        className="inline-block h-2 w-2 rounded-full bg-[var(--status-aborted)]"
      />
      {copy.interruptedMarker.label}
    </div>
  );
}
