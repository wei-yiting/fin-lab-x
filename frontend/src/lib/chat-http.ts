/**
 * HTTP layer for the chat transport. The default `fetch` swallows
 * non-2xx responses into the `response.ok=false` path, which AI SDK
 * surfaces only as a generic "Failed to parse stream" error. To route
 * status-specific messages (422/404/409/500/...) through our error
 * classifier and friendly-message mapper, we need to throw a typed
 * error before the SDK sees the failed response.
 */
export class ChatHttpError extends Error {
  readonly status: number;

  constructor(status: number, body: string) {
    super(body || `HTTP ${status}`);
    this.name = "ChatHttpError";
    this.status = status;
  }
}

export const statusAwareFetch: typeof globalThis.fetch = async (input, init) => {
  const response = await globalThis.fetch(input, init);
  if (!response.ok) {
    const body = await response.text();
    throw new ChatHttpError(response.status, body);
  }
  return response;
};
