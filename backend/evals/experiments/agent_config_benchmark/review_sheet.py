"""Blind pairwise review sheet for E1 (Arm A vs Arm B outputs).

Each dev row's two answers are shuffled into X / Y with a system RNG; the
label -> arm key goes to a separate JSON file so the sheet itself carries
no arm identity. Produces a self-contained HTML sheet (verdict radio
buttons + notes, exportable as CSV) and a Markdown twin.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import random
import re
from pathlib import Path

from markdown_it import MarkdownIt

from backend.evals.experiments.agent_config_benchmark.run import (
    ARM_A,
    ARM_B,
    SCENARIO_DIR,
)

VERDICTS = ["X 較好", "Y 較好", "平手", "兩者都差"]

# Only the RAG arm can emit chunk citation ids, so they would unblind every
# pair; the sheet shows a neutral label instead (raw outputs stay untouched).
_SEC_CHUNK_ID_RE = re.compile(r"`?sec://[^\s`)\]]+`?")


# Answers are rendered to HTML at build time, not in the browser: viewers that
# show the sheet as a static snapshot don't run scripts. html=False escapes any
# raw HTML inside model output instead of passing it through.
_MD = MarkdownIt("commonmark", {"html": False}).enable("table")


def _mask(answer: str) -> str:
    return _SEC_CHUNK_ID_RE.sub("SEC 10-K excerpt", answer)


def build(raw_dir: Path, out_dir: Path) -> None:
    rng = random.SystemRandom()
    with open(SCENARIO_DIR / "dataset.csv", newline="") as f:
        questions = {row["id"]: row["question"] for row in csv.DictReader(f)}

    pairs = []
    key = {}
    for path_a in sorted(raw_dir.glob(f"*__{ARM_A}.json")):
        path_b = path_a.with_name(path_a.name.replace(ARM_A, ARM_B))
        if not path_b.exists():
            continue
        rec_a, rec_b = json.loads(path_a.read_text()), json.loads(path_b.read_text())
        row_id = rec_a["row_id"]
        answers = {
            ARM_A: (rec_a.get("output") or {}).get("response")
            or f"(no answer — {rec_a.get('task_error')})",
            ARM_B: (rec_b.get("output") or {}).get("response")
            or f"(no answer — {rec_b.get('task_error')})",
        }
        x_arm = rng.choice([ARM_A, ARM_B])
        y_arm = ARM_B if x_arm == ARM_A else ARM_A
        key[row_id] = {"X": x_arm, "Y": y_arm}
        pairs.append(
            {
                "row_id": row_id,
                "question": questions[row_id],
                "X": _mask(answers[x_arm]),
                "Y": _mask(answers[y_arm]),
            }
        )
    pairs.sort(key=lambda p: int(p["row_id"]))

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "e1_blind_review_KEY.json").write_text(
        json.dumps(
            {
                "note": "Do not open before finishing the review sheet.",
                "arms": {ARM_A: "Arm A (no RAG)", ARM_B: "Arm B (RAG bundle)"},
                "key": key,
            },
            indent=2,
        )
    )
    (out_dir / "e1_blind_review.md").write_text(_markdown(pairs))
    (out_dir / "e1_blind_review.html").write_text(_html(pairs))


def _markdown(pairs: list[dict]) -> str:
    lines = [
        "# E1 blind pairwise review",
        "",
        "For each question, judge which answer better serves an investor asking it "
        "(correct, grounded, on-target, useful). Verdict: "
        + " / ".join(VERDICTS)
        + ". SEC chunk citation ids are masked as `SEC 10-K excerpt`; citation style "
        "(e.g. `[N]` markers) can still hint at which config produced an answer — "
        "judge the content, not the format. The key is "
        "in `e1_blind_review_KEY.json`; open it only after you finish.",
        "",
    ]
    for pair in pairs:
        lines += [
            f"## Row {pair['row_id']}",
            "",
            f"**Question:** {pair['question']}",
            "",
            "### X",
            "",
            pair["X"],
            "",
            "### Y",
            "",
            pair["Y"],
            "",
            "**Verdict:** ☐ X 較好 ☐ Y 較好 ☐ 平手 ☐ 兩者都差",
            "",
            "**Notes:**",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


def _html(pairs: list[dict]) -> str:
    cards = []
    for pair in pairs:
        rid = html.escape(pair["row_id"])
        radios = "".join(
            f'<label><input type="radio" name="v{rid}" value="{html.escape(v)}"> {html.escape(v)}</label>'
            for v in VERDICTS
        )
        cards.append(
            f"""<section class="card" data-row="{rid}">
  <h2>Row {rid}</h2>
  <p class="q">{html.escape(pair["question"])}</p>
  <div class="pair">
    <article><h3>X</h3><div class="md">{_MD.render(pair["X"])}</div></article>
    <article><h3>Y</h3><div class="md">{_MD.render(pair["Y"])}</div></article>
  </div>
  <div class="verdict">{radios}</div>
  <textarea placeholder="備註" name="n{rid}"></textarea>
</section>"""
        )
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>E1 Blind Review</title>
<style>
:root {{ --bg:#fafaf9; --fg:#1c1917; --muted:#57534e; --card:#fff; --line:#e7e5e4; --accent:#0f766e; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1c1917; --fg:#f5f5f4; --muted:#a8a29e; --card:#292524; --line:#44403c; --accent:#5eead4; }} }}
body {{ background:var(--bg); color:var(--fg); font:15px/1.6 -apple-system, "PingFang TC", sans-serif; margin:0; padding:16px; }}
main {{ max-width:1200px; margin:0 auto; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; margin:16px 0; }}
.q {{ font-weight:600; }}
.pair {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
@media (max-width:800px) {{ .pair {{ grid-template-columns:1fr; }} }}
article {{ border:1px solid var(--line); border-radius:8px; padding:12px; overflow-wrap:anywhere; }}
article h3 {{ margin-top:0; color:var(--accent); }}
.md table {{ border-collapse:collapse; display:block; overflow-x:auto; }}
.md th, .md td {{ border:1px solid var(--line); padding:4px 8px; }}
.verdict label {{ margin-right:16px; white-space:nowrap; }}
textarea {{ width:100%; min-height:60px; margin-top:8px; background:var(--bg); color:var(--fg); border:1px solid var(--line); border-radius:6px; }}
button {{ background:var(--accent); color:var(--bg); border:0; border-radius:6px; padding:8px 14px; font-size:15px; }}
.muted {{ color:var(--muted); }}
</style></head><body><main>
<h1>E1 blind pairwise review</h1>
<p class="muted">每題判斷哪個回答對發問的投資人比較有用（正確、有根據、切題）。SEC chunk 的 citation id 已遮成「SEC 10-K excerpt」；引用格式（例如 <code>[N]</code>）仍可能透露是哪個 config 產生的，請以內容判斷，不要看格式。答案 key 在 <code>e1_blind_review_KEY.json</code>，做完再打開。</p>
{"".join(cards)}
<button id="export">Export CSV</button>
</main>
<script>
document.getElementById('export').onclick = () => {{
  const rows = [['row_id','verdict','notes']];
  document.querySelectorAll('.card').forEach(c => {{
    const r = c.dataset.row;
    const v = (c.querySelector('input[name="v'+r+'"]:checked')||{{}}).value || '';
    const n = c.querySelector('textarea').value.replace(/"/g,'""');
    rows.push([r, v, '"'+n+'"']);
  }});
  const blob = new Blob([rows.map(r => r.join(',')).join('\\n')], {{type:'text/csv'}});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'e1_blind_review_verdicts.csv'; a.click();
}};
</script></body></html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    build(args.raw_dir, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
