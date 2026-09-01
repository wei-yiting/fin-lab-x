import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ActivityPlaceholder } from "../ActivityPlaceholder";

// Rendering only. WHEN the placeholder is visible is derived by
// useDeadAirPlaceholder and covered by its own hook tests; this file owns the
// copy for both stall states and the aria-live contract.
describe("ActivityPlaceholder — copy and a11y contract", () => {
  test("stalled=false renders the non-degraded copy", () => {
    render(<ActivityPlaceholder stalled={false} />);

    const el = screen.getByTestId("activity-placeholder");
    expect(el).toHaveTextContent("思考中");
    expect(el).not.toHaveTextContent("仍在處理中");
  });

  test("stalled=true renders the degraded copy", () => {
    render(<ActivityPlaceholder stalled={true} />);

    const el = screen.getByTestId("activity-placeholder");
    expect(el).toHaveTextContent("仍在處理中");
    expect(el).not.toHaveTextContent("思考中");
  });

  test("the placeholder announces politely", () => {
    render(<ActivityPlaceholder stalled={false} />);

    expect(screen.getByTestId("activity-placeholder")).toHaveAttribute("aria-live", "polite");
  });

  test("the dots cycler is aria-hidden so it never spams the polite queue", () => {
    const { container } = render(<ActivityPlaceholder stalled={false} />);

    const dots = container.querySelector(".thinking-dots");
    expect(dots).not.toBeNull();
    expect(dots).toHaveAttribute("aria-hidden", "true");
  });
});
