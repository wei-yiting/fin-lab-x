import { describe, test, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyState } from "../EmptyState";
import { copy } from "@/lib/copy";

describe("EmptyState", () => {
  test("renders 4 prompt chips, each showing its title", () => {
    const onPickPrompt = vi.fn();
    render(<EmptyState onPickPrompt={onPickPrompt} />);

    const chips = screen.getAllByTestId("prompt-chip");
    expect(chips).toHaveLength(4);
    for (const chip of Object.values(copy.emptyState.chips)) {
      expect(screen.getByText(chip.title)).toBeInTheDocument();
    }
  });

  test("chip click invokes onPickPrompt with the full prompt, not the title (populates Composer, not auto-send)", async () => {
    const user = userEvent.setup();
    const onPickPrompt = vi.fn();
    render(<EmptyState onPickPrompt={onPickPrompt} />);

    await user.click(screen.getAllByTestId("prompt-chip")[1]);

    expect(onPickPrompt).toHaveBeenCalledTimes(1);
    expect(onPickPrompt).toHaveBeenCalledWith(copy.emptyState.chips.narrativeVsNumbers.prompt);
  });
});
