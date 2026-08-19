import { describe, test, expect, beforeAll, afterAll, afterEach, vi } from "vitest";

// Exactly one ChatPanel integration case verifies the stall wiring, with a
// mocked small threshold against MSW real time. The mock is file-level
// (vi.mock hoists); the 10s production default is locked by the
// useStallTimer fake-timer unit test instead.
vi.mock("@/lib/timing", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/timing")>();
  return { ...actual, STALL_THRESHOLD_MS: 700 };
});
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
// Stop during the dead-air placeholder window
//
// A Stop that lands before the assistant message has anything renderable
// (the placeholder is the only visible content — no chip, no tool card)
// must still leave an "Interrupted" row. This is the window abortedTools
// cannot cover (no tool call exists yet) and the earlier "no chip/tool
// carrier" case above cannot cover either (that one has reply text already
// streaming).
// ---------------------------------------------------------------------------

describe("ChatPanel integration — stop during placeholder phase", () => {
  const placeholderStopServer = setupServer(
    http.post("/api/v1/chat", ({ request }) =>
      sseResponse(
        (() => {
          const encoder = new TextEncoder();
          return new ReadableStream({
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

              for (let tick = 0; tick < 30; tick++) {
                await new Promise((r) => setTimeout(r, 100));
                if (request.signal.aborted) return;
              }

              controller.enqueue(encoder.encode(sseFrame({ type: "text-start", id: "t1" })));
              controller.enqueue(
                encoder.encode(sseFrame({ type: "text-delta", id: "t1", delta: "late answer" })),
              );
              controller.enqueue(encoder.encode(sseFrame({ type: "text-end", id: "t1" })));
              controller.enqueue(encoder.encode(sseFrame({ type: "finish" })));
              controller.close();
            },
          });
        })(),
      ),
    ),
  );

  beforeAll(() => placeholderStopServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => placeholderStopServer.resetHandlers());
  afterAll(() => placeholderStopServer.close());

  test("stop while the dead-air placeholder is the only visible content → Interrupted marker renders", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    const textarea = screen.getByTestId("composer-textarea");
    await user.type(textarea, "test query");
    await user.click(screen.getByTestId("composer-send-btn"));

    await waitFor(
      () => {
        expect(screen.getByTestId("activity-placeholder")).toBeInTheDocument();
      },
      { timeout: 10000 },
    );
    expect(screen.queryByTestId("tool-card")).not.toBeInTheDocument();

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
// Dead-air placeholder stall degradation
//
// The global stall stopwatch (useStallTimer) also degrades the placeholder's
// copy from "Thinking" to "Still working" when the wire goes silent past the
// threshold, and any arriving stream part must zero it again. Mocked small
// threshold + real MSW time — the 10s production default is locked by the
// useStallTimer fake-timer unit test instead.
// ---------------------------------------------------------------------------

describe("ChatPanel integration — placeholder stall degradation (the single stall-wiring case)", () => {
  const SMALL_THRESHOLD = 700;
  const stallServer = setupServer(
    http.post("/api/v1/chat", () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        async start(controller) {
          const send = (d: Record<string, unknown>) =>
            controller.enqueue(encoder.encode(sseFrame(d)));
          send({ type: "start", messageId: "m-stall" });
          // Phase 1 — silence beyond the mocked threshold with nothing
          // renderable yet → degraded copy on the placeholder. The hold is
          // generous (threshold + 2.5s) so the degraded copy stays
          // observable even under parallel-suite load.
          await new Promise((r) => setTimeout(r, SMALL_THRESHOLD + 2500));

          // Phase 2 — the reset half of the wiring. Whitespace-only text
          // deltas are stream parts (they change `messages`, so the
          // layout-effect calls notifyActivity) but are NOT renderable
          // (hasVisibleReplyText trims them to nothing), so the dead-air
          // window stays open and the same placeholder element must revert
          // to the non-degraded copy. Spaced well under the threshold so the
          // non-degraded copy holds for the whole burst.
          send({ type: "text-start", id: "t1" });
          for (let i = 0; i < 12; i++) {
            send({ type: "text-delta", id: "t1", delta: "\n" });
            await new Promise((r) => setTimeout(r, SMALL_THRESHOLD / 4));
          }

          // Phase 3 — the real answer arrives and replaces the placeholder.
          send({ type: "text-delta", id: "t1", delta: "done" });
          send({ type: "text-end", id: "t1" });
          send({ type: "finish" });
          controller.close();
        },
      });
      return sseResponse(stream);
    }),
  );

  beforeAll(() => stallServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => stallServer.resetHandlers());
  afterAll(() => stallServer.close());

  test("silence degrades the copy, an arriving part resets the stopwatch, the answer replaces it", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    await user.type(screen.getByTestId("composer-textarea"), "tell me");
    await user.click(screen.getByTestId("composer-send-btn"));

    await waitFor(
      () => {
        expect(screen.getByTestId("activity-placeholder")).toHaveTextContent("Still working");
      },
      { timeout: 5000 },
    );

    // Any stream part zeroes the global stall stopwatch. The whitespace
    // deltas keep the placeholder mounted (nothing renderable yet) while
    // restoring the non-degraded copy — without this assertion the case
    // would pass even with notifyActivity disconnected from part arrival.
    await waitFor(
      () => {
        expect(screen.getByTestId("activity-placeholder")).toHaveTextContent("Thinking");
      },
      { timeout: 5000 },
    );

    await waitFor(
      () => {
        expect(screen.getByText("done")).toBeInTheDocument();
      },
      { timeout: 5000 },
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

describe("ChatPanel integration — onFinish does not announce non-normal completions", () => {
  const announcerServer = setupServer(
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

          controller.enqueue(encoder.encode(sseFrame({ type: "start", messageId: "a-abrt" })));
          controller.enqueue(encoder.encode(sseFrame({ type: "text-start", id: "t1" })));
          controller.enqueue(
            encoder.encode(sseFrame({ type: "text-delta", id: "t1", delta: "partial..." })),
          );
          // Hold open so the test can click Stop while streaming.
          for (let i = 0; i < 30; i++) {
            await new Promise((r) => setTimeout(r, 100));
            if (request.signal.aborted) return;
          }
          controller.enqueue(encoder.encode(sseFrame({ type: "text-end", id: "t1" })));
          controller.enqueue(encoder.encode(sseFrame({ type: "finish" })));
          controller.close();
        },
      });
      return sseResponse(stream);
    }),
  );

  beforeAll(() => announcerServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => announcerServer.resetHandlers());
  afterAll(() => announcerServer.close());

  test("clicking stop while streaming → SR announcer does not say 'Response complete'", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    const textarea = screen.getByTestId("composer-textarea");
    await user.type(textarea, "go");
    await user.click(screen.getByTestId("composer-send-btn"));

    await waitFor(
      () => {
        expect(screen.getByText(/partial.../)).toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    await user.click(screen.getByTestId("composer-stop-btn"));

    // Wait for the stream to actually finish (onFinish fires asynchronously
    // after stop()). The status returns to "ready" once the abort completes.
    await waitFor(
      () => {
        expect(screen.queryByTestId("composer-stop-btn")).not.toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    // The aria-live polite region must not announce "Response complete" on
    // a user-initiated abort — that text is reserved for natural completion.
    const announcer = screen.getByRole("status");
    expect(announcer).not.toHaveTextContent("Response complete");
  }, 15000);

  test("natural stream completion → SR announcer says 'Response complete'", async () => {
    // Regression guard for the abort branch: make sure we did not regress
    // the happy-path announcement by accident.
    const happyServer = setupServer(
      http.post("/api/v1/chat", () => sseResponse(happyStream("a-happy", "all done"))),
    );
    happyServer.listen({ onUnhandledRequest: "bypass" });

    try {
      const user = userEvent.setup();
      render(<ChatPanel />);

      await user.type(screen.getByTestId("composer-textarea"), "go");
      await user.click(screen.getByTestId("composer-send-btn"));

      await waitFor(
        () => {
          expect(screen.getByRole("status")).toHaveTextContent("Response complete");
        },
        { timeout: 5000 },
      );
    } finally {
      happyServer.close();
    }
  }, 15000);

  test("Regenerate clears the live region so a second natural completion announces again", async () => {
    // handleRegenerate must clear the completion flag the same way handleSend
    // does — otherwise the live region still holds the first turn's
    // "Response complete" and the second onFinish writes identical text,
    // which is not a DOM mutation a screen reader would pick up.
    let call = 0;
    const regenServer = setupServer(
      http.post("/api/v1/chat", () => {
        call += 1;
        if (call === 1) {
          return sseResponse(happyStream("a-first", "first answer"));
        }
        // Hold the second turn open briefly — a same-tick response would
        // make the cleared live-region window too transient for `waitFor`
        // to ever observe before the "finish" text reappears.
        const encoder = new TextEncoder();
        const stream = new ReadableStream({
          async start(controller) {
            controller.enqueue(encoder.encode(sseFrame({ type: "start", messageId: "a-second" })));
            controller.enqueue(encoder.encode(sseFrame({ type: "text-start", id: "t1" })));
            await new Promise((r) => setTimeout(r, 300));
            controller.enqueue(
              encoder.encode(sseFrame({ type: "text-delta", id: "t1", delta: "second answer" })),
            );
            controller.enqueue(encoder.encode(sseFrame({ type: "text-end", id: "t1" })));
            controller.enqueue(encoder.encode(sseFrame({ type: "finish" })));
            controller.close();
          },
        });
        return sseResponse(stream);
      }),
    );
    regenServer.listen({ onUnhandledRequest: "bypass" });

    try {
      const user = userEvent.setup();
      render(<ChatPanel />);

      await user.type(screen.getByTestId("composer-textarea"), "go");
      await user.click(screen.getByTestId("composer-send-btn"));

      await waitFor(
        () => {
          expect(screen.getByRole("status")).toHaveTextContent("Response complete");
        },
        { timeout: 5000 },
      );

      await user.click(screen.getByTestId("regenerate-btn"));

      await waitFor(
        () => {
          expect(screen.getByRole("status")).not.toHaveTextContent("Response complete");
        },
        { timeout: 5000 },
      );

      await waitFor(
        () => {
          expect(screen.getByText("second answer")).toBeInTheDocument();
        },
        { timeout: 5000 },
      );
      await waitFor(
        () => {
          expect(screen.getByRole("status")).toHaveTextContent("Response complete");
        },
        { timeout: 5000 },
      );
    } finally {
      regenServer.close();
    }
  }, 15000);

  test("mid-stream SSE error (isError=true) → SR announcer does not say 'Response complete'", async () => {
    // SSE `error` chunk → useChat catches the rethrown error → onFinish
    // fires with isError=true (isAbort=false). The ChatPanel must NOT mark
    // the completion flag on this branch — disconnect and error paths are
    // announced separately by ErrorBlock's role="alert", not this region.
    // Verifying the negative: announcer never reads "Response complete".
    const errorServer = setupServer(
      http.post("/api/v1/chat", () => {
        const encoder = new TextEncoder();
        const stream = new ReadableStream({
          start(controller) {
            controller.enqueue(encoder.encode(sseFrame({ type: "start", messageId: "a-mid-err" })));
            controller.enqueue(encoder.encode(sseFrame({ type: "text-start", id: "t1" })));
            controller.enqueue(
              encoder.encode(sseFrame({ type: "text-delta", id: "t1", delta: "partial answer" })),
            );
            // SSE error chunk — processUIMessageStream rethrows, which
            // useChat catches → onFinish fires with isError=true.
            controller.enqueue(
              encoder.encode(sseFrame({ type: "error", errorText: "rate limit exceeded" })),
            );
            controller.close();
          },
        });
        return sseResponse(stream);
      }),
    );
    errorServer.listen({ onUnhandledRequest: "bypass" });

    try {
      const user = userEvent.setup();
      render(<ChatPanel />);

      await user.type(screen.getByTestId("composer-textarea"), "go");
      await user.click(screen.getByTestId("composer-send-btn"));

      // Wait for the inline retry button (proxy for "mid-stream error
      // reached ChatPanel + onFinish has fired").
      await waitFor(
        () => {
          expect(screen.getByTestId("error-retry-btn")).toBeInTheDocument();
        },
        { timeout: 5000 },
      );

      // Negative assertion: under any onFinish path with isError=true the
      // SR announcer must not read "Response complete".
      expect(screen.getByRole("status")).not.toHaveTextContent("Response complete");
    } finally {
      errorServer.close();
    }
  }, 15000);

  test("transport network failure (isDisconnect=true) → SR announcer does not say 'Response complete'", async () => {
    // HttpResponse.error() in MSW translates to a TypeError("fetch failed")
    // at the fetch layer. In useChat's catch block:
    //     err instanceof TypeError && err.message.includes("fetch")
    // → isError=true AND isDisconnect=true. The ChatPanel must short-circuit
    // on isDisconnect too — otherwise the "finish" event leaks and the
    // completion announcer region could announce "Response complete" before
    // the status flips to "error".
    const disconnectServer = setupServer(http.post("/api/v1/chat", () => HttpResponse.error()));
    disconnectServer.listen({ onUnhandledRequest: "bypass" });

    try {
      const user = userEvent.setup();
      render(<ChatPanel />);

      await user.type(screen.getByTestId("composer-textarea"), "go");
      await user.click(screen.getByTestId("composer-send-btn"));

      // Wait until the disconnect propagates and the stream-error block
      // surfaces (proxy for "onFinish has fired with isDisconnect=true").
      await waitFor(
        () => {
          expect(screen.getByTestId("stream-error-block")).toBeInTheDocument();
        },
        { timeout: 5000 },
      );

      expect(screen.getByRole("status")).not.toHaveTextContent("Response complete");
    } finally {
      disconnectServer.close();
    }
  }, 15000);
});

// ---------------------------------------------------------------------------
// Stop + clear race
//
// During active streaming, clicking clear should stop the stream, reset the
// chat ID, and show EmptyState with no residual messages.
// ---------------------------------------------------------------------------

describe("ChatPanel integration — reasoning chips golden path", () => {
  const chipServer = setupServer(
    http.post("/api/v1/chat", () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        async start(controller) {
          const send = (d: Record<string, unknown>) =>
            controller.enqueue(encoder.encode(sseFrame(d)));
          send({ type: "start", messageId: "m-chip" });
          send({ type: "reasoning-start", id: "reasoning-0" });
          send({ type: "reasoning-delta", id: "reasoning-0", delta: "Analyzing the filing" });
          await new Promise((r) => setTimeout(r, 150));
          send({ type: "reasoning-end", id: "reasoning-0" });
          send({ type: "text-start", id: "t1" });
          send({ type: "text-delta", id: "t1", delta: "the answer" });
          send({ type: "text-end", id: "t1" });
          send({ type: "finish" });
          controller.close();
        },
      });
      return sseResponse(stream);
    }),
  );

  beforeAll(() => chipServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => chipServer.resetHandlers());
  afterAll(() => chipServer.close());

  test("chip streams its text, then collapses to Thought for Xs when the answer lands", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    await user.type(screen.getByTestId("composer-textarea"), "tell me");
    await user.click(screen.getByTestId("composer-send-btn"));

    // Streaming: chip expanded with live reasoning text.
    await waitFor(
      () => {
        const chip = screen.getByTestId("reasoning-chip");
        expect(chip).toHaveAttribute("data-state", "streaming");
        expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("Analyzing the filing");
      },
      { timeout: 5000 },
    );

    // Completed: chip collapsed to a duration header; the answer rendered;
    // the reasoning text is no longer visible but reachable by expanding.
    await waitFor(
      () => {
        expect(screen.getByText("the answer")).toBeInTheDocument();
        expect(screen.getByTestId("reasoning-chip")).toHaveAttribute("data-state", "collapsed");
      },
      { timeout: 5000 },
    );
    expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent(/Thought for \d+s/);
    expect(screen.queryByTestId("reasoning-chip-body")).not.toBeInTheDocument();

    // Post-hoc expand: clicking the collapsed header re-opens it via the user override.
    await user.click(screen.getByTestId("reasoning-chip-header"));
    expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("Analyzing the filing");
  }, 15000);
});

