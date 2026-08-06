/**
 * SEC citation resolution (ADR-0008, extract-on-finish extension).
 *
 * `sec_filing_search` tool results carry numbered evidence chunks with
 * stable citation IDs (`sec://{filing}/{item}#{chunk_index}`). The model's
 * reference definitions map `[N]` to those IDs; everything the user sees
 * (title, excerpt, EDGAR link) is resolved mechanically from the tool
 * result parts of the SAME assistant message. IDs that don't exist in any
 * tool result are dropped — a fabricated ID never renders as a source.
 */

import type { ExtractedSources, SecSourceInfo, SourceRef } from "@/models";

export const SEC_ID_PREFIX = "sec://";

type MessagePart = Record<string, unknown>;

export type SecEvidenceRegistry = ReadonlyMap<string, SecSourceInfo>;

function isSecSearchResultPart(part: MessagePart): boolean {
  const type = part.type;
  if (typeof type !== "string" || part.state !== "output-available") return false;
  if (type === "tool-sec_filing_search") return true;
  return (type === "dynamic-tool" || type === "tool") && part.toolName === "sec_filing_search";
}

/** Tool output arrives as a JSON string on the production wire but as an
 *  object in test fixtures — accept both. */
function parseOutput(output: unknown): Record<string, unknown> | null {
  if (typeof output === "string") {
    try {
      const parsed: unknown = JSON.parse(output);
      return parsed && typeof parsed === "object" ? (parsed as Record<string, unknown>) : null;
    } catch {
      return null;
    }
  }
  if (output && typeof output === "object") return output as Record<string, unknown>;
  return null;
}

export function buildSecEvidenceRegistry(parts: ReadonlyArray<MessagePart>): SecEvidenceRegistry {
  const registry = new Map<string, SecSourceInfo>();
  for (const part of parts) {
    if (!isSecSearchResultPart(part)) continue;
    const output = parseOutput(part.output);
    const groups = output?.groups;
    if (!Array.isArray(groups)) continue;
    for (const group of groups as Array<Record<string, unknown>>) {
      if (!group || typeof group !== "object") continue;
      const { ticker, fiscal_year: fiscalYear, item, edgar_url: edgarUrl } = group;
      const chunks = group.chunks;
      if (
        typeof ticker !== "string" ||
        typeof fiscalYear !== "number" ||
        typeof item !== "string" ||
        !Array.isArray(chunks)
      ) {
        continue;
      }
      for (const chunk of chunks as Array<Record<string, unknown>>) {
        if (!chunk || typeof chunk !== "object") continue;
        const { source, title, content, subsection } = chunk;
        if (
          typeof source !== "string" ||
          typeof title !== "string" ||
          typeof content !== "string"
        ) {
          continue;
        }
        registry.set(source, {
          id: source,
          ticker,
          fiscalYear,
          item,
          subsection: typeof subsection === "string" ? subsection : undefined,
          title,
          excerpt: content,
          edgarUrl: typeof edgarUrl === "string" ? edgarUrl : undefined,
        });
      }
    }
  }
  return registry;
}

/**
 * Replace extracted sec:// refs with registry-resolved entries (metadata
 * from the tool result wins over anything the model wrote); drop refs whose
 * ID is unknown. Non-SEC sources pass through untouched.
 */
export function resolveSecSources(
  sources: ExtractedSources,
  registry: SecEvidenceRegistry,
): ExtractedSources {
  const resolved: SourceRef[] = [];
  for (const source of sources) {
    if (!source.url.startsWith(SEC_ID_PREFIX)) {
      resolved.push(source);
      continue;
    }
    const info = registry.get(source.url);
    if (!info) continue;
    resolved.push({
      label: source.label,
      url: info.edgarUrl ?? `#src-${source.label}`,
      title: info.title,
      hostname: "www.sec.gov",
      sec: info,
    });
  }
  return resolved;
}

/** Aggregation key: one Sources entry per (ticker, fiscal year, item). */
export function secGroupKey(info: SecSourceInfo): string {
  return `${info.ticker}|${info.fiscalYear}|${info.item}`;
}
