import { ChatHttpError } from "./chat-http";
import { preStreamHttpMap } from "./error-messages";
import type { ErrorClass } from "@/models";

export type { ErrorClass };

function statusToClass(status: number): ErrorClass | undefined {
  const mapped = preStreamHttpMap[status];
  if (mapped) return mapped.class;
  if (status >= 500 && status < 600) return "pre-stream-5xx";
  return undefined;
}

export function classifyError(err: unknown): ErrorClass {
  if (err instanceof TypeError && /fetch/i.test(err.message)) {
    return "network";
  }

  if (err instanceof ChatHttpError) {
    return statusToClass(err.status) ?? "unknown";
  }

  if (err != null && typeof err === "object" && "status" in err) {
    const status = (err as { status: unknown }).status;
    if (typeof status === "number") {
      const cls = statusToClass(status);
      if (cls) return cls;
    }
  }

  return "unknown";
}
