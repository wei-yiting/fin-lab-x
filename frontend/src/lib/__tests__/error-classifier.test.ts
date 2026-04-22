import { describe, test, expect } from "vitest";
import { classifyError } from "../error-classifier";
import { ChatHttpError } from "../chat-http";

describe("classifyError", () => {
  test('TypeError with "fetch" in message → network', () => {
    expect(classifyError(new TypeError("Failed to fetch"))).toBe("network");
  });

  test.each([
    [422, "pre-stream-422"],
    [404, "pre-stream-404"],
    [409, "pre-stream-409"],
    [500, "pre-stream-500"],
    [503, "pre-stream-5xx"],
    [504, "pre-stream-5xx"],
  ])("error with status %d → %s", (status, expected) => {
    const err = { status, message: "mock" };
    expect(classifyError(err)).toBe(expected);
  });

  test.each([
    [422, "pre-stream-422"],
    [404, "pre-stream-404"],
    [409, "pre-stream-409"],
    [500, "pre-stream-500"],
    [503, "pre-stream-5xx"],
  ])("ChatHttpError with status %d → %s", (status, expected) => {
    expect(classifyError(new ChatHttpError(status, "mock body"))).toBe(expected);
  });

  test("unknown error → unknown", () => {
    expect(classifyError({ foo: "bar" })).toBe("unknown");
    expect(classifyError(null)).toBe("unknown");
    expect(classifyError(undefined)).toBe("unknown");
  });
});
