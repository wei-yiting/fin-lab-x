# Span labeling guide — off-target company controlled eval

> 給 Gemini / Codex 的標註說明。兩個 labeler 獨立標註、互不看對方結果；
> 輸出各自存成 `labels_gemini.jsonl` / `labels_codex.jsonl`，之後比對一致性、分歧交人工裁定。

## Task

You are labeling news snippets that a financial research assistant received from a
news-search tool while answering a user's question. The labels decide which sentences
will be **deleted** to build a "clean" version of the evidence, so be precise.

Input: `packet.jsonl` — one JSON object per question (`row`), with:
- `question_zh`: the user's question (Traditional Chinese)
- `target_companies`: the companies the user asked about
- `articles[].sentences[]`: numbered sentences (`sid`, `text`). Snippets are extracts, so
  sentences may be fragments; label them as they are.

Label **every** sentence with exactly one label.

## Labels

| label | use when |
|---|---|
| `target_or_neutral` | The sentence mentions no business other than the target companies. Also use this when the only non-target entities are: the target's own subsidiaries, brands or products (Google ⊂ Alphabet, YouTube ⊂ Google); regulators, courts, governments (DOJ, EU, FTC); market indexes or whole sectors ("the S&P 500", "chip stocks"); analysts, brokers or media cited only as the **source** of a statement ("Piper Sandler wrote…"). |
| `relevant_other` | Mentions another business, and that content **helps answer this question about the target** — e.g. a competitor/supplier/customer event the text links to the target, a deal or dispute the target is party to, or a comparison the question itself asks for. The link must be stated in the text or be direct; do not invent one. |
| `unrelated_other` | Mentions another business, and that content is about that business's own situation with no stated link to the target or to what the question asks. Removing it loses nothing a careful analyst would need for this question. |
| `mixed` | One sentence carries both target information needed for the question **and** unrelated other-company information, so it cannot be deleted without losing target information. |

Relevance is judged against **this question**, not the target in general: an article about
Apple's iPhone sales is `unrelated_other` for "Google's antitrust risk", but Apple's
default-search payments to Google are `relevant_other` for the same question.

When unsure between `relevant_other` and `unrelated_other`, pick the one a careful analyst
would choose and explain in `note`.

Two rules added after the first labeling round (resolve the two systematic disagreements):

- **Label by passage, not by name.** A sentence that continues another company's passage
  without naming it (a quote from that company's CEO, "the bank's outlook…") takes the
  passage's label.
- **Page chrome is neutral.** Navigation menus, newsletter/subscription/event promotions,
  image captions, bylines and site boilerplate are `target_or_neutral`, even when they name a
  business (the publisher, a venue). They are not other-company content.

## Per-row redaction check

After labeling a row, imagine every `unrelated_other` sentence deleted. Answer:
- `redaction_coherent`: does the remaining text still read as natural news extracts
  (no dangling references like "the company" now pointing at nothing, no broken sentences)?
- `redaction_note`: if not, which `sid`s cause the problem.

## Output format

One JSON object per line, one line per row, in packet order:

```json
{"row": "7",
 "labels": [
   {"sid": "r7-a1-s1", "label": "target_or_neutral", "other_companies": [], "note": ""},
   {"sid": "r7-a2-s5", "label": "relevant_other", "other_companies": ["Apple", "Mozilla", "Samsung", "Verizon"], "note": "search-default deals are part of Google's antitrust case"}
 ],
 "redaction_coherent": true,
 "redaction_note": ""}
```

Rules: every `sid` in the row appears exactly once; `other_companies` lists the non-target
businesses named in the sentence (empty for `target_or_neutral`); `note` is required for
`relevant_other`, `unrelated_other` and `mixed`. Output JSON only, no commentary.