describe("ChatPanel integration — abort keeps a collapsed half-chip", () => {
  const abortServer = setupServer(
    http.post("/api/v1/chat", ({ request }) => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        async start(controller) {
          const send = (d: Record<string, unknown>) =>
            controller.enqueue(encoder.encode(sseFrame(d)));
          request.signal.addEventListener(
            "abort",
            () => {
              try {
                controller.close();
              } catch {
                /* already closed */
              }
            },
            { once: true },
          );
          send({ type: "start", messageId: "m-abort" });
          send({ type: "reasoning-start", id: "reasoning-0" });
          send({ type: "reasoning-delta", id: "reasoning-0", delta: "half a thought" });
          // Hold open (no reasoning-end) until abort.
          for (let i = 0; i < 30; i++) {
            await new Promise((r) => setTimeout(r, 100));
            if (request.signal.aborted) return;
          }
          controller.close();
        },
      });
      return sseResponse(stream);
    }),
  );

  beforeAll(() => abortServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => abortServer.resetHandlers());
  afterAll(() => abortServer.close());

  test("stop mid-reasoning → chip collapses with Stopped header, text kept", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    await user.type(screen.getByTestId("composer-textarea"), "tell me");
    await user.click(screen.getByTestId("composer-send-btn"));

    await waitFor(
      () => {
        expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("half a thought");
      },
      { timeout: 5000 },
    );

    await user.click(screen.getByTestId("composer-stop-btn"));

    await waitFor(
      () => {
        const chip = screen.getByTestId("reasoning-chip");
        expect(chip).toHaveAttribute("data-state", "collapsed");
        expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent(
          /Stopped — thought for \d+s/,
        );
      },
      { timeout: 5000 },
    );

    // The half text is preserved behind the header (expand to read).
    await user.click(screen.getByTestId("reasoning-chip-header"));
    expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("half a thought");
  }, 15000);
});

