"""Build the C1 / C0 Tavily fixtures from the labeled packet.

C1 is the recorded Tavily output of one ``reader_luna_medium`` run per row,
unchanged. C0 is the same output with every sentence whose final label is
``unrelated_other`` cut out of the snippet text. Nothing else differs.

Final label per sentence: the two labelers' label when they agree; otherwise
the human adjudication for the seven disputed passages, the two documented
rules for the systematic disagreements (page chrome stays, passage
continuations follow their passage), and "keep" when neither labeler wanted
the sentence deleted. Disputed passages are kept unless ADJUDICATION.md
records a delete decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[3]
LABEL_DIR = BACKEND_DIR.parent / "artifacts" / "current" / "off_target_labeling"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures.json"

DELETE = "unrelated_other"

# ADJUDICATION.md P1..P7 -> sentence ids.
PASSAGES = {
    "P1": ["r2-a3-s11", "r2-a3-s12", "r2-a3-s13", "r2-a3-s14"],
    "P2": ["r4-a8-s8"],
    "P3": ["r4-a13-s9", "r4-a13-s10"],
    "P4": ["r4-a15-s8"],
    "P5": ["r7-a8-s2"],
    "P6": ["r10-a6-s4"],
    "P7": ["r14-a8-s10", "r14-a8-s11", "r14-a8-s12"],
}
RULE_CHROME_KEEP = {
    "r5-a2-s3", "r5-a2-s5", "r7-a8-s3", "r9-a6-s4", "r9-a6-s5",
    "r14-a3-s11", "r14-a3-s12", "r14-a3-s13", "r14-a4-s5", "r14-a4-s6",
    "r14-a4-s7", "r24-a3-s14", "r24-a3-s16", "r24-a4-s1", "r24-a7-s1",
    "r24-a7-s2", "r24-a7-s3", "r24-a9-s2", "r24-a9-s3", "r24-a9-s4",
    "r24-a9-s6", "r24-a10-s2", "r24-a10-s3", "r24-a10-s4", "r24-a10-s6",
}  # fmt: skip
RULE_PASSAGE_DELETE = {
    "r1-a4-s4", "r1-a4-s5", "r4-a7-s1", "r4-a7-s2", "r4-a7-s3", "r4-a7-s4",
    "r4-a7-s5", "r4-a7-s7", "r4-a8-s2", "r10-a8-s3", "r10-a8-s4",
}  # fmt: skip


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def read_adjudication(path: Path) -> dict[str, str]:
    decisions = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(P\d)\s*\|", line)
        if not m:
            continue
        cell = line.rstrip().rstrip("|").rsplit("|", 1)[-1].strip()
        if "刪" in cell:
            decisions[m.group(1)] = "delete"
        elif "留" in cell:
            decisions[m.group(1)] = "keep"
    return decisions


def final_labels(label_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    labels = {}
    for name in ("gemini", "codex"):
        for row in _jsonl(label_dir / f"labels_{name}.jsonl"):
            for x in row["labels"]:
                labels.setdefault(x["sid"], {})[name] = x
    adjudication = read_adjudication(label_dir / "ADJUDICATION.md")
    by_sid = {sid: p for p, sids in PASSAGES.items() for sid in sids}

    final: dict[str, dict[str, Any]] = {}
    for sid, pair in labels.items():
        g, c = pair["gemini"], pair["codex"]
        companies = sorted(
            set(g.get("other_companies") or []) | set(c.get("other_companies") or [])
        )
        if sid in by_sid:
            # Disputed passages without a human decision are kept (not cut
            # from C0): C0 only loses content both labelers call unrelated.
            decision = adjudication.get(by_sid[sid], "keep")
            label = DELETE if decision == "delete" else "relevant_other"
            source = f"dispute:{by_sid[sid]}:{decision}"
        elif g["label"] == c["label"]:
            label, source = g["label"], "agree"
        elif sid in RULE_CHROME_KEEP:
            label, source = "target_or_neutral", "rule:chrome"
        elif sid in RULE_PASSAGE_DELETE:
            label, source = DELETE, "rule:passage"
        elif DELETE in (g["label"], c["label"]):
            raise SystemExit(f"unresolved delete dispute: {sid}")
        else:
            label = "mixed" if "mixed" in (g["label"], c["label"]) else "relevant_other"
            source = "keep-either"
        final[sid] = {"label": label, "source": source, "other_companies": companies}
    return final, adjudication


def _sha(content: str) -> str:
    return hashlib.sha1(content.encode()).hexdigest()[:10]


def _redact(content: str, sentences: list[str]) -> str:
    for text in sentences:
        if text not in content:
            raise SystemExit(f"sentence not found in snippet: {text[:60]!r}")
        content = content.replace(text, "", 1)
    content = re.sub(r"[ \t]{2,}", " ", content)
    content = re.sub(r"(\[\.\.\.\]\s*){2,}", "[...] ", content)
    return content.strip()


def build(label_dir: Path = LABEL_DIR) -> dict[str, Any]:
    final, adjudication = final_labels(label_dir)
    packet = {p["row"]: p for p in _jsonl(label_dir / "packet.jsonl")}
    sources = {
        s["row"]: s
        for s in json.loads((label_dir / "fixture_source_runs.json").read_text())
    }

    rows = {}
    for row_id, p in packet.items():
        by_sha = {a["content_sha1"]: a for a in p["articles"]}
        kept_companies, deleted_companies, n_deleted = set(), set(), 0
        c0_calls = []
        for call in sources[row_id]["calls"]:
            results = []
            for item in call["results"]:
                article = by_sha[_sha(item.get("content") or "")]
                drop = [
                    s["text"]
                    for s in article["sentences"]
                    if final[s["sid"]]["label"] == DELETE
                ]
                for s in article["sentences"]:
                    f = final[s["sid"]]
                    (
                        deleted_companies if f["label"] == DELETE else kept_companies
                    ).update(f["other_companies"])
                n_deleted += len(drop)
                results.append(
                    {**item, "content": _redact(item.get("content") or "", drop)}
                )
            c0_calls.append({"args": call["args"], "results": results})
        # Companies only ever named in deleted sentences: their appearance in an
        # answer can only come from the unrelated spans (C1) or the model's own
        # knowledge (C0).
        leak = sorted(deleted_companies - kept_companies)
        rows[row_id] = {
            "row": row_id,
            "question_zh": p["question_zh"],
            "target_companies": p["target_companies"],
            "source_repetition": sources[row_id]["repetition"],
            "deleted_sentences": n_deleted,
            "leak_companies": leak,
            "C1": sources[row_id]["calls"],
            "C0": c0_calls,
        }
    return {
        "adjudication": adjudication,
        "label_sources": _count(final),
        "rows": rows,
        "final_labels": final,
    }


def _count(final: dict[str, dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in final.values():
        key = f"{f['source']}|{f['label']}"
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=FIXTURE_PATH)
    args = parser.parse_args()
    data = build()
    args.out.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    for r in data["rows"].values():
        print(r["row"], "deleted", r["deleted_sentences"], "leak", r["leak_companies"])
    print(data["label_sources"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
