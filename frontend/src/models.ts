import type { UIMessage } from "@ai-sdk/react"

export type ChatMessage = UIMessage
export type ChatStatus = "submitted" | "streaming" | "ready" | "error"
export type ChatId = string
export type ToolCallId = string
export type ToolProgressMessage = string
export type ToolProgressRecord = Record<ToolCallId, ToolProgressMessage>
export type ToolUIState =
  | "input-streaming"
  | "input-available"
  | "output-available"
  | "output-error"
  | "aborted"

export type SourceRef = {
  label: string
  url: string
  title?: string
  hostname: string
}
export type ExtractedSources = ReadonlyArray<SourceRef>
