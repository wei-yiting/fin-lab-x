import type { ChatStatus } from "@/models";

export interface AnnouncedEvent {
  type: "finish";
  errorText?: string;
}

// Pure mapping from (status, lastEvent) → announcement string. Exported so
// the transition table can be unit-tested without mounting the component.
// `status === "error"` always wins so SR announces failures even if the last
// successful event was something else.
//
// AI SDK v6 routes generic SSE chunks (start, tool-input-available,
// tool-output-available, tool-output-error) through state callbacks that are
// not exposed via onData (gated by isDataUIMessageChunk in
// node_modules/ai/dist/index.mjs:5765). Only `finish` reaches us — and it
// arrives via onFinish, not onData. Tool-call announcements would require a
// messages.parts watcher and are deferred.
export function formatStatusText(status: ChatStatus, lastEvent: AnnouncedEvent | null): string {
  if (status === "error") {
    const detail = lastEvent?.errorText ?? "stream interrupted";
    return `Error: ${detail}`;
  }

  if (!lastEvent) return "";

  if (lastEvent.type === "finish") return "Response complete";
  return "";
}
