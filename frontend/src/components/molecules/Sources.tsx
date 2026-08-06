import type { ExtractedSources, SourceRef } from "@/models";
import { SourceLink } from "@/components/atoms/SourceLink";
import { SecSourceGroup } from "@/components/molecules/SecSourceGroup";
import { secGroupKey } from "@/lib/sec-citations";

/** Group resolved SEC citations by (ticker, fiscal year, item), preserving
 *  first-appearance order of the groups and label order within each. */
function groupSecSources(
  secSources: ReadonlyArray<SourceRef>,
): ReadonlyArray<ReadonlyArray<SourceRef>> {
  const groups = new Map<string, SourceRef[]>();
  for (const source of secSources) {
    if (!source.sec) continue;
    const key = secGroupKey(source.sec);
    const bucket = groups.get(key);
    if (bucket) bucket.push(source);
    else groups.set(key, [source]);
  }
  return Array.from(groups.values());
}

export function Sources({ sources }: { sources: ExtractedSources }) {
  const webSources = sources.filter((s) => !s.sec && /^https?:/.test(s.url));
  const secGroups = groupSecSources(sources.filter((s) => s.sec));
  if (webSources.length === 0 && secGroups.length === 0) return null;
  return (
    <section data-testid="sources-block" className="mt-3 border-t border-white/[0.06] pt-2">
      <h4 className="mb-1 text-[10px] font-medium uppercase tracking-widest text-[var(--chat-fg-subtle)]">
        Sources
      </h4>
      <ul className="space-y-0.5">
        {webSources.map((s) => (
          <SourceLink
            key={s.label}
            label={s.label}
            url={s.url}
            title={s.title}
            hostname={s.hostname}
          />
        ))}
        {secGroups.map((entries) => (
          <SecSourceGroup key={entries[0].label} entries={entries} />
        ))}
      </ul>
    </section>
  );
}
