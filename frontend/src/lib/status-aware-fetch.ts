import { ChatHttpError } from "./chat-http-error"

export const statusAwareFetch: typeof globalThis.fetch = async (input, init) => {
  const response = await globalThis.fetch(input, init)
  if (!response.ok) {
    const body = await response.text()
    throw new ChatHttpError(response.status, body)
  }
  return response
}
