interface ActivityPlaceholderProps {
  /** Degraded copy swap (decision C4) driven by the global stall stopwatch. */
  stalled: boolean;
}

/**
 * Dead-air placeholder (F6′): fills the two windows where the screen has no
 * live element — submit → first content, chip collapse → reply text. Never
 * contains reasoning text; never rendered while a tool card or streaming
 * chip is on screen (the parent derives visibility).
 */
export function ActivityPlaceholder({ stalled }: ActivityPlaceholderProps) {
  return (
    <div
      data-testid="activity-placeholder"
      aria-live="polite"
      className="streaming-shimmer px-3 text-sm text-muted-foreground"
    >
      {stalled ? "Still working" : "Thinking"}
      {/* aria-hidden so the CSS content cycler never spams the polite queue. */}
      <span aria-hidden="true" className="thinking-dots" />
    </div>
  );
}
