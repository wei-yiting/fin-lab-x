import type { ErrorClass } from "@/models";

export interface ErrorContext {
  source: "pre-stream-http" | "mid-stream-sse" | "tool-output-error" | "network";
  status?: number;
  rawMessage?: string;
}

export interface FriendlyError {
  title: string;
  detail?: string;
  retriable: boolean;
}

interface PreStreamHttpEntry {
  class: ErrorClass;
  title: string;
  retriable: boolean;
}

export const preStreamHttpMap: Record<number, PreStreamHttpEntry> = {
  422: {
    class: "pre-stream-422",
    title: "Couldn't regenerate that message. Please try again.",
    retriable: true,
  },
  404: {
    class: "pre-stream-404",
    title: "Conversation not found. Refresh to start a new one.",
    retriable: false,
  },
  409: {
    class: "pre-stream-409",
    title: "The system is busy. Please try again in a moment.",
    retriable: true,
  },
  500: { class: "pre-stream-500", title: "Server error. Please try again.", retriable: true },
};

const toolOutputPatterns: Array<{ pattern: RegExp; title: string; retriable: boolean }> = [
  {
    pattern: /rate limit/i,
    title: "Too many requests. Please wait a moment and try again.",
    retriable: true,
  },
  { pattern: /not found/i, title: "We couldn't find that data.", retriable: false },
  { pattern: /timeout/i, title: "The tool timed out. Please try again.", retriable: true },
  {
    pattern: /permission denied|forbidden/i,
    title: "Access denied for this resource.",
    retriable: false,
  },
];

const midStreamPatterns: Array<{ pattern: RegExp; title: string; retriable: boolean }> = [
  {
    pattern: /context length exceeded|token limit/i,
    title: "This conversation is too long. Start a new chat to continue.",
    retriable: false,
  },
  {
    pattern: /rate limit/i,
    title: "The system is busy. Please try again in a moment.",
    retriable: true,
  },
];

function matchPattern(
  rawMessage: string | undefined,
  patterns: Array<{ pattern: RegExp; title: string; retriable: boolean }>,
  fallback: { title: string; retriable: boolean },
): { title: string; retriable: boolean } {
  if (rawMessage) {
    for (const { pattern, title, retriable } of patterns) {
      if (pattern.test(rawMessage)) {
        return { title, retriable };
      }
    }
  }
  return fallback;
}

export function toFriendlyError(ctx: ErrorContext): FriendlyError {
  const detail = ctx.rawMessage ?? undefined;

  switch (ctx.source) {
    case "pre-stream-http": {
      const mapped = ctx.status !== undefined ? preStreamHttpMap[ctx.status] : undefined;
      if (mapped) {
        return { title: mapped.title, retriable: mapped.retriable, detail };
      }
      return { title: "Something went wrong. Please try again.", retriable: true, detail };
    }

    case "network":
      return {
        title: "Connection lost. Check your network and try again.",
        retriable: true,
        detail,
      };

    case "tool-output-error": {
      const matched = matchPattern(ctx.rawMessage, toolOutputPatterns, {
        title: "The tool failed to run. Please try again.",
        retriable: true,
      });
      return { ...matched, detail };
    }

    case "mid-stream-sse": {
      const matched = matchPattern(ctx.rawMessage, midStreamPatterns, {
        title: "Something went wrong while generating the response. Please try again.",
        retriable: true,
      });
      return { ...matched, detail };
    }
  }
}
