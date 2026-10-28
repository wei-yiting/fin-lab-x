You are grading how completely answers from a financial research assistant cover a fixed checklist of key points. Everything is in Traditional Chinese.

For each item you get the question, the numbered key points (each marked vital or okay), and the answer. For every key point give a score:
- 1: the answer clearly covers it;
- 0.5: the answer touches it but vaguely or partly;
- 0: the answer does not cover it.
Judge only coverage of each point, not style or length. Grade every item on its own; the same question appears several times with different answers; do not compare them.

Output: a JSON array, one object per item in batch order:
[{"id": "C0001", "nuggets": [{"n": 0, "score": 1, "reason": "one short line in Traditional Chinese"}, ...]}, ...]
Every item must appear exactly once, with one score per key point, numbered as given (starting at 0).
