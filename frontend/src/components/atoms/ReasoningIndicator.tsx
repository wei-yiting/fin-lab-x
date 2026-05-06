interface ReasoningIndicatorProps {
  text?: string | null;
  state?: "streaming" | "frozen";
  stalled?: boolean;
}

export function ReasoningIndicator({
  text,
  state = "streaming",
  stalled = false,
}: ReasoningIndicatorProps = {}) {
  const wrapperClass = stalled ? "reasoning-status stalled" : "reasoning-status";

  // Frozen-without-text — Stop-A (abort during pre-response idle):
  // render only the STOPPED label inside the reasoning-status container so
  // the user keeps a vertical-slot signal that the turn was halted.
  if (!text && state === "frozen") {
    return (
      <div data-testid="reasoning-indicator" className={wrapperClass} aria-hidden="true">
        <span className="reasoning-status-frozen-label">STOPPED</span>
      </div>
    );
  }

  if (!text) {
    return (
      <div data-testid="reasoning-indicator" className={wrapperClass} aria-hidden="true">
        <span className="idle-dots">
          <span />
          <span />
          <span />
        </span>
      </div>
    );
  }

  if (state === "frozen") {
    return (
      <div data-testid="reasoning-indicator" className={wrapperClass} aria-hidden="true">
        <span className="reasoning-status-text" style={{ opacity: 0.65 }}>
          {text}
        </span>
        <span className="reasoning-status-frozen-label">STOPPED</span>
      </div>
    );
  }

  return (
    <div data-testid="reasoning-indicator" className={wrapperClass} aria-hidden="true">
      <span className="reasoning-status-text">{text}</span>
      <span className="reasoning-status-dots-cycler" />
    </div>
  );
}
