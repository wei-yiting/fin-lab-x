import { forwardRef, useImperativeHandle, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Button } from "@/components/primitives/button";
import { Textarea } from "@/components/primitives/textarea";
import { Send, Square } from "lucide-react";
import type { ChatStatus } from "@/models";

export type ComposerHandle = { setValue: (v: string) => void; focus: () => void };

type Props = {
  sendMessage: (m: { text: string }) => void;
  stop: () => void;
  status: ChatStatus;
};

export const Composer = forwardRef<ComposerHandle, Props>(({ sendMessage, stop, status }, ref) => {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  useImperativeHandle(
    ref,
    () => ({
      setValue: (v: string) => flushSync(() => setText(v)),
      focus: () => textareaRef.current?.focus(),
    }),
    [],
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (status !== "ready") return;
    const trimmed = text.trim();
    if (!trimmed) return;
    sendMessage({ text: trimmed });
    setText("");
  };

  const isActive = status === "submitted" || status === "streaming";

  return (
    <div className="mx-auto w-full max-w-[52rem] px-4 pt-2 pb-4">
      <form
        data-testid="composer"
        onSubmit={handleSubmit}
        className="flex flex-col gap-1 rounded-xl border border-input bg-muted px-3.5 py-2"
      >
        <Textarea
          ref={textareaRef}
          data-testid="composer-textarea"
          aria-label="Message input"
          placeholder="Ask about markets, companies, or filings..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              handleSubmit(e as unknown as React.FormEvent);
            }
          }}
          className="min-h-[24px] resize-none border-0 bg-transparent px-0.5 py-1 shadow-none focus-visible:ring-0 dark:bg-transparent"
          rows={1}
        />
        <div className="flex items-center justify-end">
          {isActive ? (
            <Button
              type="button"
              variant="outline"
              size="icon"
              data-testid="composer-stop-btn"
              aria-label="Stop response"
              onClick={stop}
              className="size-8 shrink-0"
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
              className="size-8 shrink-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </form>
      <p className="mt-2 text-center text-[10px] text-[var(--chat-fg-subtler)]">
        AI-generated responses may be inaccurate. Please verify important information.
      </p>
    </div>
  );
});

Composer.displayName = "Composer";
