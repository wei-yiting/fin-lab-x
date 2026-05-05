import { isRunningToolState, type ChatStatus } from "@/models";
import type { UIMessage } from "@ai-sdk/react";

export const IDLE_SYNTHESIZING_TEXT = "Synthesizing";
// reserved for future heuristic per D15
export const IDLE_THINKING_TEXT = "Thinking";

/**
 * Whether the "AI is reasoning" dot indicator should appear.
 *
 * The indicator fills the pre-response gap — after the user sends a
 * turn but before the assistant has streamed anything visible. Once
 * any part (text / tool) lands in the last assistant message, the
 * inline `Cursor` takes over at the tail of the Markdown, so we
 * suppress the separate indicator to avoid double-signaling.
 *
 * Two extra branches per D15 §7.4:
 *  - `reasoningStatusText` truthy → always show (real reasoning takes
 *    precedence; idle-text path is suppressed by the caller).
 *  - Post-tool gap: last part is a completed tool and the stream is
 *    still running → show indicator while waiting for the next text /
 *    reasoning event (S-rsn-07).
 */
export function shouldShowReasoningIndicator(args: {
  status: ChatStatus;
  lastMessage: Pick<UIMessage, "role" | "parts"> | null;
  reasoningStatusText: string | null;
}): boolean {
  const { status, lastMessage, reasoningStatusText } = args;

  if (status === "ready" || status === "error") return false;

  if (!lastMessage || lastMessage.role !== "assistant") return true;

  if (reasoningStatusText) return true;

  if (lastMessage.parts.length === 0) return true;

  const lastPart = lastMessage.parts.at(-1);
  if (lastPart && isCompletedToolPart(lastPart) && status === "streaming") {
    return true;
  }

  return false;
}

/**
 * Resolve the display text for the reasoning indicator.
 *
 * Returns `null` when the indicator should render in 3-dot idle mode
 * (no inline label) or not render at all — the caller decides which
 * based on `shouldShowReasoningIndicator`.
 *
 * Precedence (D15 §7.4):
 *  1. Real reasoning status text passes through verbatim.
 *  2. Streaming + completed tool last part → idle "Synthesizing".
 *  3. Otherwise null (no idle text).
 */
export function resolveReasoningDisplayText(args: {
  reasoningStatusText: string | null;
  status: ChatStatus;
  lastMessage: Pick<UIMessage, "role" | "parts"> | null;
}): string | null {
  const { reasoningStatusText, status, lastMessage } = args;

  if (reasoningStatusText) return reasoningStatusText;
  if (status !== "streaming") return null;
  if (!lastMessage || lastMessage.role !== "assistant") return null;

  const lastPart = lastMessage.parts.at(-1);
  if (lastPart && isCompletedToolPart(lastPart)) return IDLE_SYNTHESIZING_TEXT;

  return null;
}

function isCompletedToolPart(part: { type?: unknown; state?: unknown }): boolean {
  if (typeof part.type !== "string") return false;
  if (!part.type.startsWith("tool-") && part.type !== "dynamic-tool") return false;
  return !isRunningToolState(part.state as string);
}
