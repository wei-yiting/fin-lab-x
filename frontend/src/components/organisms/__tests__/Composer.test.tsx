import { describe, test, expect, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { Composer, type ComposerHandle } from "../Composer";

describe("Composer — double-submit guard", () => {
  test("TC-comp-composer-01: rapid Enter twice triggers sendMessage exactly once", async () => {
    const user = userEvent.setup();
    const sendMessage = vi.fn();
    render(<Composer sendMessage={sendMessage} stop={vi.fn()} status="ready" />);

    const textarea = screen.getByTestId("composer-textarea");
    await user.type(textarea, "hello");
    await user.keyboard("{Enter}{Enter}");

    expect(sendMessage).toHaveBeenCalledTimes(1);
    expect(sendMessage).toHaveBeenCalledWith({ text: "hello" });
  });

  test("TC-comp-composer-01: Send button click during submitted state is ignored", async () => {
    render(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="submitted" />);

    expect(screen.queryByTestId("composer-send-btn")).not.toBeInTheDocument();
    expect(screen.getByTestId("composer-stop-btn")).toBeInTheDocument();
  });
});

describe("Composer — textarea preservation", () => {
  test("TC-comp-composer-02: textarea value is not cleared when status transitions streaming → ready", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <Composer sendMessage={vi.fn()} stop={vi.fn()} status="streaming" />,
    );

    const textarea = screen.getByTestId("composer-textarea") as HTMLTextAreaElement;
    await user.type(textarea, "next question");

    expect(textarea.value).toBe("next question");

    rerender(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="ready" />);

    expect(textarea.value).toBe("next question");
  });

  test("TC-comp-composer-02: textarea value is not cleared when status transitions submitted → ready (regenerate)", async () => {
    const user = userEvent.setup();
    const { rerender } = render(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="ready" />);

    const textarea = screen.getByTestId("composer-textarea") as HTMLTextAreaElement;
    await user.type(textarea, "in-progress text");

    rerender(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="submitted" />);
    rerender(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="streaming" />);
    rerender(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="ready" />);

    expect(textarea.value).toBe("in-progress text");
  });
});

describe("Composer — send button disabled state", () => {
  test("TC-comp-composer-04: send button is disabled when textarea is empty", () => {
    render(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="ready" />);

    expect(screen.getByTestId("composer-send-btn")).toBeDisabled();
  });

  test("TC-comp-composer-04: send button stays disabled for whitespace-only input", async () => {
    const user = userEvent.setup();
    render(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="ready" />);

    await user.type(screen.getByTestId("composer-textarea"), "   ");

    expect(screen.getByTestId("composer-send-btn")).toBeDisabled();
  });

  test("TC-comp-composer-04: send button becomes enabled once real content is typed", async () => {
    const user = userEvent.setup();
    render(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="ready" />);

    await user.type(screen.getByTestId("composer-textarea"), "hello");

    expect(screen.getByTestId("composer-send-btn")).toBeEnabled();
  });

  test("TC-comp-composer-04: submitting whitespace-only via Enter does not call sendMessage", async () => {
    const user = userEvent.setup();
    const sendMessage = vi.fn();
    render(<Composer sendMessage={sendMessage} stop={vi.fn()} status="ready" />);

    await user.type(screen.getByTestId("composer-textarea"), "   ");
    await user.keyboard("{Enter}");

    expect(sendMessage).not.toHaveBeenCalled();
  });
});

describe("Composer — IME composition guard", () => {
  // fireEvent is used here because userEvent cannot express nativeEvent.isComposing,
  // which is the exact browser-level signal Composer guards against (CJK IME commit).
  test("TC-comp-composer-05: Enter during IME composition does not trigger sendMessage", async () => {
    const user = userEvent.setup();
    const sendMessage = vi.fn();
    render(<Composer sendMessage={sendMessage} stop={vi.fn()} status="ready" />);

    const textarea = screen.getByTestId("composer-textarea");
    await user.type(textarea, "你好");

    fireEvent.keyDown(textarea, { key: "Enter", isComposing: true });

    expect(sendMessage).not.toHaveBeenCalled();
  });

  test("TC-comp-composer-05: Enter after IME commit (isComposing=false) triggers sendMessage", () => {
    const sendMessage = vi.fn();
    render(<Composer sendMessage={sendMessage} stop={vi.fn()} status="ready" />);

    const textarea = screen.getByTestId("composer-textarea");
    fireEvent.change(textarea, { target: { value: "你好" } });
    fireEvent.keyDown(textarea, { key: "Enter", isComposing: false });

    expect(sendMessage).toHaveBeenCalledTimes(1);
    expect(sendMessage).toHaveBeenCalledWith({ text: "你好" });
  });
});

describe("Composer — chip click", () => {
  test("TC-comp-composer-03: chip click overwrites existing textarea content (last-wins)", async () => {
    const user = userEvent.setup();
    const composerRef = createRef<ComposerHandle>();
    render(<Composer ref={composerRef} sendMessage={vi.fn()} stop={vi.fn()} status="ready" />);

    const textarea = screen.getByTestId("composer-textarea") as HTMLTextAreaElement;
    await user.type(textarea, "已輸入一半");

    // setValue is a React state setter under the hood — wrap the imperative
    // call in act() so the resulting re-render commits before we read the DOM.
    act(() => {
      composerRef.current?.setValue("Latest market news");
    });

    expect(textarea.value).toBe("Latest market news");
    expect(textarea.value).not.toContain("已輸入一半");
  });
});
