"""One-shot candidate generation for the sec_retrieval_ab dataset.

Passage-first (and ~10 intent-first) generation with the sentence-index
technique: each Item's text is pre-split into numbered sentences, the model
returns sentence indices (never verbatim text), and span/snippet strings are
reconstructed from the original text — exact-substring correctness holds by
construction.

Model: OpenAI ``gpt-5.6-sol`` (frontier tier; see the scenario README for
the selection record). Every accepted candidate carries the model id and
``system_fingerprint``.

Stages (both run by default; ``--emit-only`` reuses candidates.json):
1. generate  -> curation/candidates.json (plans + accepted candidates)
2. emit      -> ../dataset.csv (draft), curation/review.csv, curation/review.md

Usage:
    uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.generate_candidates \
        [--limit N] [--emit-only]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.evals.scenarios.sec_retrieval_ab.curation.ingest_tickers import (
    TICKER_GRID,
)
from backend.evals.scenarios.sec_retrieval_ab.curation.validate_dataset import (
    Row,
    _corpus_occurrences,
    _token_len,
    load_filings,
    validate_rows,
)
from backend.ingestion.sec_text_pipeline.filing_models import (
    FlatItem,
    ParsedFiling,
    StructuredItem,
)

MODEL_ID = "gpt-5.6-sol"
PROMPT_VERSION = "v2"
CURATION_DIR = Path(__file__).parent
DATASET_CSV = CURATION_DIR.parent / "dataset.csv"
CANDIDATES_JSON = CURATION_DIR / "candidates.json"
REVIEW_CSV = CURATION_DIR / "review.csv"
REVIEW_MD = CURATION_DIR / "review.md"

MAX_APP_RETRIES = 3
MIN_ITEM_CHARS = 1_500  # items thinner than this have nothing worth asking
ALTERNATE_COUNT = 25  # over-generation on top of the 50 primaries (1.5x)

# Item-axis quotas: real-usage weighting, Item 8 excluded (fundamentals path).
ITEM_QUOTAS: dict[str, int] = {
    "1a": 15,
    "7": 15,
    "1": 9,
    "1c": 3,
    "7a": 3,
    # Item 3 carries only 1 row: in this grid only one filing has substantive
    # litigation text in the 10-K body (the rest point to the notes).
    "3": 1,
    "2": 1,
    "5": 1,
    "9a": 1,
}
FACTOID_QUOTA = 10
MULTI_QUOTA = 15  # remainder of the 50 rows is `passage`
INTENT_FIRST_QUOTA = 10

# Lay-user intents (style informed by the earlier zh metadata-filter
# experiment's question set — supply
# chain, customer concentration, export controls, competition, regulation —
# rewritten as English intents; never copied verbatim into the dataset).
INTENT_POOL = [
    "what supply chain risks does the company face",
    "how concentrated is the company's customer base",
    "how do export controls or trade restrictions affect the business",
    "what competitive pressures does the company highlight",
    "what regulatory or legal challenges could hurt the business",
    "how exposed is the company to China or other foreign markets",
    "what is driving the company's revenue growth",
    "what risks does the company see around AI",
    "how does the company manage interest rate or currency exposure",
    "what cybersecurity threats and governance does the company describe",
    "how dependent is the company on key suppliers or manufacturers",
    "what litigation is the company currently involved in",
]

_SENTENCE_RE = re.compile(r".+?(?:[.!?][\"')\]]*(?:\s+|$)|$)", re.DOTALL)
_ABBREV_END_RE = re.compile(
    r"\b(?:U\.S|U\.K|No|Inc|Corp|Ltd|Mr|Ms|Dr|vs|e\.g|i\.e|Jr|Sr|St)\.$"
)


def sentence_ranges(text: str) -> list[tuple[int, int]]:
    """Deterministic sentence segmentation as (start, end) char ranges.

    Splits after ./!/? (plus closing quotes/brackets); fragments shorter
    than 20 chars merge into the following sentence so abbreviation splits
    ("U.S.", "Inc.") don't produce unusable one-word sentences. Ranges index
    the ORIGINAL text, so any [start:end] slice is an exact substring.
    """
    raw_ranges: list[tuple[int, int]] = []
    for match in _SENTENCE_RE.finditer(text):
        if not match.group().strip():
            continue
        start, end = match.start(), match.end()
        # keep trailing whitespace out of the sentence
        while end > start and text[end - 1].isspace():
            end -= 1
        if raw_ranges and (raw_ranges[-1][1] - raw_ranges[-1][0]) < 20:
            raw_ranges[-1] = (raw_ranges[-1][0], end)
        else:
            raw_ranges.append((start, end))
    # Abbreviation guard: a "sentence" ending in a known abbreviation was cut
    # mid-sentence (e.g. "outside of the U.S. (31% ...") — merge it forward.
    ranges: list[tuple[int, int]] = []
    for start, end in raw_ranges:
        if ranges and _ABBREV_END_RE.search(text[ranges[-1][0] : ranges[-1][1]]):
            ranges[-1] = (ranges[-1][0], end)
        else:
            ranges.append((start, end))
    return ranges


@dataclass
class Plan:
    """One dataset row to generate: the sampled cell of every axis."""

    plan_id: str
    ticker: str
    item_keys: list[str]  # 1 for factoid/passage, 2 for cross-item multi
    query_type: str  # factoid | passage | multi_passage
    mode: str  # passage_first | intent_first
    intent: str | None = None
    role: str = "primary"  # primary | alternate | rejected


@dataclass
class Evidence:
    item_key: str
    header_path: str
    block_heading: str | None
    detection_source: str
    span: str
    snippet: str


@dataclass
class Candidate:
    candidate_id: str
    plan: Plan
    question: str
    curation_note: str
    evidences: list[Evidence]
    fiscal_year: int
    accession_number: str
    rejection_reason: str | None = None
    model: str = MODEL_ID
    system_fingerprint: str | None = None
    prompt_version: str = PROMPT_VERSION
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


# --------------------------------------------------------------------------
# sampling
# --------------------------------------------------------------------------


def _item_text_len(item: StructuredItem | FlatItem) -> int:
    if isinstance(item, FlatItem):
        return len(item.text)
    return len(item.prelude) + sum(len(b.text) for b in item.blocks)


# (ticker, item) pairs found unusable during generation — every candidate
# sentence failed corpus-uniqueness or snippet-length limits: JPM's Item 1
# is largely incorporated-by-reference boilerplate that repeats elsewhere;
# NEE's Item 7A sentences run past 200 chars. Swapped within the same
# grid cell per the sampling rule.
GENERATION_EXCLUSIONS: set[tuple[str, str]] = {("JPM", "1"), ("NEE", "7a")}


def _eligible_tickers(
    filings: dict[tuple[str, int], ParsedFiling], item_key: str
) -> list[str]:
    out = []
    for ticker in TICKER_GRID:
        if (ticker, item_key) in GENERATION_EXCLUSIONS:
            continue
        filing = _filing_for(filings, ticker)
        if filing is None:
            continue
        item = next(
            (i for i in filing.items if i.item.strip().lower() == item_key), None
        )
        if item is not None and _item_text_len(item) >= MIN_ITEM_CHARS:
            out.append(ticker)
    return out


def _filing_for(
    filings: dict[tuple[str, int], ParsedFiling], ticker: str
) -> ParsedFiling | None:
    matches = [f for (t, _), f in filings.items() if t == ticker]
    if not matches:
        return None
    return max(matches, key=lambda f: f.metadata.fiscal_year)


def build_plans(filings: dict[tuple[str, int], ParsedFiling]) -> list[Plan]:
    """Deterministic greedy allocation of the 50 primary rows + alternates."""
    per_ticker: Counter[str] = Counter()
    plans: list[Plan] = []

    def take(item_key: str, n: int) -> None:
        eligible = _eligible_tickers(filings, item_key)
        if not eligible:
            return
        for _ in range(n):
            eligible.sort(key=lambda t: (per_ticker[t], list(TICKER_GRID).index(t)))
            # Per-ticker cap of 4 rows (spec: 2-4 per ticker); fall back to
            # the least-loaded ticker only when every eligible one is full.
            under_cap = [t for t in eligible if per_ticker[t] < 4]
            ticker = (under_cap or eligible)[0]
            per_ticker[ticker] += 1
            plans.append(
                Plan(
                    plan_id=f"p{len(plans) + 1:02d}",
                    ticker=ticker,
                    item_keys=[item_key],
                    query_type="passage",  # assigned for real below
                    mode="passage_first",
                )
            )

    for item_key, quota in ITEM_QUOTAS.items():
        take(item_key, quota)
    # 49 item slots -> 50 rows: one extra row on the deepest bucket.
    take("1a", 1)

    # Query types: multi_passage prefers rich structured items (1a / 7 / 1),
    # factoid prefers narrow items, remainder is passage.
    def _multi_capable(plan: Plan) -> bool:
        filing = _filing_for(filings, plan.ticker)
        assert filing is not None
        item = next(
            i for i in filing.items if i.item.strip().lower() == plan.item_keys[0]
        )
        if isinstance(item, FlatItem):
            return _token_len(item.text) > 2 * 600 + 2 * 300
        return len(item.blocks) >= 2

    multi_assigned = 0
    for plan in plans:
        if multi_assigned >= MULTI_QUOTA:
            break
        if plan.item_keys[0] in ("1a", "7", "1") and _multi_capable(plan):
            plan.query_type = "multi_passage"
            multi_assigned += 1
    factoid_assigned = 0
    for plan in reversed(plans):  # narrow items sit at the tail of the list
        if factoid_assigned >= FACTOID_QUOTA:
            break
        if plan.query_type == "passage":
            plan.query_type = "factoid"
            factoid_assigned += 1

    # One cross-item multi_passage row (1a + 7) on a ticker having both rich.
    for plan in plans:
        if plan.query_type != "multi_passage" or plan.item_keys[0] != "1a":
            continue
        filing = _filing_for(filings, plan.ticker)
        assert filing is not None
        item7 = next((i for i in filing.items if i.item.strip().lower() == "7"), None)
        if item7 is not None and _item_text_len(item7) >= MIN_ITEM_CHARS:
            plan.item_keys = ["1a", "7"]
            break

    # intent-first: spread across distinct tickers, passage rows only.
    intent_idx = 0
    seen_tickers: set[str] = set()
    for plan in plans:
        if intent_idx >= min(INTENT_FIRST_QUOTA, len(INTENT_POOL)):
            break
        if plan.query_type == "passage" and plan.ticker not in seen_tickers:
            plan.mode = "intent_first"
            plan.intent = INTENT_POOL[intent_idx]
            intent_idx += 1
            seen_tickers.add(plan.ticker)

    # Alternates: re-sample the deepest buckets for over-generation.
    alt_sources = [p for p in plans if p.item_keys[0] in ("1a", "7", "1")]
    for i, source in enumerate(alt_sources[:ALTERNATE_COUNT]):
        plans.append(
            Plan(
                plan_id=f"a{i + 1:02d}",
                ticker=source.ticker,
                item_keys=list(source.item_keys),
                query_type=source.query_type,
                mode="passage_first",
                role="alternate",
            )
        )
    return plans


# --------------------------------------------------------------------------
# prompting
# --------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You generate evaluation rows for a dense-retrieval (RAG) system over SEC 10-K filings. [prompt {PROMPT_VERSION}]

The `query` you write simulates what an LLM orchestrator sends to a vector search tool — a concise English retrieval query (5-15 words; a question or a noun phrase), NOT what an end user types and NOT analyst prose. Examples of the style:
- "NVIDIA restrictions on shipping AI accelerators abroad"
- "Which customer concentration risks does the company disclose?"
- "drivers of gross margin change in the products segment"

You will receive one or two 10-K Items with numbered sentences, formatted as:
[unit U] heading: ...
  [U.S] sentence text

`item_key` is the bare lowercase item number exactly as shown in the section header, e.g. "1a" or "7" — never "Item 1A".

Select evidence by SENTENCE INDEX ONLY (never quote text):
- span = a contiguous sentence range inside ONE unit (span_start_sentence..span_end_sentence, inclusive)
- snippet_sentence = the single most load-bearing sentence inside that span

Hard rules:
1. factoid: span is exactly 1 sentence (snippet == span). passage: 2-6 contiguous sentences. multi_passage: 2 evidences in DIFFERENT units (or different items).
1b. multi_passage queries must express ONE information need whose complete answer requires both locations together (a causal chain, or the same event/topic elaborated in two places). NEVER join two independent facts with "and" — if the two best passages do not serve a single need, pick different passages that do.
1c. intent mode only: if nothing in the provided Item(s) substantively answers the intent, return an empty evidences array instead of forcing loosely related text.
2. The query must be answerable from the selected span alone, and NOT answerable from the other sentences shown.
3. Paraphrase: the query must not reuse any 3 consecutive words that appear in the evidence text. Use synonyms and different phrasing.
4. Pick company-specific, substantive sentences (concrete facts, named products, numbers, named risks). Never pick boilerplate that could appear in any 10-K.
5. The snippet sentence must be 50-200 characters long. The span must stay under roughly 250 tokens (~900 characters).
6. curation_note: one sentence — why this evidence was picked and what the row tests.
Respond only via the JSON schema."""

