"""Score the RAG ablation quality pools; arm A = luna_medium (control), B = reader_luna_medium."""
import json, statistics, sys
from collections import defaultdict
from pathlib import Path

from backend.evals.experiments.reader_model_reasoning import grounding as g
from backend.evals.experiments.reader_model_reasoning import judge as j

A, B = "luna_medium", "reader_luna_medium"
out = Path(sys.argv[1])
g.FAITH_ARMS = [A, B]
g.ARM_NAMES = [A, B]
g.CONTROL_ARM = A
r3 = lambda t: [round(x, 3) for x in t]

# signal judge
key = json.loads((out / "judge/KEY_do_not_share/KEY_do_not_share.json").read_text())
res = j.load_results(out / "judge/results")
entries = [{**key[i], "id": i, "pass_rate": j._pass_rate(s),
            "all_pass": float(all(x["pass"] for x in s))} for i, s in res.items()]
real = [e for e in entries if e["kind"] == "real"]
sig = {"items_judged": len(entries), "expected": len(key)}
for label, subset in (("all_reps", real), ("rep1", [e for e in real if e["rep"] == 1])):
    pr = j._row_means(subset, "arm", "pass_rate")
    ap = j._row_means(subset, "arm", "all_pass")
    sig[label] = {
        arm: {"answers": sum(e["arm"] == arm for e in subset),
              "pass_rate": r3(j._ci(pr[arm])), "all_pass": r3(j._ci(ap[arm]))}
        for arm in (A, B)}
    sig[label]["delta_B_minus_A"] = r3(j._paired(pr[B], pr[A]))
    sig[label]["delta_all_pass_B_minus_A"] = r3(j._paired(ap[B], ap[A]))
    sig[label]["rows_B_lower"] = sum(pr[B][r] < pr[A][r] for r in pr[A])
    sig[label]["rows_B_higher"] = sum(pr[B][r] > pr[A][r] for r in pr[A])
base = {(e["row"], e["arm"], e["rep"]): e["pass_rate"] for e in real}
sig["controls"] = {}
for kind in j.CONTROL_KINDS:
    cs = [e for e in entries if e["kind"] == kind]
    d = {e["row"]: e["pass_rate"] - (base[(e["row"], e["base_arm"], e["base_rep"])]
         if kind != "off_topic" else statistics.mean(
             v for (r, _, _), v in base.items() if r == e["row"])) for e in cs}
    sig["controls"][kind] = {"n": len(cs), "rate": round(statistics.mean(e["pass_rate"] for e in cs), 3),
                             "delta_vs_base": r3(j._ci(d))}
# signals passed by every real answer
cells = defaultdict(list)
for i, s in res.items():
    if key[i]["kind"] == "real":
        for x in s:
            cells[(key[i]["row"], x["signal"])].append(x["pass"])
sig["signals_passed_by_all_real"] = f"{sum(all(v) for v in cells.values())}/{len(cells)}"

# faithfulness
fkey = json.loads((out / "grounding/KEY_do_not_share/KEY_faith.json").read_text())
fres = g._results(out / "grounding/faith", "claims")
fe = []
for i, meta in fkey.items():
    claims = fres.get(i)
    if claims is None:
        continue
    v = [c["verdict"] for c in claims]
    n = len(v)
    fe.append({**meta, "id": i, "claims": n,
               "support_rate": v.count("supported") / n if n else 1.0,
               "contradicted": v.count("contradicted"), "unsupported": v.count("unsupported"),
               "flagged_alteration": meta["kind"] == "perturbed" and any(
                   c["verdict"] != "supported" and meta["altered"].replace(",", "") in c["claim"].replace(",", "")
                   for c in claims)})
faith = {"items_judged": len(fe), "expected": len(fkey)}
for arm in (A, B):
    es = [e for e in fe if e.get("arm") == arm and e["kind"] == "real"]
    faith[arm] = {"answers": len(es), "claims": sum(e["claims"] for e in es),
                  "support_rate": r3(j._ci(g._by_row(fe, arm, "support_rate"))),
                  "pooled_support": round(sum(e["claims"] * e["support_rate"] for e in es) / max(1, sum(e["claims"] for e in es)), 3),
                  "unsupported_claims": sum(e["unsupported"] for e in es),
                  "contradicted_claims": sum(e["contradicted"] for e in es),
                  "answers_with_contradiction": sum(1 for e in es if e["contradicted"])}
faith["delta_support_B_minus_A"] = r3(j._paired(g._by_row(fe, B, "support_rate"), g._by_row(fe, A, "support_rate")))
pert = [e for e in fe if e["kind"] == "perturbed"]
faith["perturbed"] = {arm: f"{sum(e['flagged_alteration'] for e in pert if e['base_arm'] == arm)}/{sum(e['base_arm'] == arm for e in pert)}" for arm in (A, B)}

# completeness
cov = {}
for name, cdir, kpath, ndir in (
    ("fresh_checklist", "coverage", "KEY_do_not_share/KEY_coverage.json", out / "grounding/nuggets"),
    ("prior_checklist", "coverage_prior_checklist", "KEY_do_not_share/prior_checklist/KEY_coverage.json",
     Path(sys.argv[2]))):
    if not (out / "grounding" / cdir / "results").glob("result_*.json"):
        continue
    try:
        c = g.score_coverage(out / "grounding" / cdir, out / "grounding" / kpath, ndir)
    except Exception as exc:  # results not complete yet
        cov[name] = f"pending: {exc!r}"
        continue
    cov[name] = {"items_scored": len(c["entries"]),
                 **{arm: {k: r3(v) for k, v in c["arms"][arm].items()} for arm in (A, B)},
                 "delta_vital_B_minus_A": r3(j._paired(g._by_row(c["entries"], B, "vital_recall"), g._by_row(c["entries"], A, "vital_recall"))),
                 "delta_all_B_minus_A": r3(j._paired(g._by_row(c["entries"], B, "all_recall"), g._by_row(c["entries"], A, "all_recall"))),
                 "truncated": {"n": c["truncated"]["n"], "vital_recall": r3(c["truncated"]["vital_recall"]),
                               "delta_vs_base": r3(c["truncated"]["delta_vs_base"])}}
    (out / "grounding" / f"coverage_scores_{name}.json").write_text(json.dumps(c["entries"], ensure_ascii=False, indent=1))

summary = {"signal": sig, "faithfulness": faith, "completeness": cov}
(out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
(out / "judge/judge_scores.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1))
(out / "grounding/faith_scores.json").write_text(json.dumps(fe, ensure_ascii=False, indent=1))
print(json.dumps(summary, indent=1, ensure_ascii=False))
