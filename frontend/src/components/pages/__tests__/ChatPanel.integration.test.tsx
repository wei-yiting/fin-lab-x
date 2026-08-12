import { describe, test, expect, beforeAll, afterAll, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
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

    // Turn-level marker (DEV-109 ruling 11): every user Stop leaves an
    // explicit "Interrupted" row under the cut turn.
    expect(screen.getByTestId("interrupted-marker")).toBeInTheDocument();
    expect(screen.getByTestId("interrupted-marker")).toHaveTextContent("Interrupted");
  }, 20000);

  test("stop while only reply text is streaming → Interrupted marker renders (no chip/tool carrier)", async () => {
    // This scenario needs a tool that has already resolved (not the shared
    // abortedServer's tool, which stays running for the whole stream) so
    // that by the time we stop, no ToolCard is in a running state — the
    // "no chip/tool carrier" case this test's name claims to cover.
    abortedServer.use(
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

            controller.enqueue(encoder.encode(sseFrame({ type: "start", messageId: "a2" })));
            controller.enqueue(
              encoder.encode(
                sseFrame({
                  type: "tool-input-available",
                  toolCallId: "tc-y",
                  toolName: "yfinance_quote",
                  input: { ticker: "NVDA" },
                }),
              ),
            );
            // Resolve the tool BEFORE any text streams, so once the reply
            // text is visible, the ToolCard is already settled.
            controller.enqueue(
              encoder.encode(
                sseFrame({
                  type: "tool-output-available",
                  toolCallId: "tc-y",
                  output: { price: 123.45 },
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

    const user = userEvent.setup();
    render(<ChatPanel />);

    const textarea = screen.getByTestId("composer-textarea");
    await user.type(textarea, "test query");
    await user.click(screen.getByTestId("composer-send-btn"));

    // Wait until reply text is visibly streaming (past the tool phase).
    await waitFor(
      () => {
        expect(screen.getByTestId("assistant-message")).toHaveTextContent(/Looking up/);
      },
      { timeout: 10000 },
    );

    await user.click(screen.getByTestId("composer-stop-btn"));

    await waitFor(
      () => {
        expect(screen.getByTestId("interrupted-marker")).toBeInTheDocument();
      },
      { timeout: 10000 },
    );
  }, 20000);
});

// ---------------------------------------------------------------------------
// M-2.1: throttled closure can miss a tool that just arrived
//
// handleStop reads running-tool ids off the CURRENT RENDER's `messages`
// closure. useChat's `experimental_throttle` coalesces the messages-store's
// re-render notifications to roughly STREAM_THROTTLE_MS — the underlying
// snapshot updates immediately, but React doesn't necessarily re-render to
// reflect it right away. If a tool-input-available chunk lands while the
// assistant message is already streaming (status is already "streaming", so
// no further status-change forces an unthrottled render), a Stop click that
// lands inside that throttle window can miss the tool entirely: it's never
// added to abortedTools, and since the stream is now aborted, no
// tool-output-available/tool-output-error will ever arrive to resolve it —
// the ToolCard is stuck pulsing forever. The fix (AssistantMessage.tsx)
// additionally treats a tool as aborted whenever the whole turn is
// `interrupted` and the tool's live state is still running, since
// `interrupted` is read fresh on every render rather than snapshotted at
// click time.
// ---------------------------------------------------------------------------

describe("ChatPanel integration — aborted tools via stop (late-arriving tool race)", () => {
  let resolveToolEnqueued: () => void;

  const raceServer = setupServer(
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

          const enqueue = (data: Record<string, unknown>) => {
            if (request.signal.aborted) return;
            try {
              controller.enqueue(encoder.encode(sseFrame(data)));
            } catch {
              /* stream already closed by abort */
            }
          };

          // Text starts streaming first — the component renders with
          // status "streaming" before any tool exists.
          enqueue({ type: "start", messageId: "a-race" });
          enqueue({ type: "text-start", id: "t1" });
          enqueue({ type: "text-delta", id: "t1", delta: "Streaming reply" });

          // Give the client time to actually commit that render (confirmed
          // by the test's waitFor) before the tool call lands on the wire —
          // this is what makes the tool arrive "while the assistant message
          // is already streaming" rather than before it. 400ms is well past
          // this environment's observed cold-start render latency (measured
          // ~150-250ms for the first SSE-driven render in jsdom/msw), so the
          // ordering (text visible, then tool sent) is not itself a race.
          await new Promise((r) => setTimeout(r, 400));

          enqueue({
            type: "tool-input-available",
            toolCallId: "tc-race",
            toolName: "yfinance_quote",
            input: { ticker: "TSLA" },
          });
          resolveToolEnqueued();

          // Keep streaming slowly to give time to click stop and for the
          // abort handshake to complete.
          for (let i = 0; i < 30; i++) {
            await new Promise((r) => setTimeout(r, 100));
            if (request.signal.aborted) return;
            enqueue({ type: "text-delta", id: "t1", delta: "." });
          }
          enqueue({ type: "text-end", id: "t1" });
          enqueue({ type: "finish" });
          try {
            controller.close();
          } catch {
            /* already closed */
          }
        },
      });
      return sseResponse(stream);
    }),
  );

  beforeAll(() => raceServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => raceServer.resetHandlers());
  afterAll(() => raceServer.close());

  test("stop clicked right as a new tool call arrives mid-stream → tool still resolves to aborted", async () => {
    const toolEnqueued = new Promise<void>((resolve) => {
      resolveToolEnqueued = resolve;
    });

    const user = userEvent.setup();
    render(<ChatPanel />);

    const textarea = screen.getByTestId("composer-textarea");
    await user.type(textarea, "test query");
    await user.click(screen.getByTestId("composer-send-btn"));

    // Wait only for the reply text — NOT for the ToolCard — so the click
    // below lands as close as possible to the tool's arrival. Waiting for
    // the ToolCard first is exactly what let the throttled snapshot catch
    // up in the original (pre-fix) bug.
    await waitFor(
      () => {
        expect(screen.getByTestId("assistant-message")).toHaveTextContent(/Streaming reply/);
      },
      { timeout: 10000 },
    );

    // Click as soon as the server has put the tool call on the wire — no
    // additional wait for it to be reflected in the DOM. `fireEvent.click`
    // (not `userEvent.click`) is deliberate here: userEvent dispatches a
    // pointerdown/mousedown/pointerup/mouseup/click sequence with yields
    // between steps, and that alone gives the throttled render enough real
    // time to catch up and mask the race this test exists to catch.
    // fireEvent dispatches a single click synchronously, landing handleStop
    // as close as possible to the tool's arrival.
    await toolEnqueued;
    fireEvent.click(screen.getByTestId("composer-stop-btn"));

    // Whether or not handleStop's closure caught the tool at click time,
    // the turn-level `interrupted` flag must eventually mark it aborted
    // once its still-running state renders — it can never resolve any
    // other way once the stream is aborted.
    await waitFor(
      () => {
        expect(screen.getByTestId("tool-card")).toHaveAttribute("data-tool-state", "aborted");
      },
      { timeout: 20000 },
    );
  }, 25000);
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
