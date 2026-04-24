import { describe, test, expect, beforeAll, afterAll, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderHook, act } from "@testing-library/react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { ChatPanel } from "../ChatPanel";

function sseFrame(data: Record<string, unknown>): string {
  return `data: ${JSON.stringify(data)}\n\n`;
}

function happyStream(messageId: string, text: string) {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(sseFrame({ type: "start", messageId })));
      controller.enqueue(encoder.encode(sseFrame({ type: "text-start", id: "t1" })));
      controller.enqueue(encoder.encode(sseFrame({ type: "text-delta", id: "t1", delta: text })));
      controller.enqueue(encoder.encode(sseFrame({ type: "text-end", id: "t1" })));
      controller.enqueue(encoder.encode(sseFrame({ type: "finish" })));
      controller.close();
    },
  });
}

function sseResponse(stream: ReadableStream) {
  return new HttpResponse(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "x-vercel-ai-ui-message-stream": "v1",
    },
  });
}

// ---------------------------------------------------------------------------
// Smart retry
//
// The AI SDK v6 DefaultChatTransport throws a plain Error (no .status) on
// HTTP errors. The ChatPanel's classifyError needs .status to detect
// pre-stream-4xx. We test the retry logic at the hook level: mock a server
// that returns 422 on first call, then succeeds. We verify that after the
// error, the user message survives and a subsequent sendMessage recovers.
// ---------------------------------------------------------------------------

