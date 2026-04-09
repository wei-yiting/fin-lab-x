import { Button } from "@/components/primitives/button"
import { Badge } from "@/components/primitives/badge"
import { Trash2 } from "lucide-react"

export function ChatHeader({ onClear, messagesEmpty }: {
  onClear: () => void
  messagesEmpty: boolean
}) {
  return (
    <header data-testid="chat-header" className="flex items-center justify-between border-b border-border px-4 py-3">
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold text-foreground">FinLab-X</h1>
        <Badge variant="outline" className="text-[10px] uppercase">v1</Badge>
      </div>
      <Button
        variant="ghost"
        size="sm"
        data-testid="composer-clear-btn"
        aria-label="Clear conversation"
        disabled={messagesEmpty}
        onClick={onClear}
        className="gap-1.5 text-xs text-muted-foreground"
      >
        <Trash2 className="h-3.5 w-3.5" />
        Clear
      </Button>
    </header>
  )
}
