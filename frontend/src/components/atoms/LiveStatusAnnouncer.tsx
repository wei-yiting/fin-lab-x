import { formatStatusText, type AnnouncedEvent } from "./live-status-text";

interface LiveStatusAnnouncerProps {
  lastEvent: AnnouncedEvent | null;
}

/**
 * Screen-reader announcer for chat lifecycle.
 *
 * Announces only the natural-completion event ('finish', via onFinish).
 * Errors are announced separately by ErrorBlock's role="alert", so a failure
 * is never read out twice. Tool-call transitions are deferred — AI SDK v6
 * routes those through state callbacks not exposed via onData.
 */
export function LiveStatusAnnouncer({ lastEvent }: LiveStatusAnnouncerProps) {
  const text = formatStatusText(lastEvent);

  return (
    <div role="status" aria-live="polite" className="sr-only">
      {text}
    </div>
  );
}

// Type-only re-export so consumers (ChatPanel) can use a single import path.
// Type-only exports are exempt from react-refresh constraints.
export type { AnnouncedEvent } from "./live-status-text";
