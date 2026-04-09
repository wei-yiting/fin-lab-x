import type { ExtractedSources } from "@/models"
import { SourceLink } from "./SourceLink"

export function Sources({ sources }: { sources: ExtractedSources }) {
  const safe = sources.filter(s => /^https?:/.test(s.url))
  if (safe.length === 0) return null
  return (
    <section data-testid="sources-block" className="mt-4 border-t border-border pt-3">
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--chat-fg-subtle)]">Sources</h4>
      <ul className="space-y-1">
        {safe.map(s => (
          <SourceLink key={s.label} label={s.label} url={s.url} title={s.title} hostname={s.hostname} />
        ))}
      </ul>
    </section>
  )
}
