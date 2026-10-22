import { afterEach, describe, expect, test, vi } from "vitest";
import type { BeforeSendEvent } from "@vercel/analytics/react";
import { ANALYTICS_OPT_OUT_KEY, dropOptedOutEvents } from "../analytics";

const event: BeforeSendEvent = { type: "pageview", url: "https://example.com/" };

describe("dropOptedOutEvents", () => {
  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  test("passes the event through when the opt-out flag is absent", () => {
    expect(dropOptedOutEvents(event)).toBe(event);
  });

  test("drops the event when the opt-out flag is set", () => {
    localStorage.setItem(ANALYTICS_OPT_OUT_KEY, "1");
    expect(dropOptedOutEvents(event)).toBeNull();
  });

  test("passes the event through when localStorage throws", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("blocked", "SecurityError");
    });
    expect(dropOptedOutEvents(event)).toBe(event);
  });
});
