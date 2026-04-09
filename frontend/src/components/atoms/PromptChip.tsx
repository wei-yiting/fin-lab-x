import { Button } from "@/components/primitives/button"
import type { LucideIcon } from "lucide-react"

export function PromptChip({
  icon: Icon,
  text,
  index,
  onClick,
}: {
  icon: LucideIcon
  text: string
  index: number
  onClick: () => void
}) {
  return (
    <Button
      variant="outline"
      data-testid="prompt-chip"
      data-chip-index={index}
      aria-label={text}
      onClick={onClick}
      className="h-auto justify-start gap-2 whitespace-normal px-3 py-2 text-left text-sm"
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span>{text}</span>
    </Button>
  )
}
