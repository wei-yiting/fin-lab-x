import { unified } from "unified";
import remarkParse from "remark-parse";
import { visit } from "unist-util-visit";
import type { Root } from "mdast";
import type { SourceRef, ExtractedSources } from "@/models";

const ALLOWED_PROTOCOLS = new Set(["http:", "https:"]);

const parser = unified().use(remarkParse);

// LLM sometimes outputs "- [1]: URL" (bulleted ref def) — normalize to "[1]: URL"
const BULLET_REF_RE = /^[-*]\s+(\[\d+\]:)/gm;

// Headers like "來源：" adjacent to definitions block CommonMark from recognising them
const SOURCE_HEADER_RE = /^\*{0,2}(?:References|來源|參考來源|參考資料)\*{0,2}\s*[：:]?\s*$/gm;

// Fallback for non-standard [N] URL (no colon) that CommonMark doesn't recognise
const FALLBACK_RE = /^\[(\d+)\]\s+(\S+?)(?:\s+"([^"]*)")?\s*$/gm;

function addSource(
  seen: Map<string, SourceRef>,
  label: string,
  rawUrl: string,
  rawTitle: string | null | undefined,
) {
  if (!/^\d+$/.test(label)) return;
  if (seen.has(label)) return;

  let parsed: URL;
  try {
    parsed = new URL(rawUrl);
  } catch {
    return;
  }

  if (!ALLOWED_PROTOCOLS.has(parsed.protocol)) return;
  if (!parsed.hostname.includes(".")) return;

  seen.set(label, {
    label,
    url: rawUrl,
    title: rawTitle ?? undefined,
    hostname: parsed.hostname,
  });
}

/**
 * Normalize text so `remark-parse` recognises every `[N]: url "title"`
 * line as a CommonMark definition node. The LLM does not consistently
 * emit spec-compliant definitions — each of the three regex rewrites
 * below corrects one observed failure mode seen in real responses:
 *
 * 1. Bullet-prefixed definitions (`- [1]: URL`). CommonMark requires
 *    definitions to start at column 0; a leading `- ` turns them into
 *    a list item whose body happens to contain a definition, so both
 *    `remark-parse` and the AssistantMessage strip regex miss it.
 *    Removing the bullet prefix pulls them back to column 0.
 *
 * 2. Source headers (`來源：`, `References`, `參考資料`). These headers
 *    attach to the first definition as a paragraph, which again blocks
 *    CommonMark from recognising the definition. Wiping the header line
 *    is safe: the Sources block supplies its own heading.
 *
 * 3. Missing blank line before the first `[N]:` line. Without the blank
 *    separator CommonMark keeps the definition inside the preceding
 *    paragraph. Injecting `\n\n` is a no-op when one already exists
 *    because the negative lookahead `[^\n]` only matches non-newline
 *    characters before the definition.
 */
export function normalizeRefDefs(text: string): string {
  return text
    .replace(BULLET_REF_RE, "$1")
    .replace(SOURCE_HEADER_RE, "")
    .replace(/([^\n])\n(\[(\d+)\]:\s)/gm, "$1\n\n$2");
}

/**
 * Remark plugin that rewrites `[N]`-style linkReference nodes whose identifier
 * matches a known source label into hast `<a>` elements carrying the source URL
 * plus `data-citation` / `data-source-label` attributes. This is the only
 * channel by which `Markdown.tsx` decides "this is a citation" — inline links
 * whose rendered text happens to equal "1" / "2" / ... are not affected.
 */
export function markdownSourcesPlugin(sources: ExtractedSources) {
  const labelMap = new Map(sources.map((s) => [s.label, s]));
  // Unified plugin signature: attacher returns a transformer.
  return function attacher() {
    return function transformer(tree: Root) {
      visit(tree, "linkReference", (node) => {
        const src = labelMap.get(node.identifier);
        if (!src) return;
        const data = (node.data ??= {});
        data.hName = "a";
        data.hProperties = {
          ...((data.hProperties as Record<string, unknown>) ?? {}),
          "data-citation": "true",
          "data-source-label": src.label,
          href: src.url,
        };
      });
    };
  };
}

export function extractSources(text: string): ExtractedSources {
  try {
    const seen = new Map<string, SourceRef>();
    const cleaned = normalizeRefDefs(text);

    // Step 1 — primary extraction via CommonMark AST. Using the same
    // parser ReactMarkdown uses internally guarantees that a definition
    // we surface in the Sources block is identical to the one
    // ReactMarkdown hides from the rendered body.
    const tree = parser.parse(cleaned) as Root;
    for (const node of tree.children) {
      if (node.type !== "definition") continue;
      addSource(seen, node.identifier, node.url, node.title);
    }

    // Step 2 — fallback for `[N] URL` with no colon. This is non-standard
    // CommonMark so `remark-parse` ignores it, but the LLM emits it
    // often enough that we cannot drop these citations.
    let match: RegExpExecArray | null;
    while ((match = FALLBACK_RE.exec(cleaned)) !== null) {
      const [, label, rawUrl, rawTitle] = match;
      addSource(seen, label, rawUrl, rawTitle);
    }

    // Step 3 — stable numeric order. Labels are numeric-only (enforced
    // by addSource); sorting keeps [1]/[2]/[3] in reading order across
    // re-renders so RefSup jump-links land where the reader expects.
    return Array.from(seen.values()).sort((a, b) => parseInt(a.label) - parseInt(b.label));
  } catch {
    return [];
  }
}
