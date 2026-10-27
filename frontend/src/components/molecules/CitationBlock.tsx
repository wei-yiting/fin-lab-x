import { useEffect, useRef } from "react";
import { AlertCircle, ChevronRight, Database, FileText } from "lucide-react";
import { useLocale } from "@/lib/locale";
import type { Citation, SecEvidence, SqlEvidence } from "@/lib/citations";
import {
  formatValue,
  formulaText,
  identityColumns,
  rowLabel,
  substitutedText,
} from "@/lib/sql-derivation";
import { cn } from "@/lib/utils";

type EvidenceCitation = Exclude<Citation, { kind: "web" }>;

const LABEL_CLASS = "shrink-0 w-4 text-[10px] font-medium text-[oklch(0.55_0.10_255)]";
const META_CLASS = "text-[11px] text-[var(--chat-fg-subtle)]";

const FLASH_KEYFRAMES: Keyframe[] = [
  { backgroundColor: "oklch(0.55 0.10 255 / 0.18)" },
  { backgroundColor: "transparent" },
];

/**
 * One `sec://` / `sql://` entry of the citation list: a header row that
 * toggles the evidence open. `focusSeq` changes every time the inline `[N]`
 * marker asks for this entry — the block scrolls into view and flashes.
 */
export function CitationBlock({
  citation,
  expanded,
  onToggle,
  focusSeq,
}: {
  citation: EvidenceCitation;
  expanded: boolean;
  onToggle: () => void;
  focusSeq?: number;
}) {
  const { copy } = useLocale();
  const ref = useRef<HTMLLIElement>(null);

  useEffect(() => {
    if (focusSeq === undefined) return;
    const el = ref.current;
    el?.scrollIntoView?.({ block: "nearest", behavior: "smooth" });
    el?.animate?.(FLASH_KEYFRAMES, { duration: 1200, easing: "ease-out" });
  }, [focusSeq]);

  const common = {
    ref,
    "data-testid": "citation-block",
    "data-source-label": citation.label,
    "data-citation-kind": citation.kind,
    id: `src-${citation.label}`,
    className: "rounded",
  };

  if (citation.evidence === null) {
    return (
      <li {...common} data-resolved="false">
        <div className="flex items-baseline gap-1.5 py-0.5 text-xs">
          <span className={LABEL_CLASS}>[{citation.label}]</span>
          <AlertCircle className="h-3 w-3 shrink-0 translate-y-0.5 text-amber-500" aria-hidden />
          <span className="text-[var(--chat-fg-subtle)]">{copy.citations.unresolved}</span>
        </div>
      </li>
    );
  }

  const Icon = citation.kind === "sec" ? FileText : Database;
  const title =
    citation.kind === "sec"
      ? citation.evidence.title
      : (citation.evidence.question ?? copy.citations.sqlFallbackTitle);

  return (
    <li {...common} data-resolved="true">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className="flex w-full items-baseline gap-1.5 py-0.5 text-left text-xs text-[oklch(0.55_0.04_252)] hover:text-[oklch(0.70_0.08_252)]"
      >
        <span className={LABEL_CLASS}>[{citation.label}]</span>
        <ChevronRight
          className={cn(
            "h-3 w-3 shrink-0 translate-y-0.5 transition-transform",
            expanded && "rotate-90",
          )}
          aria-hidden
        />
        <Icon className="h-3 w-3 shrink-0 translate-y-0.5" aria-hidden />
        <span className="min-w-0">{title}</span>
      </button>
      {expanded && (
        <div data-testid="citation-body" className="mb-2 ml-[22px] mt-1 space-y-1.5 text-xs">
          {citation.kind === "sec" ? (
            <SecBody evidence={citation.evidence} />
          ) : (
            <SqlBody evidence={citation.evidence} />
          )}
        </div>
      )}
    </li>
  );
}

function SecBody({ evidence }: { evidence: SecEvidence }) {
  const { copy } = useLocale();
  const meta = [
    evidence.fiscalYear !== undefined
      ? copy.citations.secFiscalYear(evidence.fiscalYear, evidence.fiscalYearEnd)
      : null,
    "sec_filing_search",
    evidence.score !== undefined ? copy.citations.relevance(evidence.score) : null,
  ].filter(Boolean);
  return (
    <>
      <p className={META_CLASS}>{meta.join(" · ")}</p>
      <blockquote className="max-h-48 overflow-y-auto whitespace-pre-wrap rounded border border-white/[0.06] bg-muted/30 p-2 leading-relaxed text-[var(--chat-fg-secondary)]">
        {evidence.content}
      </blockquote>
    </>
  );
}

function SqlBody({ evidence }: { evidence: SqlEvidence }) {
  const { copy } = useLocale();
  const identity = identityColumns(evidence);
  return (
    <>
      <p className={META_CLASS}>
        {copy.citations.provenanceLabel}: {copy.citations.provenance}
        {evidence.tables.length > 0 &&
          ` · ${copy.citations.tablesLabel}: ${evidence.tables.join(", ")}`}
      </p>
      {evidence.derivations.length > 0 && (
        <div>
          <p className={META_CLASS}>{copy.citations.formulaLabel}</p>
          {evidence.derivations.map((d) => (
            <p key={d.column} className="font-mono text-[11px] text-[var(--chat-fg-secondary)]">
              {formulaText(d)}
            </p>
          ))}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse font-mono text-[11px] text-[var(--chat-fg-secondary)]">
          <thead>
            <tr>
              {evidence.columns.map((c) => (
                <th
                  key={c}
                  className="border-b border-white/[0.08] px-2 py-1 text-right font-normal text-[var(--chat-fg-subtle)] first:text-left"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {evidence.rows.map((row, i) => (
              <tr key={i}>
                {evidence.columns.map((c) => (
                  <td
                    key={c}
                    className="border-b border-white/[0.04] px-2 py-1 text-right first:text-left"
                  >
                    {formatValue(c, row[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {evidence.truncated && (
        <p className={META_CLASS}>{copy.citations.truncated(evidence.rows.length)}</p>
      )}
      {evidence.derivations.length > 0 && (
        <div data-testid="citation-substitution">
          <p className={META_CLASS}>{copy.citations.substitutionLabel}</p>
          {evidence.rows.map((row, i) =>
            evidence.derivations.map((d) => {
              const label = rowLabel(row, identity);
              return (
                <p
                  key={`${i}-${d.column}`}
                  className="font-mono text-[11px] text-[var(--chat-fg-secondary)]"
                >
                  {label ? `${label}: ` : ""}
                  {substitutedText(d, row)}
                </p>
              );
            }),
          )}
        </div>
      )}
    </>
  );
}