RESPONSE_SCHEMA: Any = {
    "type": "json_schema",
    "json_schema": {
        "name": "retrieval_eval_candidate",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "query": {"type": "string"},
                "curation_note": {"type": "string"},
                "evidences": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "item_key": {"type": "string"},
                            "unit_index": {"type": "integer"},
                            "span_start_sentence": {"type": "integer"},
                            "span_end_sentence": {"type": "integer"},
                            "snippet_sentence": {"type": "integer"},
                        },
                        "required": [
                            "item_key",
                            "unit_index",
                            "span_start_sentence",
                            "span_end_sentence",
                            "snippet_sentence",
                        ],
                    },
                },
            },
            "required": ["query", "curation_note", "evidences"],
        },
    },
}


@dataclass
class _UnitView:
    index: int
    heading: str | None
    text: str
    ranges: list[tuple[int, int]]


def build_unit_views(item: StructuredItem | FlatItem) -> list[_UnitView]:
    if isinstance(item, FlatItem):
        return [_UnitView(0, None, item.text, sentence_ranges(item.text))]
    views: list[_UnitView] = []
    if item.prelude:
        views.append(
            _UnitView(0, "(prelude)", item.prelude, sentence_ranges(item.prelude))
        )
    for block in item.blocks:
        views.append(
            _UnitView(
                len(views), block.heading, block.text, sentence_ranges(block.text)
            )
        )
    return views


