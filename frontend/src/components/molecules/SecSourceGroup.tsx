import { ExternalLink } from "lucide-react";
import type { SourceRef } from "@/models";

/**
 * One aggregated Sources entry for all citations of the same
 * (ticker, fiscal year, item) group: locator title, EDGAR filing link,
 * and an expandable excerpt per cited chunk. All display data comes from
 * the tool result metadata carried on `SourceRef.sec`.
 */
export function SecSourceGroup({ entries }: { entries: ReadonlyArray<SourceRef> }) {
  const first = entries[0]?.sec;
  if (!first) return null;

  const groupTitle = `${first.ticker} FY${first.fiscalYear} 10-K · ${first.item}`;
  const edgarUrl = first.edgarUrl;

  return (
    <li data-testid="sec-source-group" className="text-xs">
      <div className="flex items-baseline gap-1.5">
        <span className="shrink-0 text-[10px] font-medium text-[oklch(0.55_0.10_255)]">
          {entries.map((e) => (
            <span key={e.label} id={`src-${e.label}`}>
              [{e.label}]
            </span>
          ))}
        </span>
        <span className="text-[oklch(0.55_0.04_252)] truncate">{groupTitle}</span>
        {edgarUrl && /^https?:/.test(edgarUrl) && (
          <a
            href={edgarUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-baseline gap-1 shrink-0 text-[oklch(0.55_0.04_252)] hover:text-[oklch(0.70_0.08_252)] hover:underline"
          >
            EDGAR
            <ExternalLink className="h-2.5 w-2.5 shrink-0 translate-y-px" />
          </a>
        )}
      </div>
      <div className="mt-0.5 space-y-0.5 pl-4">
        {entries.map((e) =>
          e.sec ? (
            <details key={e.label} data-testid="sec-source-excerpt">
              <summary className="cursor-pointer text-[10px] text-[var(--chat-fg-subtle)]">
                [{e.label}] {e.sec.subsection ?? e.sec.item}
              </summary>
              <p className="mt-0.5 whitespace-pre-wrap text-[11px] leading-relaxed text-[oklch(0.55_0.04_252)]">
                {e.sec.excerpt}
              </p>
            </details>
          ) : null,
        )}
      </div>
    </li>
  );
}
