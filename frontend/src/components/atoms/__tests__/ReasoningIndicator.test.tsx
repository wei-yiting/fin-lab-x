import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReasoningIndicator } from "../ReasoningIndicator";

describe("ReasoningIndicator — idle mode (no text)", () => {
  test("renders 3 idle dots when no text prop is passed", () => {
    const { container } = render(<ReasoningIndicator />);

    const dots = container.querySelectorAll(".idle-dots > span");
    expect(dots.length).toBe(3);
  });

  test("does not render any text content in idle mode", () => {
    const { container } = render(<ReasoningIndicator />);

    expect(container.querySelector(".reasoning-status-text")).not.toBeInTheDocument();
    expect(container.querySelector(".reasoning-status-dots-cycler")).not.toBeInTheDocument();
    expect(screen.queryByText("STOPPED")).not.toBeInTheDocument();
  });

  test("renders idle 3-dot when text is null", () => {
    const { container } = render(<ReasoningIndicator text={null} />);

    expect(container.querySelectorAll(".idle-dots > span").length).toBe(3);
  });

  test("empty string text renders idle (3 dots, no text element)", () => {
    const { container } = render(<ReasoningIndicator text="" />);
    expect(container.querySelectorAll(".idle-dots > span").length).toBe(3);
    expect(container.querySelector(".reasoning-status-text")).not.toBeInTheDocument();
  });
});

describe("ReasoningIndicator — streaming mode (text + cycler)", () => {
  test("renders text content with dots cycler when text is provided", () => {
    const { container } = render(<ReasoningIndicator text="理解問題" />);

    expect(screen.getByText("理解問題")).toBeInTheDocument();
    expect(container.querySelector(".reasoning-status-dots-cycler")).toBeInTheDocument();
  });

  test("does not render STOPPED label in streaming mode", () => {
    render(<ReasoningIndicator text="理解問題" />);

    expect(screen.queryByText("STOPPED")).not.toBeInTheDocument();
  });

  test("does not render idle 3-dot bouncing when streaming", () => {
    const { container } = render(<ReasoningIndicator text="理解問題" />);

    expect(container.querySelector(".idle-dots")).not.toBeInTheDocument();
  });

  test("text-bearing element carries the .reasoning-status-text class for nowrap clip", () => {
    const { container } = render(<ReasoningIndicator text="hello" />);

    const textEl = container.querySelector(".reasoning-status-text");
    expect(textEl).toBeInTheDocument();
    expect(textEl?.textContent).toBe("hello");
  });
});

describe("ReasoningIndicator — frozen mode (text + STOPPED label)", () => {
  test("renders text and STOPPED label, no dots cycler", () => {
    const { container } = render(<ReasoningIndicator text="理解問題" state="frozen" />);

    expect(screen.getByText("理解問題")).toBeInTheDocument();
    expect(screen.getByText("STOPPED")).toBeInTheDocument();
    expect(container.querySelector(".reasoning-status-dots-cycler")).not.toBeInTheDocument();
  });

  test("frozen text element has opacity 0.65", () => {
    const { container } = render(<ReasoningIndicator text="理解問題" state="frozen" />);

    const textEl = container.querySelector(".reasoning-status-text") as HTMLElement;
    expect(textEl).toBeInTheDocument();
    expect(textEl.style.opacity).toBe("0.65");
  });
});

describe("ReasoningIndicator — stalled modifier", () => {
  test("applies .stalled class on the wrapper when stalled=true", () => {
    const { container } = render(<ReasoningIndicator text="理解問題" stalled={true} />);

    expect(container.querySelector(".reasoning-status.stalled")).toBeInTheDocument();
  });

  test("no .stalled class on wrapper when stalled is false/omitted", () => {
    const { container } = render(<ReasoningIndicator text="理解問題" />);

    expect(container.querySelector(".reasoning-status.stalled")).not.toBeInTheDocument();
  });
});

describe("ReasoningIndicator — plain text rendering (D20)", () => {
  test("renders backticks and asterisks as literal characters, not as code/strong elements", () => {
    const raw = "run `list_sec_sections` and **bold**";
    const { container } = render(<ReasoningIndicator text={raw} />);

    expect(screen.getByText(raw)).toBeInTheDocument();
    expect(container.querySelector("code")).not.toBeInTheDocument();
    expect(container.querySelector("strong")).not.toBeInTheDocument();
  });
});

describe("ReasoningIndicator — accessibility (D22)", () => {
  test("wrapper is hidden from screen readers via aria-hidden", () => {
    const { container } = render(<ReasoningIndicator text="理解問題" />);

    const wrapper = container.querySelector(".reasoning-status");
    expect(wrapper?.getAttribute("aria-hidden")).toBe("true");
  });

  test("idle wrapper is also aria-hidden", () => {
    const { container } = render(<ReasoningIndicator />);

    const wrapper = container.querySelector(".reasoning-status");
    expect(wrapper?.getAttribute("aria-hidden")).toBe("true");
  });
});

describe("ReasoningIndicator — trailing delimiter trim", () => {
  // Provider emissions often end in a sentence delimiter; rendering the
  // dots cycler right after a delim produces "...... ..." visual mush.
  // The atom strips trailing punctuation/whitespace before render so the
  // cycler dots flow naturally after the last meaningful character.
  test.each([
    ["Analyzing your request.", "Analyzing your request"],
    ["Analyzing your request. ", "Analyzing your request"],
    ["Working on it...", "Working on it"],
    ["理解問題。", "理解問題"],
    ["處理中,", "處理中"],
    ["處理中、", "處理中"],
    ["processing!", "processing"],
    ["thinking?", "thinking"],
    ["plain", "plain"],
  ])("'%s' renders as '%s'", (input, expected) => {
    render(<ReasoningIndicator text={input} />);
    expect(screen.getByText(expected)).toBeInTheDocument();
  });

  test("frozen mode also trims trailing delimiter", () => {
    render(<ReasoningIndicator text="Analyzing your request." state="frozen" />);
    expect(screen.getByText("Analyzing your request")).toBeInTheDocument();
    expect(screen.getByText("STOPPED")).toBeInTheDocument();
  });

  test("text composed entirely of delimiters renders idle 3-dot (no empty text element)", () => {
    const { container } = render(<ReasoningIndicator text="..." />);
    expect(container.querySelectorAll(".idle-dots > span").length).toBe(3);
    expect(container.querySelector(".reasoning-status-text")).not.toBeInTheDocument();
  });
});

describe("ReasoningIndicator — backward compatibility", () => {
  test("preserves data-testid='reasoning-indicator' on root for legacy consumers", () => {
    const { container } = render(<ReasoningIndicator />);

    const root = container.querySelector("[data-testid='reasoning-indicator']");
    expect(root).toBeInTheDocument();
  });
});