def render_item(item_key: str, views: list[_UnitView]) -> str:
    lines = [f"### Item {item_key.upper()}"]
    for view in views:
        lines.append(f"[unit {view.index}] heading: {view.heading or '(none)'}")
        for s, (start, end) in enumerate(view.ranges):
            lines.append(f"  [{view.index}.{s}] {view.text[start:end]}")
    return "\n".join(lines)


def build_user_prompt(
    plan: Plan, items: dict[str, list[_UnitView]], used_snippets: list[str]
) -> str:
    n_evidence = 2 if plan.query_type == "multi_passage" else 1
    parts = [
        f"query_type: {plan.query_type} (return exactly {n_evidence} evidence"
        f"{'s' if n_evidence > 1 else ''})",
        f"company ticker: {plan.ticker}",
    ]
    if plan.mode == "intent_first":
        parts.append(
            "Underlying user intent (locate the best evidence answering it, "
            f"then write the orchestrator-style query): {plan.intent}"
        )
    if used_snippets:
        parts.append(
            "Sentences already used by other rows — do NOT select them again:\n"
            + "\n".join(f"- {s}" for s in used_snippets)
        )
    for item_key, views in items.items():
        parts.append(render_item(item_key, views))
    return "\n\n".join(parts)


# --------------------------------------------------------------------------
# programmatic filters (generation-time; the validator re-checks everything)
# --------------------------------------------------------------------------


