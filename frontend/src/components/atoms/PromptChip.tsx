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
      aria-label={`${title}: ${text}`}
      onClick={onClick}
      className="h-auto items-start justify-start gap-3 whitespace-normal px-4 py-3.5 text-left"
    >
      <Icon className="mt-0.5 h-[18px] w-[18px] shrink-0" />
      <span className="flex min-w-0 flex-col gap-1.5">
        <span className="text-[15px] font-semibold text-foreground">{title}</span>
        <span className="text-sm font-normal leading-relaxed text-muted-foreground">{text}</span>
      </span>
    </Button>
  );
}
