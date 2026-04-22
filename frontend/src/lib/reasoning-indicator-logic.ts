import type { ChatStatus } from "@/models";
import type { UIMessage } from "@ai-sdk/react";

/**
 * Whether the "AI is reasoning" dot indicator should appear.
 *
 * The indicator fills the pre-response gap — after the user sends a
 * turn but before the assistant has streamed anything visible. Once
 * any part (text / tool) lands in the last assistant message, the
 * inline `Cursor` takes over at the tail of the Markdown, so we
 * suppress the separate indicator to avoid double-signaling.
 */
export function shouldShowReasoningIndicator(args: {
  status: ChatStatus;
  lastMessage: Pick<UIMessage, "role" | "parts"> | null;
}): boolean {
  const { status, lastMessage } = args;

  if (status === "ready" || status === "error") return false;

  if (!lastMessage || lastMessage.role !== "assistant") return true;

  return lastMessage.parts.length === 0;
}