def _normalize_item_key(raw: str) -> str:
    return raw.strip().lower().removeprefix("item").strip(" _.")


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def copies_trigram(query: str, evidence_text: str) -> bool:
    q = _tokens(query)
    ev = _tokens(evidence_text)
    ev_trigrams = {tuple(ev[i : i + 3]) for i in range(len(ev) - 2)}
    return any(tuple(q[i : i + 3]) in ev_trigrams for i in range(len(q) - 2))


def jaccard(query: str, snippet: str) -> float:
    a, b = set(_tokens(query)), set(_tokens(snippet))
    return len(a & b) / len(a | b) if a | b else 0.0


def check_candidate(
    plan: Plan,
    question: str,
    evidences: list[Evidence],
    filings: dict[tuple[str, int], ParsedFiling],
    used_snippets: set[str],
) -> list[str]:
    reasons: list[str] = []
    if re.search(r"[一-鿿]", question):
        reasons.append("query must be English")
    expected_n = 2 if plan.query_type == "multi_passage" else 1
    if len(evidences) != expected_n:
        reasons.append(f"expected {expected_n} evidences, got {len(evidences)}")
        return reasons
    for ev in evidences:
        first_word = re.match(r"[^\s]+", ev.span.lstrip())
        if first_word and first_word.group().isalpha() and first_word.group().islower():
            # An all-lowercase first word means the span starts mid-sentence —
            # usually a source block that is itself fragmented (mixed-case
            # proper nouns like "cbETH" stay legal).
            reasons.append("span starts mid-sentence; pick a different location")
        if _token_len(ev.span) > 300:
            reasons.append(f"span too long ({_token_len(ev.span)} tokens > 300)")
        if not 50 <= len(ev.snippet) <= 200:
            reasons.append(f"snippet length {len(ev.snippet)} outside 50-200 chars")
        if ev.snippet.lower() in used_snippets:
            reasons.append("snippet already used by another row")
        occurrences = _corpus_occurrences(filings, ev.snippet.lower())
        if occurrences != 1:
            reasons.append(
                f"snippet occurs {occurrences} times in corpus (must be unique)"
            )
        if copies_trigram(question, ev.span):
            reasons.append("query copies a 3-gram from the evidence span")
        if jaccard(question, ev.snippet) > 0.5:
            reasons.append("query/snippet lexical overlap > 0.5 Jaccard")
        if plan.query_type == "factoid" and ev.span != ev.snippet:
            reasons.append("factoid span must equal its snippet")
    if plan.query_type == "multi_passage":
        a, b = evidences
        if a.item_key == b.item_key:
            if a.detection_source != "flat" and a.block_heading == b.block_heading:
                reasons.append("multi_passage evidences share one block")
            if a.detection_source == "flat":
                gap = _flat_gap_tokens(plan, a, b, filings)
                if gap is not None and gap < 600:
                    reasons.append(
                        f"flat-item spans only {gap} tokens apart (need >= 600)"
                    )
    return reasons


