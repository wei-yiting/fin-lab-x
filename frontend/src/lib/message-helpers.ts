import type { UIMessage } from "@ai-sdk/react";

export function findOriginalUserText(messages: UIMessage[], assistantMessageId: string): string {
  const index = messages.findIndex((m) => m.id === assistantMessageId);
  if (index < 1) return "";

  const prev = messages[index - 1];
  if (prev.role !== "user") return "";

  const textPart = prev.parts?.find((p) => p.type === "text");
  if (textPart && textPart.type === "text") return textPart.text;

  return "";
}
