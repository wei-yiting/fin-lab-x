import type { ChatStatus } from "@/models";
import { formatStatusText, type AnnouncedEvent } from "./live-status-text";

interface LiveStatusAnnouncerProps {
  status: ChatStatus;
  lastEvent: AnnouncedEvent | null;
}

/**
 * Screen-reader announcer for chat lifecycle.
 *
 * Currently announces 'finish' (via onFinish) and 'error' (via status==='error').
 * Tool-call transitions are deferred — AI SDK v6 routes those through state
 * callbacks not exposed via onData.
 */
export function LiveStatusAnnouncer({ status, lastEvent }: LiveStatusAnnouncerProps) {
  const text = formatStatusText(status, lastEvent);

  return (
    <div role="status" aria-live="polite" className="sr-only">
      {text}
    </div>
  );
}

// Type-only re-export so consumers (Task 11 ChatPanel) can use a single
// import path. Type-only exports are exempt from react-refresh constraints.
export type { AnnouncedEvent } from "./live-status-text";
