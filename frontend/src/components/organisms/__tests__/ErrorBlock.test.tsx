import { describe, test, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorBlock } from "../ErrorBlock";
import { copy } from "@/lib/copy";

describe("ErrorBlock", () => {
  test("displays friendly title only, raw detail hidden by default", () => {
    render(
      <ErrorBlock
        friendly={{
          title: "系統忙碌中，請稍後再試一次。",
          detail: "HTTP 409: session busy on backend",
          retriable: true,
        }}
        onRetry={vi.fn()}
        source="pre-stream"
        errorClass="pre-stream-409"
      />,
    );

    expect(screen.getByTestId("error-title")).toHaveTextContent("系統忙碌中，請稍後再試一次。");
    expect(screen.queryByText("HTTP 409: session busy on backend")).not.toBeInTheDocument();
  });

  test("clicking show-details toggle reveals raw detail", async () => {
    const user = userEvent.setup();
    render(
      <ErrorBlock
        friendly={{
          title: "伺服器發生錯誤，請再試一次。",
          detail: "stack trace ...",
          retriable: true,
        }}
        onRetry={vi.fn()}
        source="pre-stream"
        errorClass="pre-stream-500"
      />,
    );

    await user.click(screen.getByRole("button", { name: copy.errorBlock.showDetails }));
    expect(screen.getByTestId("error-raw-detail")).toHaveTextContent("stack trace ...");
  });

  test("Retry button hidden when retriable=false", () => {
    render(
      <ErrorBlock
        friendly={{
          title: "找不到這個對話，請重新整理頁面以開始新對話。",
          retriable: false,
        }}
        onRetry={vi.fn()}
        source="pre-stream"
        errorClass="pre-stream-404"
      />,
    );
    expect(screen.queryByRole("button", { name: copy.errorBlock.retry })).not.toBeInTheDocument();
  });

  test("long detail (>200 chars) is truncated with show-more affordance", async () => {
    const user = userEvent.setup();
    const longDetail = "x".repeat(500);
    render(
      <ErrorBlock
        friendly={{ title: "伺服器發生錯誤，請再試一次。", detail: longDetail, retriable: true }}
        onRetry={vi.fn()}
        source="pre-stream"
        errorClass="pre-stream-500"
      />,
    );

    await user.click(screen.getByRole("button", { name: copy.errorBlock.showDetails }));
    const detail = screen.getByTestId("error-raw-detail");
    expect(detail.textContent!.length).toBeLessThan(longDetail.length);
  });

  test('source="mid-stream" renders with inline-error-block testId', () => {
    render(
      <ErrorBlock
        friendly={{ title: "回覆過程中連線中斷。", retriable: true }}
        onRetry={vi.fn()}
        source="mid-stream"
        errorClass="mid-stream"
      />,
    );
    expect(screen.getByTestId("inline-error-block")).toBeInTheDocument();
    expect(screen.getByTestId("inline-error-block")).toHaveAttribute(
      "data-error-source",
      "mid-stream",
    );
    expect(screen.queryByTestId("stream-error-block")).not.toBeInTheDocument();
  });

  test('outer container carries role="alert" so screen readers interrupt and announce errors', () => {
    render(
      <ErrorBlock
        friendly={{ title: "伺服器發生錯誤，請再試一次。", retriable: false }}
        source="pre-stream"
        errorClass="pre-stream-500"
      />,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  test("toggle button is not rendered when friendly.detail is absent", () => {
    render(
      <ErrorBlock
        friendly={{ title: "發生錯誤，請再試一次。", retriable: false }}
        source="pre-stream"
        errorClass="unknown"
      />,
    );
    expect(screen.getByTestId("error-title")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: copy.errorBlock.showDetails }),
    ).not.toBeInTheDocument();
    expect(screen.queryByTestId("error-raw-detail")).not.toBeInTheDocument();
  });
});
