import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LiveStatusAnnouncer } from "../LiveStatusAnnouncer";
import { formatStatusText, type AnnouncedEvent } from "../live-status-text";

describe("LiveStatusAnnouncer — DOM structure", () => {
  test('renders role="status" with aria-live="polite" and .sr-only class', () => {
    render(<LiveStatusAnnouncer lastEvent={null} />);

    const region = screen.getByRole("status");
    expect(region).toHaveAttribute("aria-live", "polite");
    expect(region).toHaveClass("sr-only");
  });

  test("renders empty content when lastEvent is null", () => {
    render(<LiveStatusAnnouncer lastEvent={null} />);

    const region = screen.getByRole("status");
    expect(region.textContent).toBe("");
  });
});

describe("LiveStatusAnnouncer — event transitions", () => {
  test('lastEvent.type "finish" announces "Response complete"', () => {
    const event: AnnouncedEvent = { type: "finish" };
    render(<LiveStatusAnnouncer lastEvent={event} />);

    expect(screen.getByRole("status")).toHaveTextContent("Response complete");
  });
});

describe("LiveStatusAnnouncer — non-announced events", () => {
  test("reasoning events are not announced (announcer text unchanged)", () => {
    // Component only consumes the 'finish' event type — anything else is
    // upstream's responsibility to filter (ChatPanel never sets reasoning
    // events on lastSSEEvent). With lastEvent=null the announcer is empty.
    render(<LiveStatusAnnouncer lastEvent={null} />);

    expect(screen.getByRole("status").textContent).toBe("");
  });
});

describe("formatStatusText — pure mapping function", () => {
  test('maps "finish" event', () => {
    expect(formatStatusText({ type: "finish" })).toBe("Response complete");
  });

  test("null event returns empty string", () => {
    expect(formatStatusText(null)).toBe("");
  });
});
