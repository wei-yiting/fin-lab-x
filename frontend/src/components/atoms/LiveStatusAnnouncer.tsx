import type { ChatStatus } from "@/models";
import { formatStatusText, type AnnouncedEvent } from "./live-status-text";

interface LiveStatusAnnouncerProps {
  status: ChatStatus;
  lastEvent: AnnouncedEvent | null;
}

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
