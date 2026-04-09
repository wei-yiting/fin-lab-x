import { PromptChip } from "@/components/atoms/PromptChip"
import { Newspaper, DollarSign, BarChart3, FileText } from "lucide-react"

const CHIPS = [
  { icon: Newspaper, text: "Latest market news for NVDA" },
  { icon: DollarSign, text: "Show AAPL stock quote" },
  { icon: BarChart3, text: "Compare NVDA and AMD financials" },
  { icon: FileText, text: "Summarize the latest 10-K of MSFT" },
] as const

export function EmptyState({ onPickPrompt }: { onPickPrompt: (text: string) => void }) {
  return (
    <div data-testid="empty-state" className="flex flex-1 flex-col items-center justify-center px-4 py-12">
      <h2 className="text-[28px] font-bold tracking-tight text-foreground">
        What would you like to know?
      </h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Ask about markets, companies, financials, or filings.
      </p>
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
  )
}
