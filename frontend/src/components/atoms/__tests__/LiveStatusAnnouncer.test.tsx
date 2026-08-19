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
  test('lastEvent.type "finish" announces "Response complete"', () => {
    const event: AnnouncedEvent = { type: "finish" };
    render(<LiveStatusAnnouncer status="ready" lastEvent={event} />);

    expect(screen.getByRole("status")).toHaveTextContent("Response complete");
  });
});

describe("LiveStatusAnnouncer — error status precedence (D22)", () => {
  test('status="error" without errorText falls back to "Error: stream interrupted"', () => {
    render(<LiveStatusAnnouncer status="error" lastEvent={null} />);

    expect(screen.getByRole("status")).toHaveTextContent("Error: stream interrupted");
  });

  test("error status overrides any non-error event mapping", () => {
    const event: AnnouncedEvent = { type: "finish" };
    render(<LiveStatusAnnouncer status="error" lastEvent={event} />);

    const region = screen.getByRole("status");
    expect(region).toHaveTextContent("Error: stream interrupted");
    expect(region).not.toHaveTextContent("Response complete");
  });
});

describe("LiveStatusAnnouncer — non-announced events (D22 / S-rsn-14)", () => {
  test("reasoning events are not announced (announcer text unchanged)", () => {
    // Component only consumes the 'finish' event type — anything else is
    // upstream's responsibility to filter (ChatPanel never sets reasoning
    // events on lastSSEEvent). With lastEvent=null the announcer is empty.
    render(<LiveStatusAnnouncer status="streaming" lastEvent={null} />);

    expect(screen.getByRole("status").textContent).toBe("");
  });
});

describe("formatStatusText — pure mapping function", () => {
  test('maps "finish" event', () => {
    expect(formatStatusText("ready", { type: "finish" })).toBe("Response complete");
  });

  test('error status without errorText falls back to "stream interrupted"', () => {
    expect(formatStatusText("error", null)).toBe("Error: stream interrupted");
  });

  test("error status with explicit errorText takes precedence", () => {
    expect(
      formatStatusText("error", {
        type: "finish",
        errorText: "boom",
      }),
    ).toBe("Error: boom");
  });

  test("ready status with null event returns empty string", () => {
    expect(formatStatusText("ready", null)).toBe("");
  });

  test("submitted status with null event returns empty string", () => {
    expect(formatStatusText("submitted", null)).toBe("");
  });
});
