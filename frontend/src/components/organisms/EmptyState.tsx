import { PromptChip } from "@/components/atoms/PromptChip";
import { Newspaper, DollarSign, BarChart3, FileText } from "lucide-react";
import { copy } from "@/lib/copy";

const CHIPS = [
  { icon: Newspaper, text: copy.emptyState.chips.nvdaNews },
  { icon: DollarSign, text: copy.emptyState.chips.aaplQuote },
  { icon: BarChart3, text: copy.emptyState.chips.compareFinancials },
  { icon: FileText, text: copy.emptyState.chips.msftLatest10K },
] as const;

export function EmptyState({ onPickPrompt }: { onPickPrompt: (text: string) => void }) {
  return (
    <div
      data-testid="empty-state"
      className="flex flex-1 flex-col items-center justify-center px-4 py-12"
    >
      <h2 className="text-[28px] font-bold tracking-tight text-foreground">
        {copy.emptyState.heading}
      </h2>
      <p className="mt-2 text-sm text-muted-foreground">{copy.emptyState.subtext}</p>
      <div className="mt-8 grid w-full max-w-md grid-cols-2 gap-2">
        {CHIPS.map((chip, i) => (
          <PromptChip
            key={i}
            icon={chip.icon}
            text={chip.text}
            index={i}
            onClick={() => onPickPrompt(chip.text)}
          />
        ))}
      </div>
    </div>
  );
}
