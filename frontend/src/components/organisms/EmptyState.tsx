import { PromptChip } from "@/components/atoms/PromptChip";
import {
  BadgeDollarSign,
  Building2,
  GitCompare,
  Scale,
  ShieldAlert,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import type { Copy } from "@/lib/copy";
import { useLocale } from "@/lib/locale";

type ChipKey = keyof Copy["emptyState"]["chips"];
type GroupLabelKey = "everydayGroupLabel" | "analystGroupLabel";

// Plain-language questions first, research-grade ones second — the two
// audiences the demo is shown to.
const CHIP_GROUPS: ReadonlyArray<{
  labelKey: GroupLabelKey;
  chips: ReadonlyArray<{ key: ChipKey; icon: LucideIcon }>;
}> = [
  {
    labelKey: "everydayGroupLabel",
    chips: [
      { key: "priceToday", icon: TrendingUp },
      { key: "businessModel", icon: Building2 },
      { key: "valuationCheck", icon: BadgeDollarSign },
    ],
  },
  {
    labelKey: "analystGroupLabel",
    chips: [
      { key: "riskVsNews", icon: ShieldAlert },
      { key: "narrativeVsNumbers", icon: Scale },
      { key: "crossCompanyDisclosure", icon: GitCompare },
    ],
  },
];

export function EmptyState({ onPickPrompt }: { onPickPrompt: (text: string) => void }) {
  const { copy } = useLocale();
  let chipIndex = 0;
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
        <div className="mt-8 flex w-full max-w-5xl flex-col gap-6">
          {CHIP_GROUPS.map(({ labelKey, chips }) => (
            <section
              key={labelKey}
              aria-label={copy.emptyState[labelKey]}
              data-testid="prompt-chip-group"
            >
              <h3 className="mb-2.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {copy.emptyState[labelKey]}
              </h3>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                {chips.map(({ key, icon }) => {
                  const chip = copy.emptyState.chips[key];
                  const index = chipIndex++;
                  return (
                    <PromptChip
                      key={key}
                      icon={icon}
                      title={chip.title}
                      text={chip.prompt}
                      index={index}
                      onClick={() => onPickPrompt(chip.prompt)}
                    />
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
