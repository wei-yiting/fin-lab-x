import { unified } from 'unified'
import remarkParse from 'remark-parse'
import { visit } from 'unist-util-visit'
import type { Root } from 'mdast'
import type { SourceRef, ExtractedSources } from '@/models'

const ALLOWED_PROTOCOLS = new Set(['http:', 'https:'])

const parser = unified().use(remarkParse)

// LLM sometimes outputs "- [1]: URL" (bulleted ref def) — normalize to "[1]: URL"
const BULLET_REF_RE = /^[-*]\s+(\[\d+\]:)/gm

// Headers like "來源：" adjacent to definitions block CommonMark from recognising them
const SOURCE_HEADER_RE = /^\*{0,2}(?:References|來源|參考來源|參考資料)\*{0,2}\s*[：:]?\s*$/gm

// Fallback for non-standard [N] URL (no colon) that CommonMark doesn't recognise
const FALLBACK_RE = /^\[(\d+)\]\s+(\S+?)(?:\s+"([^"]*)")?\s*$/gm

function addSource(seen: Map<string, SourceRef>, label: string, rawUrl: string, rawTitle: string | null | undefined) {
  if (!/^\d+$/.test(label)) return
  if (seen.has(label)) return

  let parsed: URL
  try {
    parsed = new URL(rawUrl)
  } catch {
    return
  }

  if (!ALLOWED_PROTOCOLS.has(parsed.protocol)) return
  if (!parsed.hostname.includes('.')) return

  seen.set(label, {
    label,
    url: rawUrl,
    title: rawTitle ?? undefined,
    hostname: parsed.hostname,
  })
}

/**
 * Normalize text so that reference definitions are in standard CommonMark form.
 * - Strips bullet prefixes: "- [1]: URL" → "[1]: URL"
 * - Strips source headers: "來源：", "References", etc.
 * - Ensures a blank line before the first [N]: so CommonMark treats them as definitions
 */
export function normalizeRefDefs(text: string): string {
  return text
    .replace(BULLET_REF_RE, '$1')
    .replace(SOURCE_HEADER_RE, '')
    // Ensure blank line before first ref def so CommonMark doesn't merge it with preceding paragraph
    .replace(/([^\n])\n(\[(\d+)\]:\s)/gm, '$1\n\n$2')
}

/**
 * Remark plugin that rewrites `[N]`-style linkReference nodes whose identifier
 * matches a known source label into hast `<a>` elements carrying the source URL
 * plus `data-citation` / `data-source-label` attributes. This is the only
 * channel by which `Markdown.tsx` decides "this is a citation" — inline links
 * whose rendered text happens to equal "1" / "2" / ... are not affected.
 */
export function markdownSourcesPlugin(sources: ExtractedSources) {
  const labelMap = new Map(sources.map((s) => [s.label, s]))
  // Unified plugin signature: attacher returns a transformer.
  return function attacher() {
    return function transformer(tree: Root) {
      visit(tree, 'linkReference', (node) => {
        const src = labelMap.get(node.identifier)
        if (!src) return
        const data = (node.data ??= {})
        data.hName = 'a'
        data.hProperties = {
          ...((data.hProperties as Record<string, unknown>) ?? {}),
          'data-citation': 'true',
          'data-source-label': src.label,
          href: src.url,
        }
      })
    }
  }
}

export function extractSources(text: string): ExtractedSources {
  try {
    const seen = new Map<string, SourceRef>()
    const cleaned = normalizeRefDefs(text)

    // Primary: use the same CommonMark parser as ReactMarkdown
    const tree = parser.parse(cleaned) as Root
    for (const node of tree.children) {
      if (node.type !== 'definition') continue
      addSource(seen, node.identifier, node.url, node.title)
    }

    // Fallback: non-standard [N] URL (no colon) that remark-parse skips
    let match: RegExpExecArray | null
    while ((match = FALLBACK_RE.exec(cleaned)) !== null) {
      const [, label, rawUrl, rawTitle] = match
      addSource(seen, label, rawUrl, rawTitle)
    }

    return Array.from(seen.values()).sort(
      (a, b) => parseInt(a.label) - parseInt(b.label),
    )
  } catch {
    return []
  }
}
