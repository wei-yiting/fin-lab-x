/**
 * Citation resolution (see CONTEXT.md "Citation block").
 *
 * The model binds each `[N]` to an ID in a bottom reference definition; the
 * evidence behind that ID is never written by the model — it is joined, by
 * ID, against the tool results of the SAME assistant message, which already
 * reach the client as tool-part `output`. Nothing here needs a backend or
 * streaming-contract change (ADR-0024).
 *
 * - `http(s)://…` → a web link (news), shown as before
 * - `sec://…`     → one `sec_filing_search` evidence chunk, keyed by its `source`
 * - `sql://{toolCallId}` → one whole `company_fundamentals_query` result (status `ok` only)
 *
 * An ID that matches no tool result still resolves — with `evidence: null` —
 * so the UI can say so instead of silently dropping the citation.
 */

import type { ExtractedSources } from "@/models";

export const SEC_ID_PREFIX = "sec://";
export const SQL_ID_PREFIX = "sql://";

export type SourceKind = "web" | "sec" | "sql";

export function sourceKind(url: string): SourceKind {
  if (url.startsWith(SEC_ID_PREFIX)) return "sec";
  if (url.startsWith(SQL_ID_PREFIX)) return "sql";
  return "web";
}

export interface SecEvidence {
  title: string;
  subsection?: string;
  content: string;
  score?: number;
  fiscalYear?: number;
  fiscalYearEnd?: string;
}

/** A derived output column and the expression over raw columns it came from. */
export interface SqlDerivation {
  column: string;
  expression: string;
  inputs: string[];
}

export interface SqlEvidence {
  question?: string;
  columns: string[];
  rows: Record<string, unknown>[];
  truncated: boolean;
  derivations: SqlDerivation[];
}

export type Citation =
  | { kind: "web"; label: string; url: string; title?: string; hostname: string }
  | { kind: "sec"; label: string; id: string; evidence: SecEvidence | null }
  | { kind: "sql"; label: string; id: string; evidence: SqlEvidence | null };

type MessagePart = Record<string, unknown>;

function completedToolName(part: MessagePart): string | null {
  if (part.state !== "output-available") return null;
  if (typeof part.toolName === "string") return part.toolName;
  const type = part.type;
  if (typeof type === "string" && type.startsWith("tool-")) return type.slice(5);
  return null;
}

/** Tool output arrives as a JSON string on the wire but as an object in test
 *  fixtures — accept both. */
function parseOutput(output: unknown): Record<string, unknown> | null {
  let value = output;
  if (typeof value === "string") {
    try {
      value = JSON.parse(value);
    } catch {
      return null;
    }
  }
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

const isRecord = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === "object" && !Array.isArray(v);

const stringList = (v: unknown): string[] =>
  Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : [];

function collectSecEvidence(output: Record<string, unknown>, into: Map<string, SecEvidence>) {
  const fiscalYearEnd =
    typeof output.fiscal_year_end === "string" ? output.fiscal_year_end : undefined;
  const groups = Array.isArray(output.groups) ? output.groups : [];
  for (const group of groups) {
    if (!isRecord(group) || !Array.isArray(group.chunks)) continue;
    const fiscalYear =
      typeof group.fiscal_year === "number"
        ? group.fiscal_year
        : typeof output.fiscal_year === "number"
          ? output.fiscal_year
          : undefined;
    for (const chunk of group.chunks) {
      if (!isRecord(chunk)) continue;
      const { source, title, content } = chunk;
      if (typeof source !== "string" || typeof content !== "string") continue;
      if (into.has(source)) continue;
      into.set(source, {
        title: typeof title === "string" ? title : source,
        subsection: typeof chunk.subsection === "string" ? chunk.subsection : undefined,
        content,
        score: typeof chunk.score === "number" ? chunk.score : undefined,
        fiscalYear,
        fiscalYearEnd,
      });
    }
  }
}

function parseDerivations(value: unknown, columns: string[]): SqlDerivation[] {
  if (!Array.isArray(value)) return [];
  const known = new Set(columns);
  const out: SqlDerivation[] = [];
  for (const d of value) {
    if (!isRecord(d)) continue;
    const { column, expression } = d;
    if (typeof column !== "string" || typeof expression !== "string") continue;
    const inputs = stringList(d.inputs);
    // Substitution reads raw values from the rows by column name; a
    // derivation whose inputs were not selected cannot be shown faithfully.
    if (!known.has(column) || inputs.length === 0 || !inputs.every((c) => known.has(c))) continue;
    out.push({ column, expression, inputs });
  }
  return out;
}

function toSqlEvidence(output: Record<string, unknown>): SqlEvidence | null {
  if (output.status !== "ok") return null;
  const columns = stringList(output.columns);
  const rows = Array.isArray(output.rows) ? output.rows.filter(isRecord) : [];
  return {
    question: typeof output.question === "string" ? output.question : undefined,
    columns,
    rows,
    truncated: output.truncated === true,
    derivations: parseDerivations(output.derivations, columns),
  };
}

interface EvidenceRegistry {
  sec: Map<string, SecEvidence>;
  sql: Map<string, SqlEvidence>;
}

function buildRegistry(parts: ReadonlyArray<MessagePart>): EvidenceRegistry {
  const registry: EvidenceRegistry = { sec: new Map(), sql: new Map() };
  for (const part of parts) {
    const toolName = completedToolName(part);
    if (toolName !== "sec_filing_search" && toolName !== "company_fundamentals_query") continue;
    const output = parseOutput(part.output);
    if (!output) continue;
    if (toolName === "sec_filing_search") {
      collectSecEvidence(output, registry.sec);
    } else if (typeof part.toolCallId === "string") {
      // Keyed by the client-visible toolCallId so the ID the tool hands the
      // model (`citation_id`) and the one resolved here cannot drift apart.
      const evidence = toSqlEvidence(output);
      if (evidence) registry.sql.set(`${SQL_ID_PREFIX}${part.toolCallId}`, evidence);
    }
  }
  return registry;
}

export function resolveCitations(
  sources: ExtractedSources,
  parts: ReadonlyArray<MessagePart>,
): Citation[] {
  if (sources.length === 0) return [];
  const registry = buildRegistry(parts);
  return sources.map((s): Citation => {
    const kind = sourceKind(s.url);
    if (kind === "sec") {
      return { kind, label: s.label, id: s.url, evidence: registry.sec.get(s.url) ?? null };
    }
    if (kind === "sql") {
      return { kind, label: s.label, id: s.url, evidence: registry.sql.get(s.url) ?? null };
    }
    return { kind, label: s.label, url: s.url, title: s.title, hostname: s.hostname };
  });
}
