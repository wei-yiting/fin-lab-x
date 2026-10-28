"""Build blinded judge / faithfulness / nugget pools for the RAG ablation."""
import json, random, sys
from collections import defaultdict
from pathlib import Path

from backend.evals.experiments.reader_model_reasoning import grounding as g
from backend.evals.experiments.reader_model_reasoning import judge as j

ARM_A, ARM_B = "luna_medium", "reader_luna_medium"
raw, out = Path(sys.argv[1]), Path(sys.argv[2])
g.FAITH_ARMS = [ARM_A, ARM_B]
g.ARM_NAMES = [ARM_A, ARM_B]
g.CONTROL_ARM = ARM_A

# 1. signal judge: all 3 reps, both arms, + controls; no within-pool re-judge
j.cmd_build_pool(raw, out / "judge", out / "judge" / "KEY_do_not_share",
                 id_prefix="Q", rejudge_items=0)

# 2. nugget checklists from both arms' rep-1 answers
g.cmd_build_nuggets(raw, out / "grounding" / "nuggets")

# 3. faithfulness: per-item evidence files (arm A evidence is up to 1.1M chars)
FAITH_BATCH, PERTURBED_ROWS = 3, 12
dataset = j.load_dataset()
rng = random.Random(g.SEED)
recs = [r for r in g._records(raw, 1) if r["arm"] in g.FAITH_ARMS]
pool = [({"rec": r, "answer": g._answer(r)},
         {"row": r["row_id"], "kind": "real", "arm": r["arm"], "rep": 1}) for r in recs]
by_row = defaultdict(list)
for r in recs:
    by_row[r["row_id"]].append(r)
rows = sorted(by_row, key=int)
for i, row in enumerate(rng.sample(rows, PERTURBED_ROWS)):
    want = ARM_A if i % 2 == 0 else ARM_B
    base = next(r for r in by_row[row] if r["arm"] == want)
    res = g.perturb(g._answer(base), rng)
    if res:
        ans, change = res
        pool.append(({"rec": base, "answer": ans},
                     {"row": row, "kind": "perturbed", "base_arm": want, "rep": 1, **change}))
rng.shuffle(pool)
fdir = out / "grounding" / "faith"
(fdir / "evidence").mkdir(parents=True, exist_ok=True)
key, items = {}, []
for n, (item, meta) in enumerate(pool, start=1):
    iid = f"F{n:04d}"
    key[iid] = meta
    ev = fdir / "evidence" / f"evidence_{iid}.txt"
    ev.write_text(g._evidence(item["rec"]))
    items.append({"id": iid, "question": dataset[meta["row"]]["question"],
                  "evidence_file": f"evidence/evidence_{iid}.txt",
                  "evidence_chars": ev.stat().st_size, "answer": item["answer"]})

def render(name, its):
    lines = [f"# Faithfulness batch {name} — {len(its)} items", ""]
    for it in its:
        lines += [f"===== ITEM {it['id']} =====", "", "QUESTION:", it["question"], "",
                  f"EVIDENCE: in file {it['evidence_file']} ({it['evidence_chars']:,} characters)", "",
                  f"----- BEGIN ANSWER {it['id']} -----", it["answer"],
                  f"----- END ANSWER {it['id']} -----", ""]
    return "\n".join(lines)

b = 0
for b, start in enumerate(range(0, len(items), FAITH_BATCH), start=1):
    g._write(fdir / "batches", str(b), items[start:start + FAITH_BATCH], render)
(fdir / "faith_prompt.md").write_text(g.FAITH_PROMPT + "\n")
kd = out / "grounding" / "KEY_do_not_share"
kd.mkdir(parents=True, exist_ok=True)
(kd / "KEY_faith.json").write_text(json.dumps(key, ensure_ascii=False, indent=1))
kinds = defaultdict(int)
for m in key.values():
    kinds[m["kind"]] += 1
print(f"{len(items)} faith items in {b} batches: {dict(kinds)}")
