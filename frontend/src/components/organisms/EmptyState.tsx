import { PromptChip } from "@/components/atoms/PromptChip";
import { ShieldAlert, Scale, GitCompare, TrendingDown, type LucideIcon } from "lucide-react";
import type { Copy } from "@/lib/copy";
import { useLocale } from "@/lib/locale";

type ChipKey = keyof Copy["emptyState"]["chips"];

const CHIPS: ReadonlyArray<{ key: ChipKey; icon: LucideIcon }> = [
  { key: "riskVsNews", icon: ShieldAlert },
  { key: "narrativeVsNumbers", icon: Scale },
  { key: "crossCompanyDisclosure", icon: GitCompare },
  { key: "bearCaseAudit", icon: TrendingDown },
];

export function EmptyState({ onPickPrompt }: { onPickPrompt: (text: string) => void }) {
  const { copy } = useLocale();
  return (
    <div data-testid="empty-state" className="flex min-h-0 flex-1 flex-col overflow-y-auto">
      {/* m-auto (not justify-center) keeps the top reachable when content overflows on short viewports */}
      <div className="m-auto flex w-full flex-col items-center px-4 pb-8 pt-14 sm:py-12">
        <h2 className="text-center text-[28px] font-bold tracking-tight text-foreground">
          {copy.emptyState.heading}
        </h2>
        <p className="mt-2 max-w-xl text-center text-[15px] text-muted-foreground">
          {copy.emptyState.subtext}
        </p>
        <div className="mt-8 grid w-full max-w-4xl grid-cols-1 gap-3 md:grid-cols-2">
          {CHIPS.map(({ key, icon }, i) => {
            const chip = copy.emptyState.chips[key];
            return (
              <PromptChip
                key={key}
                icon={icon}
                title={chip.title}
                text={chip.prompt}
                index={i}
                onClick={() => onPickPrompt(chip.prompt)}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
