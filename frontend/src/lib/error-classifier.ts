import { ChatHttpError } from "./chat-http-error"

export type ErrorClass =
  | "pre-stream-422"
  | "pre-stream-404"
  | "pre-stream-409"
  | "pre-stream-500"
  | "pre-stream-5xx"
  | "network"
  | "mid-stream"
  | "unknown"

const STATUS_MAP: Record<number, ErrorClass> = {
  422: "pre-stream-422",
  404: "pre-stream-404",
  409: "pre-stream-409",
  500: "pre-stream-500",
}

export function classifyError(err: unknown): ErrorClass {
  if (err instanceof TypeError && /fetch/i.test(err.message)) {
    return "network"
  }

  if (err instanceof ChatHttpError) {
    const mapped = STATUS_MAP[err.status]
    if (mapped) return mapped
    if (err.status >= 500 && err.status < 600) return "pre-stream-5xx"
  }

  if (err != null && typeof err === "object" && "status" in err) {
    const status = (err as { status: unknown }).status
    if (typeof status === "number") {
      const mapped = STATUS_MAP[status]
      if (mapped) return mapped
      if (status >= 500 && status < 600) return "pre-stream-5xx"
    }
  }

  return "unknown"
}
