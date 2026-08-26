import { describe, test, expect } from "vitest";
import { toFriendlyError } from "../error-messages";
import { copy } from "@/lib/copy";

describe("toFriendlyError — pre-stream HTTP errors", () => {
  test.each([
    [422, copy.errorMessages.regenerateFailed, true],
    [404, copy.errorMessages.conversationNotFound, false],
    [409, copy.errorMessages.sessionBusy, true],
    [500, copy.errorMessages.serverError, true],
    [503, copy.errorMessages.preStreamFallback, true],
  ])('status %d → "%s" (retriable: %s)', (status, expectedTitle, expectedRetriable) => {
    const result = toFriendlyError({ source: "pre-stream-http", status });
    expect(result.title).toBe(expectedTitle);
    expect(result.retriable).toBe(expectedRetriable);
  });
});

test("network failure → connection-lost message", () => {
  const result = toFriendlyError({
    source: "network",
    rawMessage: "Failed to fetch",
  });
  expect(result.title).toBe(copy.errorMessages.networkError);
  expect(result.retriable).toBe(true);
  expect(result.detail).toBe("Failed to fetch");
});

describe("toFriendlyError — tool-output-error pattern matching", () => {
  // The actual sentinel produced by backend RunBudgetMiddleware._budget_message().
  // Includes the "NOT an external rate limit" disambiguation phrase the LLM
  // sees, which historically was misclassified as a rate-limit error by the
  // /rate limit/i pattern when it appeared anywhere in the body.
  const BUDGET_REACHED_BACKEND_MESSAGE =
    "Per-run tool-call budget reached for this request. " +
    "Do not call 'sec_filing_list_sections' again in this run. " +
    "This is an INTERNAL orchestration budget — it is NOT an external " +
    "rate limit from SEC EDGAR, Yahoo Finance, Tavily, or any other " +
    "external API. Summarize with the data already collected; do not " +
    "describe this to the user as a network or API failure.";

  test.each([
    [BUDGET_REACHED_BACKEND_MESSAGE, copy.errorMessages.toolBudgetReached, false],
    ["API rate limit exceeded", copy.errorMessages.tooManyRequests, true],
    ["ticker not found", copy.errorMessages.dataNotFound, false],
    ["Connection timeout after 30s", copy.errorMessages.toolTimeout, true],
    ["Permission denied (403)", copy.errorMessages.accessDenied, false],
    ["Some unknown error", copy.errorMessages.toolFailedFallback, true],
  ])('rawMessage "%s" → "%s"', (rawMessage, expectedTitle, expectedRetriable) => {
    const result = toFriendlyError({
      source: "tool-output-error",
      rawMessage,
    });
    expect(result.title).toBe(expectedTitle);
    expect(result.retriable).toBe(expectedRetriable);
    expect(result.detail).toBe(rawMessage);
  });
});

describe("toFriendlyError — mid-stream-sse pattern matching", () => {
  test.each([
    ["context length exceeded", copy.errorMessages.conversationTooLong, false],
    ["token limit reached", copy.errorMessages.conversationTooLong, false],
    ["rate limit", copy.errorMessages.sessionBusy, true],
    ["Unknown stream error", copy.errorMessages.midStreamFallback, true],
  ])('mid-stream rawMessage "%s" → "%s"', (rawMessage, expectedTitle, expectedRetriable) => {
    const result = toFriendlyError({
      source: "mid-stream-sse",
      rawMessage,
    });
    expect(result.title).toBe(expectedTitle);
    expect(result.retriable).toBe(expectedRetriable);
  });
});

describe("toFriendlyError — invariants", () => {
  test("detail is set only when rawMessage is provided", () => {
    expect(toFriendlyError({ source: "pre-stream-http", status: 422 }).detail).toBeUndefined();
    expect(
      toFriendlyError({ source: "pre-stream-http", status: 422, rawMessage: "x" }).detail,
    ).toBe("x");
  });
});
