import { Badge } from "@/components/primitives/badge";

export function ChatHeader({
  onClear,
  messagesEmpty,
}: {
  onClear: () => void;
  messagesEmpty: boolean;
}) {
  return (
    <header
      data-testid="chat-header"
      className="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-center justify-between px-4 py-3 [&_*]:pointer-events-auto"
    >
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold text-foreground">FinLab-X</h1>
        <Badge variant="outline" className="text-[10px] uppercase">
          v1
        </Badge>
      </div>
      <button
        data-testid="composer-clear-btn"
        aria-label="Clear conversation"
        disabled={messagesEmpty}
        onClick={onClear}
        className="rounded-md border border-[oklch(0.7282_0.1610_27.12/0.2)] bg-[oklch(0.7282_0.1610_27.12/0.08)] px-3.5 py-1.5 text-xs font-medium text-[oklch(0.7282_0.1610_27.12)] transition-all hover:border-[oklch(0.7282_0.1610_27.12/0.35)] hover:bg-[oklch(0.7282_0.1610_27.12/0.14)] disabled:cursor-not-allowed disabled:opacity-40"
      >
        Clear conversation
      </button>
    </header>
  );
}
