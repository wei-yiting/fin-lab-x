You are grading answers from a financial research assistant. Answers are in Traditional Chinese. Each item gives the user's question, the company or companies the user asked about (TARGET), and the ANSWER.

Rubric (functional criterion). Every part of the answer should serve the user's question about the TARGET. Content about another company or the broader market is acceptable only when it directly supports the answer to the question that was asked — e.g. a peer comparison or market context that helps explain the TARGET's situation on the aspect the question asks about. Content about another company that stands on its own — that company's own news, results, deals or regulatory matters with no stated link to what the question asks about the TARGET — is OFF-TARGET, regardless of length. Mentioning another company only to say it is unrelated is fine. Data sources, analysts or media cited as the source of a statement are not "another company".

For each item:
1. List every statement in the answer that is about a company other than the TARGET (skip statements that only name a source). Quote or closely paraphrase it.
2. Label each "supports" or "off_target", with a short reason.
3. verdict = "N" if any statement is off_target, else "Y".

Grade every item on its own; do not compare items.

Output: write a JSON array, one object per item in batch order, to the result path given below:
[{"id": "J001", "statements": [{"text": "...", "company": "...", "label": "supports", "reason": "..."}], "verdict": "Y"}, ...]
Every item must appear exactly once. Write the JSON file only; reply "done" when written.