import { Button } from "@/components/primitives/button";
import type { LucideIcon } from "lucide-react";

export function PromptChip({
  icon: Icon,
  title,
  text,
  index,
  onClick,
}: {
  icon: LucideIcon;
  title: string;
  text: string;
  index: number;
  onClick: () => void;
}) {
  return (
    <Button
      variant="outline"
      data-testid="prompt-chip"
      data-chip-index={index}
      aria-label={`${title}：${text}`}
      onClick={onClick}
      className="h-auto items-start justify-start gap-2 whitespace-normal px-3 py-2.5 text-left text-sm"
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <span className="flex min-w-0 flex-col gap-1">
        <span className="font-medium text-foreground">{title}</span>
        <span className="line-clamp-3 text-xs font-normal text-muted-foreground">{text}</span>
      </span>
    </Button>
  );
}
