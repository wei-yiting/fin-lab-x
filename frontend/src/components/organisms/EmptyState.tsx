import { PromptChip } from "@/components/atoms/PromptChip";
import { ShieldAlert, Scale, GitCompare, TrendingDown } from "lucide-react";
import { copy } from "@/lib/copy";

const CHIPS = [
  { icon: ShieldAlert, ...copy.emptyState.chips.riskVsNews },
  { icon: Scale, ...copy.emptyState.chips.narrativeVsNumbers },
  { icon: GitCompare, ...copy.emptyState.chips.crossCompanyDisclosure },
  { icon: TrendingDown, ...copy.emptyState.chips.bearCaseAudit },
] as const;

export function EmptyState({ onPickPrompt }: { onPickPrompt: (text: string) => void }) {
  return (
    <div data-testid="empty-state" className="flex min-h-0 flex-1 flex-col overflow-y-auto">
      {/* m-auto (not justify-center) keeps the top reachable when content overflows on short viewports */}
      <div className="m-auto flex w-full flex-col items-center px-4 pb-8 pt-14 sm:py-12">
        <h2 className="text-center text-[28px] font-bold tracking-tight text-foreground">
          {copy.emptyState.heading}
        </h2>
        <p className="mt-2 max-w-xl text-center text-sm text-muted-foreground">
          {copy.emptyState.subtext}
        </p>
        <div className="mt-8 grid w-full max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
          {CHIPS.map((chip, i) => (
            <PromptChip
              key={i}
              icon={chip.icon}
              title={chip.title}
              text={chip.prompt}
              index={i}
              onClick={() => onPickPrompt(chip.prompt)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
