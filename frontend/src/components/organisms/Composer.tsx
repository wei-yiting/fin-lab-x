import { forwardRef, useImperativeHandle, useState } from "react"
import { flushSync } from "react-dom"
import { Button } from "@/components/primitives/button"
import { Textarea } from "@/components/primitives/textarea"
import { Send, Square } from "lucide-react"
import type { ChatStatus } from "@/models"

export type ComposerHandle = { setValue: (v: string) => void }

type Props = {
  sendMessage: (m: { text: string }) => void
  stop: () => void
  status: ChatStatus
}

export const Composer = forwardRef<ComposerHandle, Props>(
  ({ sendMessage, stop, status }, ref) => {
    const [text, setText] = useState("")
    useImperativeHandle(ref, () => ({ setValue: (v: string) => flushSync(() => setText(v)) }), [])

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault()
      if (status !== "ready") return
      const trimmed = text.trim()
      if (!trimmed) return
      sendMessage({ text: trimmed })
      setText("")
    }

    const isActive = status === "submitted" || status === "streaming"

    return (
      <form data-testid="composer" onSubmit={handleSubmit} className="border-t border-border px-4 py-3">
        <div className="flex items-end gap-2">
          <Textarea
            data-testid="composer-textarea"
            aria-label="Message input"
            placeholder="Ask about markets, companies, or filings..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault()
                handleSubmit(e as unknown as React.FormEvent)
              }
            }}
            className="min-h-[44px] resize-none"
            rows={1}
          />
          {isActive ? (
            <Button
              type="button"
              variant="outline"
              size="icon"
              data-testid="composer-stop-btn"
              aria-label="Stop response"
              onClick={stop}
              className="shrink-0"
            >
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon"
              data-testid="composer-send-btn"
              aria-label="Send message"
              disabled={!text.trim()}
              className="shrink-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
        <p className="mt-2 text-center text-[10px] text-[var(--chat-fg-subtler)]">
          AI-generated responses may be inaccurate. Please verify important information.
        </p>
      </form>
    )
  },
)

Composer.displayName = "Composer"
