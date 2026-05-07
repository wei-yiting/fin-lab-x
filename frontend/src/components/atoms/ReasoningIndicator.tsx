interface ReasoningIndicatorProps {
  text?: string | null;
  state?: "streaming" | "frozen";
  stalled?: boolean;
}

// The reasoning text from `data-reasoning-status` events tends to arrive
// with a trailing sentence-ending punctuation (provider-emitted "...",
// ". ", "。", "，" etc.). When the dots cycler renders right after that
// trailing delim, the user sees "Analyzing your request. ..." which
// reads as two collapsed dot patterns instead of one loader. Strip the
// trailing whitespace + punctuation so the cycler dots flow naturally
// after the last meaningful character.
function trimTrailingDelim(text: string): string {
  return text.replace(/[.,;:!?。，；：！？、…\s]+$/u, "");
}

export function ReasoningIndicator({
  text,
  state = "streaming",
  stalled = false,
}: ReasoningIndicatorProps = {}) {
  const wrapperClass = stalled ? "reasoning-status stalled" : "reasoning-status";
  const displayText = typeof text === "string" ? trimTrailingDelim(text) : text;

  // Frozen-without-text — Stop-A (abort during pre-response idle):
  // render only the STOPPED label inside the reasoning-status container so
  // the user keeps a vertical-slot signal that the turn was halted.
  if (!displayText && state === "frozen") {
    return (
      <div data-testid="reasoning-indicator" className={wrapperClass} aria-hidden="true">
        <span className="reasoning-status-frozen-label">STOPPED</span>
      </div>
    );
  }

  if (!displayText) {
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
          {displayText}
        </span>
        <span className="reasoning-status-frozen-label">STOPPED</span>
      </div>
    );
  }

  return (
    <div data-testid="reasoning-indicator" className={wrapperClass} aria-hidden="true">
      <span className="reasoning-status-text">{displayText}</span>
      <span className="reasoning-status-dots-cycler" />
    </div>
  );
}
