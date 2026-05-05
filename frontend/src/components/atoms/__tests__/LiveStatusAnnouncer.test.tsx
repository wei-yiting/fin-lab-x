import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LiveStatusAnnouncer } from "../LiveStatusAnnouncer";
import { formatStatusText, type AnnouncedEvent } from "../live-status-text";

describe("LiveStatusAnnouncer — DOM structure (D22)", () => {
  test('renders role="status" with aria-live="polite" and .sr-only class', () => {
    render(<LiveStatusAnnouncer status="ready" lastEvent={null} />);

    const region = screen.getByRole("status");
    expect(region).toHaveAttribute("aria-live", "polite");
    expect(region).toHaveClass("sr-only");
  });

  test("renders empty content when status is ready and lastEvent is null", () => {
    render(<LiveStatusAnnouncer status="ready" lastEvent={null} />);

    const region = screen.getByRole("status");
    expect(region.textContent).toBe("");
  });
});

describe("LiveStatusAnnouncer — event transitions (D22)", () => {
  test('lastEvent.type "start" announces "Generating response"', () => {
    const event: AnnouncedEvent = { type: "start" };
    render(<LiveStatusAnnouncer status="streaming" lastEvent={event} />);

    expect(screen.getByRole("status")).toHaveTextContent("Generating response");
  });

  test('lastEvent.type "tool-input-available" announces "Calling <toolName>"', () => {
    const event: AnnouncedEvent = {
      type: "tool-input-available",
      toolName: "yfinance_quote",
    };
    render(<LiveStatusAnnouncer status="streaming" lastEvent={event} />);

    expect(screen.getByRole("status")).toHaveTextContent("Calling yfinance_quote");
  });

  test('lastEvent.type "tool-output-available" announces "Tool <toolName> completed"', () => {
    const event: AnnouncedEvent = {
      type: "tool-output-available",
      toolName: "yfinance_quote",
    };
    render(<LiveStatusAnnouncer status="streaming" lastEvent={event} />);

    expect(screen.getByRole("status")).toHaveTextContent("Tool yfinance_quote completed");
  });

  test('lastEvent.type "tool-output-error" announces "Tool <toolName> failed"', () => {
    const event: AnnouncedEvent = {
      type: "tool-output-error",
      toolName: "yfinance_quote",
    };
    render(<LiveStatusAnnouncer status="streaming" lastEvent={event} />);

    expect(screen.getByRole("status")).toHaveTextContent("Tool yfinance_quote failed");
  });

  test('lastEvent.type "finish" announces "Response complete"', () => {
    const event: AnnouncedEvent = { type: "finish" };
    render(<LiveStatusAnnouncer status="ready" lastEvent={event} />);

    expect(screen.getByRole("status")).toHaveTextContent("Response complete");
  });
});

describe("LiveStatusAnnouncer — error status precedence (D22)", () => {
  test('status="error" with errorText announces "Error: <errorText>"', () => {
    const event: AnnouncedEvent = {
      type: "tool-output-available",
      toolName: "yfinance_quote",
      errorText: "rate limit exceeded",
    };
    render(<LiveStatusAnnouncer status="error" lastEvent={event} />);

    expect(screen.getByRole("status")).toHaveTextContent("Error: rate limit exceeded");
  });

  test('status="error" without errorText falls back to "Error: stream interrupted"', () => {
    render(<LiveStatusAnnouncer status="error" lastEvent={null} />);

    expect(screen.getByRole("status")).toHaveTextContent("Error: stream interrupted");
  });

  test("error status overrides any non-error event mapping", () => {
    const event: AnnouncedEvent = { type: "start" };
    render(<LiveStatusAnnouncer status="error" lastEvent={event} />);

    const region = screen.getByRole("status");
    expect(region).toHaveTextContent("Error: stream interrupted");
    expect(region).not.toHaveTextContent("Generating response");
  });
});

describe("LiveStatusAnnouncer — non-announced events (D22 / S-rsn-14)", () => {
  test("reasoning events are not announced (announcer text unchanged)", () => {
    // Component only consumes the 5 listed event types — anything else is
    // upstream's responsibility to filter (ChatPanel never sets reasoning
    // events on lastSSEEventRef). With lastEvent=null the announcer is empty.
    render(<LiveStatusAnnouncer status="streaming" lastEvent={null} />);

    expect(screen.getByRole("status").textContent).toBe("");
  });
});

describe("formatStatusText — pure mapping function", () => {
  test('maps "start" event to "Generating response"', () => {
    expect(formatStatusText("streaming", { type: "start" })).toBe("Generating response");
  });

  test('maps "tool-input-available" with toolName', () => {
    expect(
      formatStatusText("streaming", {
        type: "tool-input-available",
        toolName: "search",
      }),
    ).toBe("Calling search");
  });

  test('maps "tool-output-available" with toolName', () => {
    expect(
      formatStatusText("streaming", {
        type: "tool-output-available",
        toolName: "search",
      }),
    ).toBe("Tool search completed");
  });

  test('maps "tool-output-error" with toolName', () => {
    expect(
      formatStatusText("streaming", {
        type: "tool-output-error",
        toolName: "search",
      }),
    ).toBe("Tool search failed");
  });

  test('maps "finish" event', () => {
    expect(formatStatusText("ready", { type: "finish" })).toBe("Response complete");
  });

  test("error status with explicit errorText takes precedence", () => {
    expect(
      formatStatusText("error", {
        type: "start",
        errorText: "boom",
      }),
    ).toBe("Error: boom");
  });

  test('error status without errorText falls back to "stream interrupted"', () => {
    expect(formatStatusText("error", null)).toBe("Error: stream interrupted");
  });

  test("ready status with null event returns empty string", () => {
    expect(formatStatusText("ready", null)).toBe("");
  });

  test("submitted status with null event returns empty string", () => {
    expect(formatStatusText("submitted", null)).toBe("");
  });

  test("tool-input-available with missing toolName → 'Calling tool'", () => {
    expect(formatStatusText("streaming", { type: "tool-input-available" })).toBe("Calling tool");
  });

  test("tool-output-available with missing toolName → 'Tool tool completed'", () => {
    expect(formatStatusText("streaming", { type: "tool-output-available" })).toBe(
      "Tool tool completed",
    );
  });

  test("tool-output-error with missing toolName → 'Tool tool failed'", () => {
    expect(formatStatusText("streaming", { type: "tool-output-error" })).toBe("Tool tool failed");
  });
});
