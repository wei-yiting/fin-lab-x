import type { ErrorClass } from "@/models";
import type { Copy } from "@/lib/copy";

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

/** Tables hold keys, not text, so the title resolves in the active locale at render time. */
type ErrorTitleKey = {
  [K in keyof Copy["errorMessages"]]: Copy["errorMessages"][K] extends string ? K : never;
}[keyof Copy["errorMessages"]];

interface PreStreamHttpEntry {
  class: ErrorClass;
  titleKey: ErrorTitleKey;
  retriable: boolean;
}

interface PatternEntry {
  pattern: RegExp;
  titleKey: ErrorTitleKey;
  retriable: boolean;
}

export const preStreamHttpMap: Record<number, PreStreamHttpEntry> = {
  422: {
    class: "pre-stream-422",
    titleKey: "regenerateFailed",
    retriable: true,
  },
  404: {
    class: "pre-stream-404",
    titleKey: "conversationNotFound",
    retriable: false,
  },
  409: {
    class: "pre-stream-409",
    titleKey: "sessionBusy",
    retriable: true,
  },
  500: { class: "pre-stream-500", titleKey: "serverError", retriable: true },
};

const toolOutputPatterns: PatternEntry[] = [
  {
    // Backend RunBudgetMiddleware sentinel — must be matched before
    // /rate limit/ so the budget message (which contains the phrase
    // "NOT an external rate limit" for the LLM's benefit) doesn't fall
    // through to the rate-limit case. Per-run budgets are not retriable
    // within the same request.
    pattern: /per-run tool-call budget reached/i,
    titleKey: "toolBudgetReached",
    retriable: false,
  },
  {
    pattern: /rate limit/i,
    titleKey: "tooManyRequests",
    retriable: true,
  },
  { pattern: /not found/i, titleKey: "dataNotFound", retriable: false },
  { pattern: /timeout/i, titleKey: "toolTimeout", retriable: true },
  {
    pattern: /permission denied|forbidden/i,
    titleKey: "accessDenied",
    retriable: false,
  },
];

const midStreamPatterns: PatternEntry[] = [
  {
    pattern: /context length exceeded|token limit/i,
    titleKey: "conversationTooLong",
    retriable: false,
  },
  {
    pattern: /rate limit/i,
    titleKey: "sessionBusy",
    retriable: true,
  },
];

function matchPattern(
  rawMessage: string | undefined,
  patterns: PatternEntry[],
  fallback: Omit<PatternEntry, "pattern">,
): Omit<PatternEntry, "pattern"> {
  if (rawMessage) {
    for (const { pattern, titleKey, retriable } of patterns) {
      if (pattern.test(rawMessage)) {
        return { titleKey, retriable };
      }
    }
  }
  return fallback;
}

export function toFriendlyError(ctx: ErrorContext, copy: Copy): FriendlyError {
  const detail = ctx.rawMessage ?? undefined;
  const titles = copy.errorMessages;

  switch (ctx.source) {
    case "pre-stream-http": {
      const mapped = ctx.status !== undefined ? preStreamHttpMap[ctx.status] : undefined;
      if (mapped) {
        return { title: titles[mapped.titleKey], retriable: mapped.retriable, detail };
      }
      return { title: titles.preStreamFallback, retriable: true, detail };
    }

    case "network":
      return {
        title: titles.networkError,
        retriable: true,
        detail,
      };

    case "tool-output-error": {
      const { titleKey, retriable } = matchPattern(ctx.rawMessage, toolOutputPatterns, {
        titleKey: "toolFailedFallback",
        retriable: true,
      });
      return { title: titles[titleKey], retriable, detail };
    }

    case "mid-stream-sse": {
      const { titleKey, retriable } = matchPattern(ctx.rawMessage, midStreamPatterns, {
        titleKey: "midStreamFallback",
        retriable: true,
      });
      return { title: titles[titleKey], retriable, detail };
    }
  }
}
