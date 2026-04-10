import type { SourceRef, ExtractedSources } from '@/models'

const ALLOWED_PROTOCOLS = new Set(['http:', 'https:'])

const REF_DEF_RE = /^\[(\d+)\]:?\s+(\S+?)(?:\s+"([^"]*)")?\s*$/gm

export function extractSources(text: string): ExtractedSources {
  try {
    const seen = new Map<string, SourceRef>()
    let match: RegExpExecArray | null

    while ((match = REF_DEF_RE.exec(text)) !== null) {
      const [, label, rawUrl, rawTitle] = match

      if (seen.has(label)) continue

      let parsed: URL
      try {
        parsed = new URL(rawUrl)
      } catch {
        continue
      }

      if (!ALLOWED_PROTOCOLS.has(parsed.protocol)) continue
      if (!parsed.hostname.includes('.')) continue

      const title = rawTitle ?? undefined

      seen.set(label, {
        label,
        url: rawUrl,
        title,
        hostname: parsed.hostname,
      })
    }

    return Array.from(seen.values()).sort(
      (a, b) => parseInt(a.label) - parseInt(b.label),
    )
  } catch {
    return []
  }
}