describe("ChatPanel integration — smart retry (hook-level)", () => {
  let callCount = 0;

  const retryServer = setupServer(
    http.post("/api/v1/chat", async () => {
      callCount++;
      if (callCount === 1) {
        return new HttpResponse(happyStream("msg-1", "first response"), {
          headers: {
            "Content-Type": "text/event-stream",
            "x-vercel-ai-ui-message-stream": "v1",
          },
        });
      }
      if (callCount === 2) {
        return HttpResponse.json(
          { error: "last turn is not an assistant message" },
          { status: 422 },
        );
      }
      return new HttpResponse(happyStream("msg-3", "recovered"), {
        headers: {
          "Content-Type": "text/event-stream",
          "x-vercel-ai-ui-message-stream": "v1",
        },
      });
    }),
  );

  beforeAll(() => retryServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => {
    callCount = 0;
    retryServer.resetHandlers();
  });
  afterAll(() => retryServer.close());

  test("after 422 on regenerate, sendMessage with same text recovers", async () => {
    const transport = new DefaultChatTransport({ api: "/api/v1/chat" });
    const { result } = renderHook(() => useChat({ transport, id: "retry-test" }));

    // 1. Send initial message → success
    await act(async () => {
      result.current.sendMessage({ text: "first question" });
    });
    await waitFor(() => expect(result.current.status).toBe("ready"), { timeout: 5000 });
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].role).toBe("assistant");

    // 2. Regenerate → 422
    await act(async () => {
      result.current.regenerate({ messageId: result.current.messages[1].id });
    });
    await waitFor(() => expect(result.current.status).toBe("error"), { timeout: 5000 });
    expect(result.current.error).toBeTruthy();
    expect(callCount).toBe(2);

    // 3. Smart retry: sendMessage with original text → recovers
    await act(async () => {
      result.current.sendMessage({ text: "first question" });
    });
    await waitFor(() => expect(result.current.status).toBe("ready"), { timeout: 5000 });
    expect(callCount).toBe(3);

    const assistantMessages = result.current.messages.filter((m) => m.role === "assistant");
    expect(assistantMessages.length).toBeGreaterThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// Mid-stream retry does not duplicate user history
//
// When an SSE error arrives mid-stream, the inline Retry button in the
// AssistantMessage ErrorBlock must trigger regenerate() (which removes the
// failed assistant turn and re-runs with the existing user turn intact),
// NOT a pattern that re-appends the user message. Verify the message history
// still has exactly one user turn after retry.
// ---------------------------------------------------------------------------

describe("ChatPanel integration — mid-stream retry preserves user history", () => {
  let callCount = 0;

  const midStreamServer = setupServer(
    http.post("/api/v1/chat", () => {
      callCount++;
      const encoder = new TextEncoder();
      if (callCount === 1) {
        const stream = new ReadableStream({
          start(controller) {
            controller.enqueue(
              encoder.encode(sseFrame({ type: "start", messageId: "asst-mid-err" })),
            );
            controller.enqueue(encoder.encode(sseFrame({ type: "text-start", id: "t1" })));
            controller.enqueue(
              encoder.encode(
                sseFrame({ type: "text-delta", id: "t1", delta: "partial answer..." }),
              ),
            );
            // "rate limit" maps to a retriable mid-stream friendly error, so the
            // Retry button is rendered; see error-messages.ts midStreamPatterns.
            controller.enqueue(
              encoder.encode(sseFrame({ type: "error", errorText: "rate limit exceeded" })),
            );
            controller.close();
          },
        });
        return sseResponse(stream);
      }
      // Second request (from retry): succeeds
      return sseResponse(happyStream("asst-recovered", "full recovered response"));
    }),
  );

  beforeAll(() => midStreamServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => {
    callCount = 0;
    midStreamServer.resetHandlers();
  });
  afterAll(() => midStreamServer.close());

  test("Retry after mid-stream error does not duplicate user turns", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    const textarea = screen.getByTestId("composer-textarea");
    await user.type(textarea, "ask me something");
    await user.click(screen.getByTestId("composer-send-btn"));

    // Wait for the mid-stream error to surface as an inline-error-block (not
    // stream-error-block — ChatPanel detects the partial assistant message and
    // routes through the mid-stream-sse friendly mapper).
    await waitFor(
      () => {
        expect(screen.getByTestId("inline-error-block")).toBeInTheDocument();
      },
      { timeout: 5000 },
    );
    expect(screen.getByTestId("error-retry-btn")).toBeInTheDocument();

    // Before retry: exactly one user turn is visible
    expect(screen.getAllByTestId("user-bubble")).toHaveLength(1);
    expect(callCount).toBe(1);

    // Click Retry
    await user.click(screen.getByTestId("error-retry-btn"));

    // Recovery: second call fires, assistant finishes with recovered text
    await waitFor(
      () => {
        expect(callCount).toBe(2);
      },
      { timeout: 5000 },
    );
    await waitFor(
      () => {
        expect(screen.getByText(/full recovered response/)).toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    // After retry: still exactly one user turn — no duplication
    expect(screen.getAllByTestId("user-bubble")).toHaveLength(1);
  }, 15000);
});

// ---------------------------------------------------------------------------
// Aborted tools via stop
//
// When the user clicks stop while a tool is in input-available state, the
// ChatPanel's handleStop marks those tools as aborted. The ToolCard should
// display data-tool-state="aborted".
// ---------------------------------------------------------------------------

describe("ChatPanel integration — aborted tools via stop", () => {
  const abortedServer = setupServer(
    http.post("/api/v1/chat", ({ request }) => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        async start(controller) {
          const onAbort = () => {
            try {
              controller.close();
            } catch {
              /* already closed */
            }
          };
          request.signal.addEventListener("abort", onAbort, { once: true });

          controller.enqueue(encoder.encode(sseFrame({ type: "start", messageId: "a1" })));
          controller.enqueue(
            encoder.encode(
              sseFrame({
                type: "tool-input-available",
                toolCallId: "tc-x",
                toolName: "yfinance_quote",
                input: { ticker: "NVDA" },
              }),
            ),
          );
          controller.enqueue(encoder.encode(sseFrame({ type: "text-start", id: "t1" })));
          controller.enqueue(
            encoder.encode(sseFrame({ type: "text-delta", id: "t1", delta: "Looking up..." })),
          );

          // Keep streaming slowly to give time to click stop
          for (let i = 0; i < 30; i++) {
            await new Promise((r) => setTimeout(r, 100));
            if (request.signal.aborted) return;
            controller.enqueue(
              encoder.encode(sseFrame({ type: "text-delta", id: "t1", delta: "." })),
            );
          }
          controller.enqueue(encoder.encode(sseFrame({ type: "text-end", id: "t1" })));
          controller.enqueue(encoder.encode(sseFrame({ type: "finish" })));
          controller.close();
        },
      });
      return sseResponse(stream);
    }),
  );

  beforeAll(() => abortedServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => abortedServer.resetHandlers());
  afterAll(() => abortedServer.close());

  test("stop during streaming with running tool → ToolCard becomes aborted", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    const textarea = screen.getByTestId("composer-textarea");
    await user.type(textarea, "test query");
    await user.click(screen.getByTestId("composer-send-btn"));

    // Wait for the stop button to appear (indicates streaming is active)
    await waitFor(
      () => {
        expect(screen.getByTestId("composer-stop-btn")).toBeInTheDocument();
      },
      { timeout: 10000 },
    );

    // Wait for tool card to appear
    await waitFor(
      () => {
        expect(screen.getByTestId("tool-card")).toBeInTheDocument();
      },
      { timeout: 10000 },
    );

    // Click stop while tool is running
    await user.click(screen.getByTestId("composer-stop-btn"));

    // The tool should become aborted
    await waitFor(
      () => {
        expect(screen.getByTestId("tool-card")).toHaveAttribute("data-tool-state", "aborted");
      },
      { timeout: 10000 },
    );
  }, 20000);
});

