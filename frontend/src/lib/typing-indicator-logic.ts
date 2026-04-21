import type { ChatStatus } from "@/models";
import type { UIMessage } from "@ai-sdk/react";

export function shouldShowTypingIndicator(args: {
  status: ChatStatus;
  lastMessage: Pick<UIMessage, "role" | "parts"> | null;
}): boolean {
  const { status, lastMessage } = args;

  if (status === "ready" || status === "error") return false;

  if (!lastMessage || lastMessage.role !== "assistant") return true;

  return lastMessage.parts.length === 0;
}
