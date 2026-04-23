import { test, expect, beforeAll, afterAll } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

const server = setupServer(
  http.post("/api/v1/chat", () => HttpResponse.json({ error: "boom" }, { status: 500 })),
);

beforeAll(() => server.listen());
afterAll(() => server.close());

test("user message remains in messages array after pre-stream HTTP 500", async () => {
  const transport = new DefaultChatTransport({ api: "/api/v1/chat" });
  const { result } = renderHook(() => useChat({ transport, id: "test" }));

  await act(async () => {
    result.current.sendMessage({ text: "test message" });
  });

  await waitFor(() => expect(result.current.error).toBeTruthy());

  expect(result.current.messages).toHaveLength(1);
  expect(result.current.messages[0].role).toBe("user");
});
