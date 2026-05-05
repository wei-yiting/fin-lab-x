import type { ChatStatus } from "@/models";

export interface AnnouncedEvent {
  type:
    | "start"
    | "tool-input-available"
    | "tool-output-available"
    | "tool-output-error"
    | "finish";
  toolName?: string;
  errorText?: string;
}

// Pure mapping from (status, lastEvent) → announcement string. Exported so
// the transition table can be unit-tested without mounting the component.
// `status === "error"` always wins so SR announces failures even if the last
// successful event was something else.
export function formatStatusText(
  status: ChatStatus,
  lastEvent: AnnouncedEvent | null,
): string {
  if (status === "error") {
    const detail = lastEvent?.errorText ?? "stream interrupted";
    return `Error: ${detail}`;
  }

  if (!lastEvent) return "";

  switch (lastEvent.type) {
    case "start":
      return "Generating response";
    case "tool-input-available": {
      const name = lastEvent.toolName ?? "tool";
      return `Calling ${name}`;
    }
    case "tool-output-available": {
      const name = lastEvent.toolName ?? "tool";
      return `Tool ${name} completed`;
    }
    case "tool-output-error": {
      const name = lastEvent.toolName ?? "tool";
      return `Tool ${name} failed`;
    }
    case "finish":
      return "Response complete";
    default:
      return "";
  }
}