def _flat_gap_tokens(
    plan: Plan,
    a: Evidence,
    b: Evidence,
    filings: dict[tuple[str, int], ParsedFiling],
) -> int | None:
    filing = _filing_for(filings, plan.ticker)
    if filing is None:
        return None
    item = next((i for i in filing.items if i.item.strip().lower() == a.item_key), None)
    if not isinstance(item, FlatItem):
        return None
    text_lower = item.text.lower()
    pos_a, pos_b = text_lower.find(a.span.lower()), text_lower.find(b.span.lower())
    if pos_a < 0 or pos_b < 0:
        return None
    (first_pos, first_span), (second_pos, _) = sorted(
        [(pos_a, a.span), (pos_b, b.span)]
    )
    gap_start = first_pos + len(first_span)
    if second_pos <= gap_start:
        return 0
    return _token_len(item.text[gap_start:second_pos])


# --------------------------------------------------------------------------
# generation loop
# --------------------------------------------------------------------------


def generate(limit: int | None) -> list[Candidate]:
    from openai import (
        OpenAI,
        RateLimitError,
    )  # lazy: emit-only runs must not need the key

    client = OpenAI(timeout=600, max_retries=2)
    filings = load_filings()
    plans = build_plans(filings)
    if limit is not None:
        plans = plans[:limit]

    # Resume: keep candidates already on disk (a rate-limit crash must not
    # burn the finished ones) and skip their plans.
    candidates: list[Candidate] = _load_candidates() if CANDIDATES_JSON.exists() else []
    done_ids = {c.candidate_id for c in candidates}
    if done_ids:
        print(f"resuming: {len(done_ids)} candidates already on disk")
        plans = [p for p in plans if p.plan_id not in done_ids]
    used_snippets: set[str] = {
        ev.snippet.lower() for c in candidates for ev in c.evidences
    }
    # Snippets from human/agent-rejected candidates: seeded into the used set
    # so regeneration cannot pick the same rejected sentence again.
    rejected_path = CURATION_DIR / "rejected_snippets.json"
    if rejected_path.exists():
        used_snippets |= {s.lower() for s in json.loads(rejected_path.read_text())}
    used_by_item: dict[tuple[str, str], list[str]] = {}
    for c in candidates:
        for ev in c.evidences:
            used_by_item.setdefault((c.plan.ticker, ev.item_key), []).append(ev.snippet)
    state_lock = threading.Lock()

    def _flush() -> None:
        CANDIDATES_JSON.write_text(
            json.dumps([asdict(c) for c in candidates], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def run_plan(plan: Plan) -> Candidate | None:
        filing = _filing_for(filings, plan.ticker)
        assert filing is not None
        meta = filing.metadata
        items: dict[str, list[_UnitView]] = {}
        detection: dict[str, str] = {}
        for key in plan.item_keys:
            item = next(i for i in filing.items if i.item.strip().lower() == key)
            items[key] = build_unit_views(item)
            detection[key] = (
                item.detection_source if isinstance(item, StructuredItem) else "flat"
            )
        titles = {
            key: next(i.title for i in filing.items if i.item.strip().lower() == key)
            for key in plan.item_keys
        }
        with state_lock:
            snapshot = [
                s
                for key in plan.item_keys
                for s in used_by_item.get((plan.ticker, key), [])
            ]

        messages: list[Any] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(plan, items, snapshot),
            },
        ]

        accepted: Candidate | None = None
        for attempt in range(1 + MAX_APP_RETRIES):
            for backoff in range(8):
                try:
                    response = client.chat.completions.create(
                        model=MODEL_ID,
                        messages=messages,
                        response_format=RESPONSE_SCHEMA,
                    )
                    break
                except RateLimitError:
                    wait = min(60, 10 * (backoff + 1))
                    print(f"[429]  {plan.plan_id}: waiting {wait}s", flush=True)
                    time.sleep(wait)
            else:
                print(f"[DROP] {plan.plan_id} (rate limit exhausted)", flush=True)
                return None
            content = response.choices[0].message.content
            if content is None:
                raise ValueError(f"empty completion for plan {plan.plan_id}")
            payload = json.loads(content)
            if plan.mode == "intent_first" and not payload["evidences"]:
                # Model reports the Item has no evidence for this intent:
                # fall back to passage-first on the same cell.
                plan.mode = "passage_first"
                plan.intent = None
                print(
                    f"[FALLBACK] {plan.plan_id}: intent unanswerable, "
                    "switching to passage_first",
                    flush=True,
                )
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_user_prompt(plan, items, snapshot),
                    },
                ]
                continue
            evidences: list[Evidence] = []
            index_errors: list[str] = []
            for ev in payload["evidences"]:
                key = _normalize_item_key(ev["item_key"])
                views = items.get(key)
                if views is None:
                    index_errors.append(f"unknown item_key {ev['item_key']!r}")
                    continue
                unit = next((v for v in views if v.index == ev["unit_index"]), None)
                if unit is None:
                    index_errors.append(f"unknown unit_index {ev['unit_index']}")
                    continue
                s0, s1, sk = (
                    ev["span_start_sentence"],
                    ev["span_end_sentence"],
                    ev["snippet_sentence"],
                )
                if not (0 <= s0 <= s1 < len(unit.ranges) and s0 <= sk <= s1):
                    index_errors.append(
                        f"sentence indices out of range: {s0}..{s1} snippet {sk} "
                        f"(unit has {len(unit.ranges)})"
                    )
                    continue
                span = unit.text[unit.ranges[s0][0] : unit.ranges[s1][1]]
                snippet = unit.text[unit.ranges[sk][0] : unit.ranges[sk][1]]
                evidences.append(
                    Evidence(
                        item_key=key,
                        header_path=(
                            f"{meta.ticker} / {meta.fiscal_year} / "
                            f"Item {key.upper()}. {titles[key]}"
                        ),
                        block_heading=(
                            None if unit.heading == "(prelude)" else unit.heading
                        ),
                        detection_source=detection[key],
                        span=span,
                        snippet=snippet,
                    )
                )
            with state_lock:
                reasons = index_errors + check_candidate(
                    plan, payload["query"], evidences, filings, used_snippets
                )
            if not reasons:
                accepted = Candidate(
                    candidate_id=plan.plan_id,
                    plan=plan,
                    question=payload["query"],
                    curation_note=payload["curation_note"],
                    evidences=evidences,
                    fiscal_year=meta.fiscal_year,
                    accession_number=meta.accession_number,
                    system_fingerprint=response.system_fingerprint,
                )
                break
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous selection failed validation:\n"
                        + "\n".join(f"- {r}" for r in reasons)
                        + "\nPick different sentences and/or rephrase the "
                        "query, then respond again via the schema."
                    ),
                }
            )
            print(f"[retry {attempt + 1}] {plan.plan_id}: {reasons}", flush=True)

        if accepted is None:
            print(f"[DROP] {plan.plan_id} ({plan.ticker} {plan.item_keys})", flush=True)
            return None
        with state_lock:
            # Re-check uniqueness against rows accepted while this one was in
            # flight, then claim the snippets atomically.
            clash = any(
                ev.snippet.lower() in used_snippets for ev in accepted.evidences
            )
            if clash:
                print(f"[DROP] {plan.plan_id} (post-flight snippet clash)", flush=True)
                return None
            for ev in accepted.evidences:
                used_snippets.add(ev.snippet.lower())
                used_by_item.setdefault((plan.ticker, ev.item_key), []).append(
                    ev.snippet
                )
            candidates.append(accepted)
            _flush()
        print(
            f"[GEN]  {plan.plan_id} {plan.ticker} {'/'.join(plan.item_keys)} "
            f"{plan.query_type} ({plan.mode}, {plan.role})",
            flush=True,
        )
        return accepted

    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(run_plan, plans))
    candidates.sort(key=_role_order)
    _flush()
    print(f"\nwrote {len(candidates)} candidates -> {CANDIDATES_JSON}")
    return candidates


