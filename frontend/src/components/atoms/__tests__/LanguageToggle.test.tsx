import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatHeader } from "@/components/organisms/ChatHeader";
import { EmptyState } from "@/components/organisms/EmptyState";
import { LocaleProvider } from "@/lib/LocaleProvider";
import { LOCALE_STORAGE_KEY } from "@/lib/locale";

function renderShell() {
  return render(
    <LocaleProvider>
      <ChatHeader onClear={vi.fn()} messagesEmpty={true} />
      <EmptyState onPickPrompt={vi.fn()} />
    </LocaleProvider>,
  );
}

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
  document.documentElement.lang = "en";
});

describe("LanguageToggle", () => {
  test("defaults to English with EN pressed", () => {
    renderShell();

    expect(screen.getByRole("group", { name: "Interface language" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "English" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "繁體中文" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent(
      "Research any US-listed stock",
    );
    expect(document.documentElement.lang).toBe("en");
  });

  test("switching to 中文 re-renders the UI, sets <html lang>, and persists the choice", async () => {
    const user = userEvent.setup();
    renderShell();

    await user.click(screen.getByRole("button", { name: "繁體中文" }));

    expect(screen.getByRole("button", { name: "繁體中文" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("group", { name: "介面語言" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("研究任何一檔美股");
    expect(screen.getByText("美股研究 AI Agent")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "清除對話" })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("zh-TW");
    expect(document.title).toBe("FinLab-X — 美股研究 AI Agent");
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("zh-TW");
  });

  test("a stored choice survives a remount, and switching back to EN restores English", async () => {
    const user = userEvent.setup();
    localStorage.setItem(LOCALE_STORAGE_KEY, "zh-TW");
    renderShell();

    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("研究任何一檔美股");

    await user.click(screen.getByRole("button", { name: "English" }));

    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent(
      "Research any US-listed stock",
    );
    expect(document.documentElement.lang).toBe("en");
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("en");
  });

  test("an unknown stored value falls back to English", () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "fr");
    renderShell();
    expect(screen.getByRole("button", { name: "English" })).toHaveAttribute("aria-pressed", "true");
  });

  test("blocked storage neither breaks rendering nor switching", async () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("blocked", "SecurityError");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("blocked", "SecurityError");
    });
    const user = userEvent.setup();
    renderShell();

    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent(
      "Research any US-listed stock",
    );
    await user.click(screen.getByRole("button", { name: "繁體中文" }));
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("研究任何一檔美股");
  });
});
