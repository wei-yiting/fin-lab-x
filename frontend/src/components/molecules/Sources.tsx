import type { Citation } from "@/lib/citations";
import { SourceLink } from "@/components/atoms/SourceLink";
import { CitationBlock } from "@/components/molecules/CitationBlock";
import { useLocale } from "@/lib/locale";

export interface CitationFocus {
  label: string;
  seq: number;
}

/**
 * The citation list under an answer, one entry per `[N]` in label order:
 * web sources stay external links, evidence sources (`sec://`, `sql://`)
 * are expandable citation blocks.
 */
export function Sources({
  citations,
  expanded = new Set(),
  onToggle = () => {},
  focus,
}: {
  citations: ReadonlyArray<Citation>;
  expanded?: ReadonlySet<string>;
  onToggle?: (label: string) => void;
  focus?: CitationFocus | null;
}) {
  const { copy } = useLocale();
  const shown = citations.filter((c) => c.kind !== "web" || /^https?:/.test(c.url));
  if (shown.length === 0) return null;
  return (
    <section data-testid="sources-block" className="mt-3 border-t border-white/[0.06] pt-2">
      <h4 className="mb-1 text-[10px] font-medium uppercase tracking-widest text-[var(--chat-fg-subtle)]">
        {copy.sources.heading}
      </h4>
      <ul className="space-y-0.5">
        {shown.map((c) =>
          c.kind === "web" ? (
            <SourceLink
              key={c.label}
              label={c.label}
              url={c.url}
              title={c.title}
              hostname={c.hostname}
            />
          ) : (
            <CitationBlock
              key={c.label}
              citation={c}
              expanded={expanded.has(c.label)}
              onToggle={() => onToggle(c.label)}
              focusSeq={focus?.label === c.label ? focus.seq : undefined}
            />
          ),
        )}
      </ul>
    </section>
  );
}
