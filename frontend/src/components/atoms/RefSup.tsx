import { useCitationJump } from "@/lib/citation-jump";
import { useLocale } from "@/lib/locale";
import type { SourceKind } from "@/lib/citations";

const MARKER_CLASS =
  "text-[oklch(0.55_0.10_255)] hover:text-[oklch(0.65_0.14_255)] hover:underline text-[10px] font-medium";

/**
 * Inline `[N]` marker. A web source opens its page; an evidence source
 * (`sec://`, `sql://`) has no page to open, so it reveals its citation block
 * in the list below the answer instead.
 */
export function RefSup({
  label,
  href,
  kind = "web",
}: {
  label: string;
  href: string;
  kind?: SourceKind;
}) {
  const jump = useCitationJump();
  const { copy } = useLocale();
  return (
    <sup data-testid="ref-sup" data-ref-label={label}>
      {kind === "web" ? (
        <a href={href} target="_blank" rel="noopener noreferrer" className={MARKER_CLASS}>
          [{label}]
        </a>
      ) : (
        <button
          type="button"
          onClick={() => jump(label)}
          aria-label={copy.citations.jumpAriaLabel(label)}
          className={`${MARKER_CLASS} cursor-pointer`}
        >
          [{label}]
        </button>
      )}
    </sup>
  );
}
