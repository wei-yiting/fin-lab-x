import type { ErrorClass } from "@/models";
import { copy } from "@/lib/copy";

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
    title: copy.errorMessages.regenerateFailed,
    retriable: true,
  },
  404: {
    class: "pre-stream-404",
    title: copy.errorMessages.conversationNotFound,
    retriable: false,
  },
  409: {
    class: "pre-stream-409",
    title: copy.errorMessages.sessionBusy,
    retriable: true,
  },
  500: { class: "pre-stream-500", title: copy.errorMessages.serverError, retriable: true },
};

const toolOutputPatterns: Array<{ pattern: RegExp; title: string; retriable: boolean }> = [
  {
    // Backend RunBudgetMiddleware sentinel — must be matched before
    // /rate limit/ so the budget message (which contains the phrase
    // "NOT an external rate limit" for the LLM's benefit) doesn't fall
    // through to the rate-limit case. Per-run budgets are not retriable
    // within the same request.
    pattern: /per-run tool-call budget reached/i,
    title: copy.errorMessages.toolBudgetReached,
    retriable: false,
  },
  {
    pattern: /rate limit/i,
    title: copy.errorMessages.tooManyRequests,
    retriable: true,
  },
  { pattern: /not found/i, title: copy.errorMessages.dataNotFound, retriable: false },
  { pattern: /timeout/i, title: copy.errorMessages.toolTimeout, retriable: true },
  {
    pattern: /permission denied|forbidden/i,
    title: copy.errorMessages.accessDenied,
    retriable: false,
  },
];

const midStreamPatterns: Array<{ pattern: RegExp; title: string; retriable: boolean }> = [
  {
    pattern: /context length exceeded|token limit/i,
    title: copy.errorMessages.conversationTooLong,
    retriable: false,
  },
  {
    pattern: /rate limit/i,
    title: copy.errorMessages.sessionBusy,
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
      return { title: copy.errorMessages.preStreamFallback, retriable: true, detail };
    }

    case "network":
      return {
        title: copy.errorMessages.networkError,
        retriable: true,
        detail,
      };

    case "tool-output-error": {
      const matched = matchPattern(ctx.rawMessage, toolOutputPatterns, {
        title: copy.errorMessages.toolFailedFallback,
        retriable: true,
      });
      return { ...matched, detail };
    }

    case "mid-stream-sse": {
      const matched = matchPattern(ctx.rawMessage, midStreamPatterns, {
        title: copy.errorMessages.midStreamFallback,
        retriable: true,
      });
      return { ...matched, detail };
    }
  }
}
