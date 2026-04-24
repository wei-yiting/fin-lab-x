import type { ExtractedSources } from "@/models";
import { SourceLink } from "@/components/atoms/SourceLink";

export function Sources({ sources }: { sources: ExtractedSources }) {
  const safe = sources.filter((s) => /^https?:/.test(s.url));
  if (safe.length === 0) return null;
  return (
    <section data-testid="sources-block" className="mt-3 border-t border-white/[0.06] pt-2">
      <h4 className="mb-1 text-[10px] font-medium uppercase tracking-widest text-[var(--chat-fg-subtle)]">
        Sources
      </h4>
      <ul className="space-y-0.5">
        {safe.map((s) => (
          <SourceLink
            key={s.label}
            label={s.label}
            url={s.url}
            title={s.title}
            hostname={s.hostname}
          />
        ))}
      </ul>
    </section>
  );
}