# --------------------------------------------------------------------------
# emit: dataset.csv (draft), review.csv, review.md
# --------------------------------------------------------------------------


_ROLE_RANK = {"primary": 0, "alternate": 1, "rejected": 2}


def _role_order(c: Candidate) -> tuple[int, int, str]:
    # Sort by slot number first (the digits in "p05"/"a05"), not the id
    # string — otherwise a promoted "aNN" (alphabetically before "pNN")
    # jumps to the front of its role group instead of sitting near the
    # slot it now fills.
    slot = int(re.match(r"^[a-z]+(\d+)$", c.candidate_id).group(1))
    return (_ROLE_RANK[c.plan.role], slot, c.candidate_id)


def _load_candidates() -> list[Candidate]:
    raw = json.loads(CANDIDATES_JSON.read_text(encoding="utf-8"))
    out = []
    for c in raw:
        plan = Plan(**c.pop("plan"))
        evidences = [Evidence(**e) for e in c.pop("evidences")]
        out.append(Candidate(plan=plan, evidences=evidences, **c))
    return out


def _dataset_row(c: Candidate) -> dict[str, str]:
    grid = TICKER_GRID[c.plan.ticker]

    def j(values: list[str] | list[str | None]) -> str:
        return json.dumps(values, ensure_ascii=False)

    return {
        "question": c.question,
        "expected_header_paths": j([e.header_path for e in c.evidences]),
        "expected_tickers": j([c.plan.ticker]),
        "match_mode": "startswith",
        "answer_snippets": j([e.snippet for e in c.evidences]),
        "query_type": c.plan.query_type,
        "answer_spans": j([e.span for e in c.evidences]),
        "block_heading": j([e.block_heading for e in c.evidences]),
        "detection_source": j([e.detection_source for e in c.evidences]),
        "sector": grid["sector"],
        "market_cap_bucket": grid["cap"],
        "generation_mode": c.plan.mode,
        "user_intent": c.plan.intent or "",
        "curation_note": c.curation_note,
        "generated_by": c.model,
        "fiscal_year": str(c.fiscal_year),
        "accession_number": c.accession_number,
    }


