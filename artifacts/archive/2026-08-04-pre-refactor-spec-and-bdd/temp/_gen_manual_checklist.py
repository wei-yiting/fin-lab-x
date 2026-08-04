#!/usr/bin/env python3
"""Generate the manual verification HTML checklist.

Bug from previous run: raw <pre> content with newline literals broke JSON
parsing. This version builds Python objects → json.dumps (auto-escapes \\n)
→ inject into the template placeholders.
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEMPLATE = Path(os.path.expanduser("~/.claude/skills/bdd-e2e-loop/assets/manual-verification.html"))
OUT = ROOT / "artifacts/current/temp/manual-verification-round-manual-3.html"


def cmd(line: str) -> str:
    """Render a CLI command in the dark code block."""
    return f"<pre>{line}</pre>"


def helper(profile: str) -> str:
    return cmd(f"./scripts/manual-bdd-backend.sh {profile}")


def boot_block(profile: str) -> list[str]:
    """Two steps to flip backend profile cleanly."""
    return [
        f"In a backend terminal, stop any running backend (Ctrl+C) then start the <code>{profile}</code> profile:",
        helper(profile),
        "Frontend dev server should already be running at <code>http://localhost:5173/</code>. If not: " + cmd("pnpm --dir frontend run dev"),
        "Open <code>http://localhost:5173/</code> in a fresh tab.",
    ]


SCENARIOS = [
    # ────────── A. Things automation can't reach ──────────
    {
        "id": "S-rsn-04",
        "title": "S-rsn-04 — Long CJK reasoning sentence does not break layout",
        "type": "technical",
        "steps": boot_block("gemini-on") + [
            "Send the prompt: <code>請用繁體中文詳細推理:從第一性原理推導為什麼 Apple 的服務業務毛利率比硬體高,直接走完一段不要分點不要句點</code>",
            "While the reasoning indicator is streaming, watch for any visual breakage when the indicator text gets long.",
            "Check three things: (1) container stays single-line height (no vertical wrap); (2) long Chinese reasoning is hard-clipped at the right edge (NO <code>…</code> ellipsis); (3) the trailing dots cycler is still visible at the right edge of the line."
        ],
        "expected": "Indicator stays one line tall, Chinese text overflows are hard-clipped (no ellipsis), trailing dots cycler always visible. No vertical wrap, no layout shift, no text-cursor jumping."
    },
    {
        "id": "S-rsn-09c",
        "title": "S-rsn-09c — Abort during text streaming preserves partial text + STOPPED label",
        "type": "technical",
        "steps": boot_block("gemini-on") + [
            "Send a long-text prompt that minimises tool use: <code>Write a 400-word essay on the history of compound interest in everyday lending. Use full sentences and start writing immediately.</code>",
            "Wait until the assistant message body shows real essay text (sentences appearing one after another, NOT just a tool card or reasoning indicator). You're now in the text-streaming phase.",
            "Click the Stop button as text is streaming.",
            "Check: the partial essay text remains visible on the prior bubble. Does a STOPPED inline label appear at the end of the partial text?",
            "Then send a follow-up: <code>Continue the essay.</code> and confirm the prior bubble (with partial + STOPPED) coexists with the new bubble below."
        ],
        "expected": "Partial essay text survives the stop click. STOPPED inline label visible at the end of the partial text. After the follow-up turn streams, both bubbles coexist (prior with partial+STOPPED, new with full reply). This complements Gap #1: it's the case where there IS partial text to preserve."
    },
    {
        "id": "S-rsn-14",
        "title": "S-rsn-14 — Screen reader announces transitions, not every reasoning sentence",
        "type": "technical",
        "steps": boot_block("gemini-on") + [
            "macOS only: enable VoiceOver with <code>Cmd+F5</code>.",
            "Tab into the message input.",
            "Send the prompt: <code>What is Microsoft's current stock price?</code>",
            "Listen to the announcements during the turn.",
            "Check the announcement sequence — should be high-level only: \"Generating response\" → \"Calling yfinance_stock_quote\" → \"Tool yfinance_stock_quote completed\" → (final answer text gets read) → \"Response complete\".",
            "Confirm: reasoning sentences (each transient indicator update, e.g. \"prioritizing retrieval and comparison\") are NOT announced one by one.",
            "Disable VoiceOver with <code>Cmd+F5</code> when done."
        ],
        "expected": "Transition-level announcements only. Reasoning sentences are not read aloud one by one. ErrorBlock (if any) gets role=alert priority."
    },

    # ────────── B. 6-case provider × reasoning matrix UX feel ──────────
    {
        "id": "J-stream-01-A",
        "title": "J-stream-01.A — Gemini reasoning ON: streaming UX feel",
        "type": "technical",
        "steps": boot_block("gemini-on") + [
            "Send: <code>Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)</code>",
            "Watch the full lifecycle: 3-dot idle → reasoning text appearing → tool cards (sec_filing_get_section ×2) → final answer text streaming with cursor → done.",
            "Subjective check: does reasoning indicator feel readable? Does state transition feel smooth?",
            "Note any visual jank, wrong text, missing transitions."
        ],
        "expected": "Lifecycle plays through cleanly with reasoning text visible, tool cards appearing, final answer streaming. No console errors. Reasoning text reads natural (not garbage)."
    },
    {
        "id": "J-stream-01-B",
        "title": "J-stream-01.B — Gemini reasoning OFF: no reasoning indicator, post-tool idle text",
        "type": "technical",
        "steps": boot_block("gemini-off") + [
            "Send: <code>Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)</code>",
            "Watch the lifecycle. There should be NO reasoning text shown (because reasoning is off).",
            "BUT: in the gap between tool completion and the next phase, an idle text \"Synthesizing\" or \"Thinking\" should briefly appear in the indicator slot.",
            "Final answer streams to completion."
        ],
        "expected": "No reasoning text ever appears in the indicator. \"Synthesizing\" or \"Thinking\" idle text shows in post-tool gaps (D15). Final answer streams fine."
    },
    {
        "id": "J-stream-01-C",
        "title": "J-stream-01.C — Anthropic reasoning ON: extended thinking pause, then text",
        "type": "technical",
        "steps": boot_block("anthropic-on") + [
            "Send: <code>Pick a single industry that will be most disrupted by AI agents in 2027. Walk through your reasoning step by step, then state your conclusion in one sentence.</code>",
            "Anthropic's extended thinking takes ~15-25s of silent thinking BEFORE any text appears.",
            "During that silence, the reasoning indicator should be visible (with 3-dot idle, then any reasoning text Claude emits).",
            "After the thinking pause, text streams to completion.",
            "Note: by design Gap #2, no mid-text re-entry of indicator (no Option B re-entry — Anthropic interleaved beta not enabled)."
        ],
        "expected": "Indicator visible during the long thinking pause. Text answer eventually streams. No mid-text re-entry of indicator (this is current by-design state per Gap #2)."
    },
    {
        "id": "J-stream-01-D",
        "title": "J-stream-01.D — Anthropic reasoning OFF: short answer, no thinking pause",
        "type": "technical",
        "steps": boot_block("anthropic-off") + [
            "Send: <code>What is the typical fiscal year end for Apple, Microsoft, and Google?</code>",
            "Anthropic with reasoning off should answer quickly without the long thinking pause.",
            "No reasoning indicator text should show during the streaming phase."
        ],
        "expected": "Answer streams quickly with no extended pause. No reasoning text in the indicator."
    },
    {
        "id": "J-stream-01-E",
        "title": "J-stream-01.E — OpenAI gpt-5-mini reasoning ON: reasoning summaries appear",
        "type": "technical",
        "steps": boot_block("openai-on") + [
            "Send: <code>Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)</code>",
            "OpenAI gpt-5-mini with reasoning ON emits a short reasoning SUMMARY block before each text turn (different style from Gemini's full reasoning text).",
            "Watch for short summary-style reasoning text (e.g. \"Comparing fiscal years…\") in the indicator before each LLM call.",
            "Tool cards + final answer should all complete normally."
        ],
        "expected": "Short reasoning summary text appears in indicator before each LLM call. Multi-tool flow completes. No errors."
    },
    {
        "id": "J-stream-01-F",
        "title": "J-stream-01.F — OpenAI gpt-5-mini reasoning OFF",
        "type": "technical",
        "steps": boot_block("openai-off") + [
            "Send: <code>Summarize the latest 10-K of MSFT</code>",
            "Multi-tool flow runs without reasoning text shown.",
            "Final answer streams normally."
        ],
        "expected": "No reasoning text shown. Stream completes normally."
    },

    # ────────── C. Stop / abort journeys (real user flows) ──────────
    {
        "id": "Stop-A",
        "title": "Stop-A — Stop during pre-response idle (3-dot phase, before any SSE)",
        "type": "technical",
        "steps": boot_block("gemini-on") + [
            "Send the prompt: <code>Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)</code>",
            "Within ~500ms (while only the 3-dot idle is showing — BEFORE any reasoning text appears), click the Stop button.",
            "Note: this needs fast clicking. If you see reasoning text appear, you missed the window — refresh and retry."
        ],
        "expected": "Stream halts immediately. Per Gap #1 design: prior bubble may end up empty (no STOPPED label persists for pre-text aborts). Confirm what you actually see."
    },
    {
        "id": "Stop-B",
        "title": "Stop-B — Stop during reasoning streaming (indicator showing reasoning text)",
        "type": "technical",
        "steps": boot_block("gemini-on") + [
            "Send the prompt: <code>Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)</code>",
            "Wait until the reasoning indicator shows a real reasoning sentence (e.g. \"The goal is to isolate…\").",
            "Click Stop.",
            "Send a follow-up message: <code>What is Microsoft's stock ticker?</code>",
            "Confirm: prior bubble vs new bubble in the chat list."
        ],
        "expected": "Per Gap #1 (accepted by design): prior bubble is empty after the new turn arrives — STOPPED label / reasoning text don't persist. Two bubbles coexist regardless. Document if this matches the as-shipped behavior."
    },
    {
        "id": "Stop-C",
        "title": "Stop-C — Stop during tool execution (mid-tool-call)",
        "type": "technical",
        "steps": boot_block("gemini-on") + [
            "Send the prompt: <code>Get the latest stock quote for AAPL, MSFT, GOOGL, NVDA, AMD, and TSLA. Compare them.</code>",
            "Wait until you see one or more tool cards appear (yfinance_stock_quote running).",
            "Click Stop while a tool is mid-execution."
        ],
        "expected": "Stream halts. The currently running tool card should transition to an aborted state (visual signal — typically a different color or label)."
    },

    # ────────── D. Mid-stream error injection ──────────
    {
        "id": "Err-mid-stream",
        "title": "Err-mid-stream — FORCE_LLM_FAIL injects mid-stream provider error",
        "type": "technical",
        "steps": boot_block("force-llm-fail") + [
            "Send any prompt, e.g. <code>Hello</code>",
            "Backend will raise immediately — frontend should show an ErrorBlock instead of a normal answer.",
            "Confirm: error message is human-readable (not a stack trace), retry button or recovery path is reasonable."
        ],
        "expected": "ErrorBlock appears with friendly title (not raw stack). No half-rendered streaming UI left over. Composer is re-enabled for next message."
    },

    # ────────── E. Cleanup ──────────
    {
        "id": "Cleanup",
        "title": "Cleanup — restore default config",
        "type": "technical",
        "steps": [
            "When you're done with all the above, restore the default config (this just moves the .bak file back):",
            cmd("./scripts/manual-bdd-backend.sh restore"),
            "Verify clean: " + cmd("git status backend/agent_engine/agents/versions/v1_baseline/"),
            "Should report nothing to commit. Then you can stop the backend (Ctrl+C) and the frontend dev server."
        ],
        "expected": "git status reports v1_baseline.yaml is unchanged from main. Backend / frontend processes can be stopped."
    },
]


def main() -> None:
    if not TEMPLATE.exists():
        print(f"template not found: {TEMPLATE}", file=sys.stderr)
        sys.exit(1)
    template = TEMPLATE.read_text()
    scenarios_json = json.dumps(SCENARIOS, ensure_ascii=False, indent=2)
    # Both placeholders go inside JS source as literal expressions, so they
    # need json.dumps to produce valid JS literals. The previous bug:
    # __ROUND_PLACEHOLDER__ → "manual-3" (no quotes) → JS parsed as
    # `manual - 1`, ReferenceError, whole script died, cards never rendered.
    out = template.replace("__SCENARIOS_PLACEHOLDER__", scenarios_json).replace(
        "__ROUND_PLACEHOLDER__", json.dumps("manual-3")
    )
    OUT.write_text(out)
    print(f"wrote {OUT}  ({len(out)} chars, {len(SCENARIOS)} scenarios)")


if __name__ == "__main__":
    main()