// ---------------------------------------------------------------------------
// Stop + clear race
//
// During active streaming, clicking clear should stop the stream, reset the
// chat ID, and show EmptyState with no residual messages.
// ---------------------------------------------------------------------------

describe("ChatPanel integration — stop + clear", () => {
  const clearServer = setupServer(
    http.post("/api/v1/chat", ({ request }) => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        async start(controller) {
          const onAbort = () => {
            try {
              controller.close();
            } catch {
              /* already closed */
            }
          };
          request.signal.addEventListener("abort", onAbort, { once: true });

          controller.enqueue(encoder.encode(sseFrame({ type: "start", messageId: "a-clear" })));
          controller.enqueue(encoder.encode(sseFrame({ type: "text-start", id: "t1" })));
          controller.enqueue(
            encoder.encode(
              sseFrame({ type: "text-delta", id: "t1", delta: "streaming content here" }),
            ),
          );

          for (let i = 0; i < 30; i++) {
            await new Promise((r) => setTimeout(r, 100));
            if (request.signal.aborted) return;
            controller.enqueue(
              encoder.encode(sseFrame({ type: "text-delta", id: "t1", delta: ` chunk${i}` })),
            );
          }
          controller.enqueue(encoder.encode(sseFrame({ type: "text-end", id: "t1" })));
          controller.enqueue(encoder.encode(sseFrame({ type: "finish" })));
          controller.close();
        },
      });
      return sseResponse(stream);
    }),
  );

  beforeAll(() => clearServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => clearServer.resetHandlers());
  afterAll(() => clearServer.close());

  test("streaming → click clear → EmptyState, no residual messages", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    const textarea = screen.getByTestId("composer-textarea");
    await user.type(textarea, "stream me");
    await user.click(screen.getByTestId("composer-send-btn"));

    // Wait for streaming to start
    await waitFor(
      () => {
        expect(screen.getByText(/streaming content/)).toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    // Click clear during streaming
    await user.click(screen.getByTestId("composer-clear-btn"));

    // Should show empty state, no messages
    await waitFor(
      () => {
        expect(screen.getByTestId("empty-state")).toBeInTheDocument();
        expect(screen.queryByTestId("assistant-message")).not.toBeInTheDocument();
        expect(screen.queryByTestId("user-bubble")).not.toBeInTheDocument();
      },
      { timeout: 5000 },
    );
  });
});
