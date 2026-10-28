/**
 * Display helpers for a company_fundamentals_query citation block: value formatting by
 * column-name convention, and a derivation's formula with each row's raw
 * values substituted in.
 *
 * Column conventions come from the fundamentals store: `*_usd` columns are
 * dollar amounts and `*_pct` columns are already scaled to percent (the
 * views compute `… * 100`), so neither needs type metadata from the tool.
 */

import type { SqlDerivation, SqlEvidence } from "@/lib/citations";

const IDENTIFIER_RE = /[A-Za-z_][A-Za-z0-9_]*/g;

const OPERATOR_GLYPHS: Record<string, string> = { "/": "÷", "*": "×" };

function abbreviate(abs: number): string {
  if (abs >= 1e12) return `${(abs / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(abs / 1e6).toFixed(2)}M`;
  return abs.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

export function formatValue(column: string, value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value !== "number") return String(value);
  if (/_pct$/i.test(column)) return `${value.toFixed(1)}%`;
  if (/_usd$/i.test(column)) {
    return `${value < 0 ? "-" : ""}$${abbreviate(Math.abs(value))}`;
  }
  // Integers (fiscal years, quarters, counts) print as-is — a thousands
  // separator would turn 2024 into "2,024".
  if (Number.isInteger(value) && Math.abs(value) < 1e6) return String(value);
  return `${value < 0 ? "-" : ""}${abbreviate(Math.abs(value))}`;
}

/** Rewrite an expression for reading: `a / b * 100` → `a ÷ b × 100`. */
function prettifyOperators(expression: string): string {
  return expression.replace(/\s*([/*])\s*/g, (_, op: string) => ` ${OPERATOR_GLYPHS[op]} `);
}

export function formulaText(d: SqlDerivation): string {
  return `${d.column} = ${prettifyOperators(d.expression)}`;
}

export function substitutedText(d: SqlDerivation, row: Record<string, unknown>): string {
  const inputs = new Set(d.inputs);
  const substituted = d.expression.replace(IDENTIFIER_RE, (name) =>
    inputs.has(name) ? formatValue(name, row[name]) : name,
  );
  return `${formatValue(d.column, row[d.column])} = ${prettifyOperators(substituted)}`;
}

/**
 * Columns that identify a row (ticker, fiscal year, period end …): every
 * column that is neither a derived metric nor one of its inputs.
 */
export function identityColumns(evidence: SqlEvidence): string[] {
  const used = new Set<string>();
  for (const d of evidence.derivations) {
    used.add(d.column);
    d.inputs.forEach((c) => used.add(c));
  }
  return evidence.columns.filter((c) => !used.has(c));
}

export function rowLabel(row: Record<string, unknown>, columns: string[]): string {
  return columns
    .map((c) => row[c])
    .filter((v) => v !== null && v !== undefined && v !== "")
    .map(String)
    .join(" · ");
}
