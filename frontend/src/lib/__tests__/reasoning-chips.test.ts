import { describe, test, expect } from "vitest";
import {
  isReasoningPart,
  isToolPart,
  isRenderablePart,
  turnHasRenderableContent,
  chipStateOf,
  isChipExpanded,
  chipHeaderLabel,
  chipKey,
} from "@/lib/reasoning-chips";

/**
 * Owner of the part-shape enumeration. `useDeadAirPlaceholder` consumes these
 * predicates and keeps one representative case per window rather than
 * re-enumerating shapes behind fake timers.
 */

describe("isReasoningPart", () => {
  test.each([
    ["reasoning-start shape (no delta yet)", { type: "reasoning", text: "", state: "streaming" }],
    ["streaming reasoning", { type: "reasoning", text: "…", state: "streaming" }],
    ["completed reasoning", { type: "reasoning", text: "r", state: "done" }],
  ])("%s → true", (_label, part) => {
    expect(isReasoningPart(part)).toBe(true);
  });

  test.each([
    ["text", { type: "text", text: "hi" }],
    ["tool", { type: "tool-get_section" }],
    ["step boundary", { type: "step-start" }],
    ["absent type", {}],
    ["non-string type", { type: 7 }],
  ])("%s → false", (_label, part) => {
    expect(isReasoningPart(part)).toBe(false);
  });
});

describe("isToolPart", () => {
  test.each([
    ["static tool part", { type: "tool-get_section" }],
    ["dynamic tool part", { type: "dynamic-tool" }],
  ])("%s → true", (_label, part) => {
    expect(isToolPart(part)).toBe(true);
  });

  test.each([
    // AssistantMessage's own predicate additionally matches a bare "tool";
    // this module delegates to the SDK guard, which does not.
    ['plain "tool"', { type: "tool" }],
    ["reasoning", { type: "reasoning" }],
    ["absent type", {}],
    ["non-string type", { type: 42 }],
  ])("%s → false", (_label, part) => {
    expect(isToolPart(part)).toBe(false);
  });
});

describe("isRenderablePart", () => {
  test.each([
    ["reasoning that has carried a delta", { type: "reasoning", text: "…", state: "streaming" }],
    ["completed reasoning with content", { type: "reasoning", text: "r", state: "done" }],
    ["static tool part", { type: "tool-get_section", state: "input-available" }],
    ["dynamic tool part", { type: "dynamic-tool", state: "output-available" }],
    ["text with visible prose", { type: "text", text: "answer…" }],
    // Whitespace around real prose still paints the prose.
    ["text with prose plus a ref def", { type: "text", text: "NVDA [1]\n\n[1]: https://a.com" }],
  ])("%s → true", (_label, part) => {
    expect(isRenderablePart(part)).toBe(true);
  });

  test.each([
    // Zero-delta reasoning never paints (zero-delta suppression).
    ["reasoning-start before its first delta", { type: "reasoning", text: "", state: "streaming" }],
    ["reasoning closed without any delta", { type: "reasoning", text: "", state: "done" }],
    ["empty text", { type: "text", text: "" }],
    ["whitespace-only text", { type: "text", text: "  \n " }],
    // These normalize to nothing in AssistantMessage's displayText, so the
    // screen shows nothing new — the dead-air window must not end here.
    ["column-zero reference definition only", { type: "text", text: "[1]: https://example.com" }],
    [
      "three-space-indented reference definition only",
      { type: "text", text: "   [1]: https://example.com" },
    ],
    ["Chinese source header only", { type: "text", text: "來源：" }],
    ["English source header only", { type: "text", text: "**References**" }],
    ["step boundary", { type: "step-start" }],
    ["unknown part type", { type: "data-tool-progress" }],
    ["absent type", {}],
  ])("%s → false", (_label, part) => {
    expect(isRenderablePart(part)).toBe(false);
  });
});

describe("turnHasRenderableContent", () => {
  const msg = (parts: Array<Record<string, unknown>>) => ({
    id: "a1",
    role: "assistant",
    parts,
  });

  test("no parts yet → false", () => {
    expect(turnHasRenderableContent(msg([]))).toBe(false);
  });

  test("only invisible parts → false", () => {
    expect(
      turnHasRenderableContent(
        msg([
          { type: "step-start" },
          { type: "reasoning", text: "", state: "streaming" },
          { type: "text", text: "  " },
        ]),
      ),
    ).toBe(false);
  });

  test("one renderable part among invisible ones → true", () => {
    expect(
      turnHasRenderableContent(
        msg([{ type: "step-start" }, { type: "reasoning", text: "…", state: "streaming" }]),
      ),
    ).toBe(true);
  });

  test("trailing invisible part does not un-render the turn", () => {
    expect(
      turnHasRenderableContent(
        msg([
          { type: "tool-x", toolCallId: "tc-1", state: "output-available" },
          { type: "reasoning", text: "", state: "streaming" },
        ]),
      ),
    ).toBe(true);
  });
});

// Chip derivations — the header/state contract `ReasoningChip` renders from.
// Kept here (not behind a component render) so the abort-vs-finish rule and
// the override precedence are pinned as pure functions.
describe("chipStateOf — abort detection from part shape", () => {
  test("state=streaming while the chat is active → streaming", () => {
    expect(chipStateOf({ type: "reasoning", text: "…", state: "streaming" }, true)).toBe(
      "streaming",
    );
  });

  test("state=streaming after the chat left the active pair → aborted (no reasoning-end)", () => {
    expect(chipStateOf({ type: "reasoning", text: "…", state: "streaming" }, false)).toBe(
      "aborted",
    );
  });

  test("state=done → done regardless of chat activity", () => {
    const part = { type: "reasoning", text: "…", state: "done" };
    expect(chipStateOf(part, true)).toBe("done");
    expect(chipStateOf(part, false)).toBe("done");
  });
});

describe("isChipExpanded — tail-only derivation with user override", () => {
  test("no override: only a streaming chip is expanded", () => {
    expect(isChipExpanded("streaming", undefined)).toBe(true);
    expect(isChipExpanded("done", undefined)).toBe(false);
    expect(isChipExpanded("aborted", undefined)).toBe(false);
  });

  test("override beats the derivation in both directions", () => {
    expect(isChipExpanded("streaming", false)).toBe(false);
    expect(isChipExpanded("done", true)).toBe(true);
  });
});

describe("chipHeaderLabel", () => {
  test("streaming: Thinking…, degraded to Still working… on stall", () => {
    expect(chipHeaderLabel("streaming", 0, false)).toBe("Thinking…");
    expect(chipHeaderLabel("streaming", 0, true)).toBe("Still working…");
  });

  test("done / aborted carry the measured seconds; stall has no effect", () => {
    expect(chipHeaderLabel("done", 7, true)).toBe("Thought for 7s");
    expect(chipHeaderLabel("aborted", 3, false)).toBe("Stopped — thought for 3s");
  });
});

describe("chipKey", () => {
  test("scopes the part index by message id so cross-turn id reuse never collides", () => {
    expect(chipKey("m1", 0)).toBe("m1:0");
    expect(chipKey("m1", 0)).not.toBe(chipKey("m2", 0));
  });
});
