import { copy } from "@/lib/copy";

interface ActivityPlaceholderProps {
  /** Swaps in the degraded copy; driven by the global stall stopwatch. */
  stalled: boolean;
}

/**
 * Dead-air placeholder: fills the three windows where the screen has no
 * live element — (A) submit → first renderable content, (B) reasoning chip
 * collapse → next content, (C) tool round complete (every tool part terminal)
 * → next content. Never contains reasoning text. Visibility is derived by the
 * parent via `useDeadAirPlaceholder`, which suppresses it while a chip is
 * streaming or a tool card is still *running*; window C is exactly the case
 * where it renders beneath *completed* tool cards, which are not live
 * elements.
 */
export function ActivityPlaceholder({ stalled }: ActivityPlaceholderProps) {
  return (
    <div
      data-testid="activity-placeholder"
      aria-live="polite"
      className="streaming-shimmer px-3 text-sm text-muted-foreground"
    >
      {stalled ? copy.activityIndicator.stalled : copy.activityIndicator.thinking}
      {/* aria-hidden so the CSS content cycler never spams the polite queue. */}
      <span aria-hidden="true" className="thinking-dots" />
    </div>
  );
}
