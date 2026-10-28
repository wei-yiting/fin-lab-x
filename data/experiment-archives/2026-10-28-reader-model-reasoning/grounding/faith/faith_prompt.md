You are checking whether answers from a financial research assistant are faithful to the evidence the assistant retrieved. Answers are in Traditional Chinese; evidence is mostly English tool output (SEC filing excerpts, news search results, market data).

For each item you get the question, the EVIDENCE (every tool result that run received), and the ANSWER.

1. List the checkable factual claims in the answer: figures, percentages, dates, amounts, named events, rulings, guidance, and statements attributed to a filing or news source. Skip opinions, conclusions, hedges, general background and advice. List at most 25 claims, preferring figures and attributed statements. Quote or closely paraphrase each claim in the answer's language.
2. Label each claim against the EVIDENCE only:
   - "supported": the evidence states it (allow rounding, unit conversion and translation);
   - "unsupported": the evidence does not contain it (it may still be true; you are not checking the world, only this evidence);
   - "contradicted": the evidence states something incompatible (e.g. a different figure for the same thing).
3. Grade every item on its own; do not compare items.

Output: a JSON array, one object per item in batch order:
[{"id": "F0001", "claims": [{"claim": "...", "verdict": "supported", "note": "short pointer to the evidence or why not"}, ...]}, ...]
Every item must appear exactly once. If an answer has no checkable claims, return an empty claims list.
