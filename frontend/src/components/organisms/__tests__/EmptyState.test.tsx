import { describe, test, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyState } from "../EmptyState";

describe("EmptyState", () => {
  test("TC-comp-empty-01: renders 4 prompt chips with correct labels", () => {
    const onPickPrompt = vi.fn();
    render(<EmptyState onPickPrompt={onPickPrompt} />);

    const chips = screen.getAllByTestId("prompt-chip");
    expect(chips).toHaveLength(4);
  });

  test("TC-comp-empty-01: chip click invokes onPickPrompt with chip text (populates Composer, not auto-send)", async () => {
    const user = userEvent.setup();
    const onPickPrompt = vi.fn();
    render(<EmptyState onPickPrompt={onPickPrompt} />);

    await user.click(screen.getAllByTestId("prompt-chip")[1]);

    expect(onPickPrompt).toHaveBeenCalledTimes(1);
    expect(onPickPrompt).toHaveBeenCalledWith(expect.any(String));
  });
});
