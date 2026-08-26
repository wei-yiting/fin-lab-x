import { describe, test, expect } from "vitest";
import { toFriendlyError } from "../error-messages";

describe("toFriendlyError — pre-stream HTTP errors", () => {
  test.each([
    [422, "無法重新產生這則回覆，請再試一次。", true],
    [404, "找不到這個對話，請重新整理頁面以開始新對話。", false],
    [409, "系統忙碌中，請稍後再試一次。", true],
    [500, "伺服器發生錯誤，請再試一次。", true],
    [503, "發生錯誤，請再試一次。", true],
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
  expect(result.title).toBe("連線中斷，請檢查網路連線後再試一次。");
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
    [BUDGET_REACHED_BACKEND_MESSAGE, "這次請求的工具呼叫次數已達上限。", false],
    ["API rate limit exceeded", "請求過於頻繁，請稍候片刻後再試。", true],
    ["ticker not found", "找不到相關資料。", false],
    ["Connection timeout after 30s", "工具執行逾時，請再試一次。", true],
    ["Permission denied (403)", "沒有權限存取這項資源。", false],
    ["Some unknown error", "工具執行失敗，請再試一次。", true],
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
    ["context length exceeded", "這段對話已經太長，請開啟新對話繼續。", false],
    ["token limit reached", "這段對話已經太長，請開啟新對話繼續。", false],
    ["rate limit", "系統忙碌中，請稍後再試一次。", true],
    ["Unknown stream error", "產生回覆時發生錯誤，請再試一次。", true],
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
