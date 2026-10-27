import { describe, test, expect } from "vitest";
import { en, zhTW } from "@/lib/copy";

type Shape = string | { [key: string]: Shape };

/** Leaves become their kind ("string" / "function") so values don't matter, only structure. */
function shapeOf(node: unknown): Shape {
  if (typeof node === "object" && node !== null) {
    return Object.fromEntries(Object.entries(node).map(([k, v]) => [k, shapeOf(v)]));
  }
  return typeof node;
}

function stringLeaves(node: unknown, path = ""): Array<[string, string]> {
  if (typeof node === "string") return [[path, node]];
  if (typeof node === "object" && node !== null) {
    return Object.entries(node).flatMap(([k, v]) => stringLeaves(v, path ? `${path}.${k}` : k));
  }
  return [];
}

const HAN = /\p{Script=Han}/u;

describe("UI copy dictionaries", () => {
  test("zh-TW has exactly the same keys and leaf kinds as en", () => {
    expect(shapeOf(zhTW)).toEqual(shapeOf(en));
  });

  test("no empty strings in either locale", () => {
    for (const [path, value] of [...stringLeaves(en), ...stringLeaves(zhTW)]) {
      expect(value.trim(), path).not.toBe("");
    }
  });

  test("interpolating entries keep their arguments in both locales", () => {
    expect(zhTW.reasoningChip.thoughtFor(12)).toContain("12");
    expect(zhTW.toolStatus.running("sec_filing_search")).toContain("sec_filing_search");
    expect(zhTW.reasoningChip.toggleAriaLabel("思考中…", true)).toContain("思考中…");
  });

  // The backend answers in Traditional Chinese iff the message contains a Han
  // character, so a zh-TW chip must contain one — and an English chip none.
  test("starter prompts are written in their locale's language", () => {
    for (const chip of Object.values(zhTW.emptyState.chips)) {
      expect(chip.prompt).toMatch(HAN);
    }
    for (const chip of Object.values(en.emptyState.chips)) {
      expect(chip.prompt).not.toMatch(HAN);
    }
  });
});