def emit() -> int:
    candidates = sorted(_load_candidates(), key=_role_order)
    primaries = [c for c in candidates if c.plan.role == "primary"]
    if not primaries:
        print("no primary candidates to emit", file=sys.stderr)
        return 1

    fieldnames = list(_dataset_row(primaries[0]).keys())
    with DATASET_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in primaries:
            writer.writerow(_dataset_row(c))

    with REVIEW_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "candidate_id",
                "in_draft",
                "ticker",
                "items",
                "query_type",
                "generation_mode",
                "question",
                "snippet_preview",
                "approved",
                "reviewer_comment",
            ],
        )
        writer.writeheader()
        for c in candidates:
            writer.writerow(
                {
                    "candidate_id": c.candidate_id,
                    "in_draft": {
                        "primary": "yes",
                        "alternate": "no",
                        "rejected": "rejected",
                    }[c.plan.role],
                    "ticker": c.plan.ticker,
                    "items": "/".join(c.plan.item_keys),
                    "query_type": c.plan.query_type,
                    "generation_mode": c.plan.mode,
                    "question": c.question,
                    "snippet_preview": c.evidences[0].snippet[:80],
                    "approved": "",
                    "reviewer_comment": "",
                }
            )

    filings = load_filings()
    REVIEW_MD.write_text(_render_review_md(candidates, filings), encoding="utf-8")

    # Final gate: the draft dataset must pass the store-anchored validator.
    rows = [
        Row(
            row_id=c.candidate_id,
            question=c.question,
            header_paths=[e.header_path for e in c.evidences],
            tickers=[c.plan.ticker],
            spans=[e.span for e in c.evidences],
            snippets=[e.snippet for e in c.evidences],
            query_type=c.plan.query_type,
        )
        for c in primaries
    ]
    issues = validate_rows(rows, filings)
    for issue in issues:
        print(f"[VALIDATE] {issue.row_id} {issue.rule}: {issue.message}")
    print(
        f"emitted dataset.csv ({len(primaries)} rows), review.csv/md "
        f"({len(candidates)} candidates); validator issues: {len(issues)}"
    )
    return 1 if issues else 0