describe("ChatPanel integration — chip header stall degradation (shares the file-level mocked threshold)", () => {
  // Mock small threshold + real MSW time. The 10s default itself is locked
  // by the useStallTimer fake-timer unit test.
  const SMALL_THRESHOLD = 700;
  const stallServer = setupServer(
    http.post("/api/v1/chat", () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        async start(controller) {
          const send = (d: Record<string, unknown>) =>
            controller.enqueue(encoder.encode(sseFrame(d)));
          send({ type: "start", messageId: "m-stall" });
          send({ type: "reasoning-start", id: "reasoning-0" });
          send({ type: "reasoning-delta", id: "reasoning-0", delta: "thinking hard" });
          // Silence beyond the mocked threshold → degraded copy on the
          // streaming chip header; then a delta arrives and resets it. The
          // hold is generous (threshold + 2.5s) so the degraded header stays
          // observable even under parallel-suite load.
          await new Promise((r) => setTimeout(r, SMALL_THRESHOLD + 2500));
          send({ type: "reasoning-delta", id: "reasoning-0", delta: " more" });
          await new Promise((r) => setTimeout(r, 150));
          send({ type: "reasoning-end", id: "reasoning-0" });
          send({ type: "text-start", id: "t1" });
          send({ type: "text-delta", id: "t1", delta: "done" });
          send({ type: "text-end", id: "t1" });
          send({ type: "finish" });
          controller.close();
        },
      });
      return sseResponse(stream);
    }),
  );

  beforeAll(() => stallServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => stallServer.resetHandlers());
  afterAll(() => stallServer.close());

  test("silence past threshold degrades the streaming chip header; a delta restores it", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    await user.type(screen.getByTestId("composer-textarea"), "tell me");
    await user.click(screen.getByTestId("composer-send-btn"));

    await waitFor(
      () => {
        expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent("Still working…");
      },
      { timeout: 5000 },
    );

    // The late delta resets the stopwatch → normal copy returns (tolerance:
    // we only assert the recovery, not frame-exact timing).
    await waitFor(
      () => {
        expect(screen.getByText("done")).toBeInTheDocument();
      },
      { timeout: 5000 },
    );
  }, 15000);
});

