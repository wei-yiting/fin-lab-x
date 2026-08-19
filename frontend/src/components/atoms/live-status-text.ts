export interface AnnouncedEvent {
  type: "finish";
}

// Pure mapping from lastEvent → announcement string. Exported so the
// transition table can be unit-tested without mounting the component.
//
// AI SDK v6 routes generic SSE chunks (start, tool-input-available,
// tool-output-available, tool-output-error) through state callbacks that are
// not exposed via onData (gated by isDataUIMessageChunk in
// node_modules/ai/dist/index.mjs:5765). Only `finish` reaches us — and it
// arrives via onFinish, not onData. Tool-call announcements would require a
// messages.parts watcher and are deferred.
//
// Errors are announced separately by ErrorBlock's role="alert" — this
// announcer only ever represents the natural-completion event, so a failure
// is never read out twice.
export function formatStatusText(lastEvent: AnnouncedEvent | null): string {
  if (!lastEvent) return "";

  if (lastEvent.type === "finish") return "Response complete";
  return "";
}
