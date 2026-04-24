import type { UIMessage } from "@ai-sdk/react";

export type ChatMessage = UIMessage;
export type ChatStatus = "submitted" | "streaming" | "ready" | "error";
export type ChatId = string;
export type ToolCallId = string;
export type ToolProgressMessage = string;
export type ToolProgressRecord = Record<ToolCallId, ToolProgressMessage>;
export type ToolUIState =
  | "input-streaming"
  | "input-available"
  | "output-available"
  | "output-error"
  | "aborted";

export const isRunningToolState = (state: string): boolean =>
  state === "input-streaming" || state === "input-available";

export type ErrorClass =
  | "pre-stream-422"
  | "pre-stream-404"
  | "pre-stream-409"
  | "pre-stream-500"
  | "pre-stream-5xx"
  | "network"
  | "mid-stream"
  | "unknown";

export interface SourceRef {
  label: string;
  url: string;
  title?: string;
  hostname: string;
}
export type ExtractedSources = ReadonlyArray<SourceRef>;