describe("ChatPanel integration — abort-then-resend coexistence", () => {
  let call = 0;
  const resendServer = setupServer(
    http.post("/api/v1/chat", ({ request }) => {
      call++;
      const thisCall = call;
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        async start(controller) {
          const send = (d: Record<string, unknown>) =>
            controller.enqueue(encoder.encode(sseFrame(d)));
          request.signal.addEventListener(
            "abort",
            () => {
              try {
                controller.close();
              } catch {
                /* already closed */
              }
            },
            { once: true },
          );
          send({ type: "start", messageId: `m-${thisCall}` });
          send({ type: "reasoning-start", id: "reasoning-0" });
          send({
            type: "reasoning-delta",
            id: "reasoning-0",
            delta: thisCall === 1 ? "first turn thinking" : "second turn thinking",
          });
          if (thisCall === 1) {
            // Hold open until aborted (no reasoning-end).
            for (let i = 0; i < 30; i++) {
              await new Promise((r) => setTimeout(r, 100));
              if (request.signal.aborted) return;
            }
            controller.close();
            return;
          }
          await new Promise((r) => setTimeout(r, 100));
          send({ type: "reasoning-end", id: "reasoning-0" });
          send({ type: "text-start", id: "t1" });
          send({ type: "text-delta", id: "t1", delta: "second answer" });
          send({ type: "text-end", id: "t1" });
          send({ type: "finish" });
          controller.close();
        },
      });
      return sseResponse(stream);
    }),
  );

  beforeAll(() => resendServer.listen({ onUnhandledRequest: "bypass" }));
  afterEach(() => resendServer.resetHandlers());
  afterAll(() => {
    resendServer.close();
    call = 0;
  });

  test("stop first turn → resend → both bubbles coexist; Stopped chip persists; new chip untainted", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    await user.type(screen.getByTestId("composer-textarea"), "first");
    await user.click(screen.getByTestId("composer-send-btn"));
    await waitFor(
      () => {
        expect(screen.getByTestId("reasoning-chip-body")).toHaveTextContent("first turn thinking");
      },
      { timeout: 5000 },
    );
    // Real-timer test: hold a beat before stopping so the frozen duration is
    // guaranteed to round to a non-zero number of seconds. Without this, the
    // wiped-map regression (re-freezing at 0s) can coincidentally match a
    // fast first turn's own near-zero duration and the assertion below would
    // not discriminate a broken fix from a correct one.
    await new Promise((r) => setTimeout(r, 1200));
    await user.click(screen.getByTestId("composer-stop-btn"));
    await waitFor(
      () => {
        expect(screen.getByTestId("reasoning-chip-header")).toHaveTextContent(/Stopped/);
      },
      { timeout: 5000 },
    );
    // Pin the exact displayed duration before the second turn starts — this
    // guards against the timing map being wiped wholesale on handleSend,
    // which would re-freeze this already-completed chip at 0s. A loose
    // /\d+s/ regex would still pass on "0s", so capture the literal text and
    // require an exact match after the second send.
    const firstHeaderTextBeforeSecondTurn =
      screen.getByTestId("reasoning-chip-header").textContent ?? "";
    expect(firstHeaderTextBeforeSecondTurn).toMatch(/Stopped — thought for [1-9]\d*s/);

    await user.type(screen.getByTestId("composer-textarea"), "second");
    await user.click(screen.getByTestId("composer-send-btn"));

    await waitFor(
      () => {
        expect(screen.getByText("second answer")).toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    // Two assistant bubbles; the aborted chip's Stopped header persists on
    // the first while the second collapsed cleanly.
    expect(screen.getAllByTestId("assistant-message")).toHaveLength(2);
    const headers = screen
      .getAllByTestId("reasoning-chip-header")
      .map((el) => el.textContent ?? "");
    expect(headers.some((h) => /Stopped — thought for \d+s/.test(h))).toBe(true);
    expect(headers.some((h) => /^Thought for \d+s/.test(h))).toBe(true);
    // The first chip's duration must be byte-for-byte unchanged by the
    // second turn's send — this is the exact assertion the old loose regex
    // could not catch (it also matches "Stopped — thought for 0s").
    expect(headers).toContain(firstHeaderTextBeforeSecondTurn);
    // No degraded copy leaked into the resent turn (stopwatch reset).
    expect(screen.queryByText("Still working…")).not.toBeInTheDocument();
  }, 20000);
});
