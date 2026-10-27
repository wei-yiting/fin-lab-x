import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyState } from "../EmptyState";
import { en } from "@/lib/copy";
import { LocaleProvider } from "@/lib/LocaleProvider";
import { LOCALE_STORAGE_KEY } from "@/lib/locale";

afterEach(() => {
  localStorage.clear();
});

describe("EmptyState", () => {
  test("renders 4 prompt chips, each showing its title", () => {
    const onPickPrompt = vi.fn();
    render(<EmptyState onPickPrompt={onPickPrompt} />);

    const chips = screen.getAllByTestId("prompt-chip");
    expect(chips).toHaveLength(4);
    for (const chip of Object.values(en.emptyState.chips)) {
      expect(screen.getByText(chip.title)).toBeInTheDocument();
    }
  });

  test("chip click invokes onPickPrompt with the full prompt, not the title (populates Composer, not auto-send)", async () => {
    const user = userEvent.setup();
    const onPickPrompt = vi.fn();
    render(<EmptyState onPickPrompt={onPickPrompt} />);

    await user.click(screen.getAllByTestId("prompt-chip")[1]);

    expect(onPickPrompt).toHaveBeenCalledTimes(1);
    expect(onPickPrompt).toHaveBeenCalledWith(en.emptyState.chips.narrativeVsNumbers.prompt);
  });

  test("in zh-TW, heading and chips render in Traditional Chinese and a chip picks the Chinese prompt", async () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "zh-TW");
    const user = userEvent.setup();
    const onPickPrompt = vi.fn();
    render(
      <LocaleProvider>
        <EmptyState onPickPrompt={onPickPrompt} />
      </LocaleProvider>,
    );

    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("研究任何一檔美股");
    expect(screen.getAllByTestId("prompt-chip")).toHaveLength(4);
    expect(screen.getByText("風險揭露 vs. 近期新聞")).toBeInTheDocument();

    await user.click(screen.getAllByTestId("prompt-chip")[2]);

    expect(onPickPrompt).toHaveBeenCalledWith(
      expect.stringContaining("比較 Apple 與 Alphabet 在最新 10-K 中揭露的反托拉斯風險"),
    );
  });
});
