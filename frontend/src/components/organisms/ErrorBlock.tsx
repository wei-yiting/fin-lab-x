import { useState } from "react"
import { AlertCircle } from "lucide-react"
import { Button } from "@/components/primitives/button"
import type { FriendlyError } from "@/lib/error-messages"

export function ErrorBlock({
  friendly,
  onRetry,
  source,
  errorClass,
}: {
  friendly: FriendlyError
  onRetry: () => void
  source: "pre-stream" | "mid-stream"
  errorClass: string
}) {
  const [showDetail, setShowDetail] = useState(false)
  const [showMore, setShowMore] = useState(false)

  const testId = source === "pre-stream" ? "stream-error-block" : "inline-error-block"
  const truncateThreshold = 200
  const displayDetail = friendly.detail && !showMore && friendly.detail.length > truncateThreshold
    ? friendly.detail.slice(0, truncateThreshold) + "..."
    : friendly.detail

  return (
    <div
      data-testid={testId}
      data-error-source={source}
      data-error-class={errorClass}
      className="my-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3"
    >
      <div className="flex items-start gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
        <div className="flex-1 space-y-2">
          <h3 data-testid="error-title" className="text-sm font-medium text-destructive">
            {friendly.title}
          </h3>
          {friendly.detail && (
            <button
              data-testid="error-detail-toggle"
              aria-expanded={showDetail}
              onClick={() => setShowDetail(!showDetail)}
              className="text-xs text-muted-foreground hover:underline"
            >
              {showDetail ? "Hide details" : "Show details"}
            </button>
          )}
          {showDetail && friendly.detail && (
            <pre data-testid="error-raw-detail" className="overflow-auto rounded bg-muted/50 p-2 text-xs font-mono text-muted-foreground">
              {displayDetail}
              {friendly.detail.length > truncateThreshold && !showMore && (
                <button onClick={() => setShowMore(true)} className="ml-1 text-[var(--chat-brand-accent)] hover:underline">
                  Show more
                </button>
              )}
            </pre>
          )}
          <div className="flex gap-2">
            {friendly.retriable && (
              <Button
                variant="outline"
                size="sm"
                data-testid="error-retry-btn"
                aria-label="Retry"
                onClick={onRetry}
                className="h-7 text-xs"
              >
                Retry
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