def _render_review_md(
    candidates: list[Candidate],
    filings: dict[tuple[str, int], ParsedFiling],
) -> str:
    lines = [
        "# sec_retrieval_ab dataset — human review sheet",
        "",
        "Mark decisions in `review.csv` (`approved`: yes/no + optional "
        "`reviewer_comment`). Snippet is **bold** inside its span; one "
        "sentence of context shown on each side.",
        "",
    ]
    rejected_header_written = False
    for c in sorted(candidates, key=_role_order):
        if c.plan.role == "rejected" and not rejected_header_written:
            lines += [
                "",
                "# Rejected candidates",
                "",
                "Removed from the draft after quality review; kept for "
                "provenance only. No review action needed.",
                "",
            ]
            rejected_header_written = True
        grid = TICKER_GRID[c.plan.ticker]
        role_tag = {"primary": "", "alternate": ", ALTERNATE", "rejected": ", REJECTED"}
        lines += [
            f"## {c.candidate_id} — {c.plan.ticker} "
            f"{'/'.join('Item ' + k.upper() for k in c.plan.item_keys)} "
            f"({c.plan.query_type}, {c.plan.mode}{role_tag[c.plan.role]})",
            "",
            f"- sector: {grid['sector']} / cap: {grid['cap']} / "
            f"FY{c.fiscal_year} / detection: "
            f"{', '.join(e.detection_source for e in c.evidences)}",
            f"- **query**: {c.question}",
        ]
        if c.plan.intent:
            lines.append(f"- user_intent: {c.plan.intent}")
        lines.append(f"- curation_note: {c.curation_note}")
        if c.rejection_reason:
            lines.append(f"- **rejected because**: {c.rejection_reason}")
        for i, ev in enumerate(c.evidences):
            lines += [
                "",
                f"**Evidence {i + 1}** — `{ev.header_path}`"
                + (f" / block: {ev.block_heading}" if ev.block_heading else ""),
                "",
                _quote_with_context(ev, filings),
            ]
        lines.append("\n---\n")
    return "\n".join(lines)


def _quote_with_context(
    ev: Evidence, filings: dict[tuple[str, int], ParsedFiling]
) -> str:
    ticker, fy = ev.header_path.split(" / ")[0], int(ev.header_path.split(" / ")[1])
    filing = filings[(ticker, fy)]
    item = next(i for i in filing.items if i.item.strip().lower() == ev.item_key)
    views = build_unit_views(item)
    for view in views:
        pos = view.text.lower().find(ev.span.lower())
        if pos < 0:
            continue
        before = view.text[max(0, pos - 200) : pos].strip()
        after = view.text[pos + len(ev.span) : pos + len(ev.span) + 200].strip()
        span_marked = ev.span.replace(ev.snippet, f"**{ev.snippet}**", 1)
        return "> " + " ".join(
            filter(
                None,
                [
                    f"…{before}" if before else "",
                    span_marked,
                    f"{after}…" if after else "",
                ],
            )
        ).replace("\n", " ")
    return "> (span not located for preview)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="generate only the first N plans (smoke run)",
    )
    parser.add_argument(
        "--emit-only",
        action="store_true",
        help="skip generation; rebuild outputs from candidates.json",
    )
    args = parser.parse_args(argv)
    if not args.emit_only:
        generate(args.limit)
    return emit()


if __name__ == "__main__":
    sys.exit(main())
