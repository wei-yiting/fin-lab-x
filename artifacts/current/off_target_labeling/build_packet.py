"""Build the span-labeling packet for the off-target controlled eval.

Usage: python3 -I build_packet.py <raw_dir> <dataset_csv> <out_dir>
"""

import csv
import glob
import hashlib
import json
import re
import sys
from pathlib import Path

ROWS = ["1", "2", "3", "4", "5", "7", "9", "10", "14", "23", "24", "26", "27", "29"]
ARM = "reader_luna_medium"

NAMES = {
    "AAPL": ["Apple"], "MSFT": ["Microsoft"], "GOOGL": ["Alphabet", "Google"],
    "AMZN": ["Amazon"], "META": ["Meta", "Facebook"], "NVDA": ["Nvidia"],
    "TSLA": ["Tesla"], "NFLX": ["Netflix"], "DIS": ["Disney"], "BA": ["Boeing"],
    "INTC": ["Intel"], "AMD": ["AMD", "Advanced Micro"], "JPM": ["JPMorgan"],
    "WMT": ["Walmart"], "COST": ["Costco"], "KO": ["Coca-Cola"], "PEP": ["PepsiCo"],
    "XOM": ["Exxon"], "V": ["Visa"], "MA": ["Mastercard"],
    "JNJ": ["Johnson & Johnson"], "LLY": ["Eli Lilly", "Lilly"], "NKE": ["Nike"],
    "MCD": ["McDonald"], "TSM": ["TSMC", "Taiwan Semiconductor"], "ASML": ["ASML"],
    "AIR": ["Airbus"], "BRK-B": ["Berkshire"], "ORCL": ["Oracle"],
    "QCOM": ["Qualcomm"], "AVGO": ["Broadcom"], "CVX": ["Chevron"],
    "GS": ["Goldman"], "MS": ["Morgan Stanley"], "SBUX": ["Starbucks"],
    "UBER": ["Uber"], "PFE": ["Pfizer"], "NVO": ["Novo Nordisk"],
}

ABBREV = r"(?<!\bU\.S)(?<!\bInc)(?<!\bCorp)(?<!\bCo)(?<!\bMr)(?<!\bMs)(?<!\bNo)(?<!\bSt)(?<!\bLtd)"
SPLIT_RE = re.compile(ABBREV + r"(?<=[.!?])\s+(?=[A-Z\"“(])")


def tavily_calls(rec):
    calls = []
    for t in (rec.get("output") or {}).get("tool_outputs") or []:
        if t.get("tool") != "tavily_financial_search" or "result" not in t:
            continue
        r = t["result"]
        r = json.loads(r) if isinstance(r, str) else r
        calls.append({"args": t["args"], "results": (r or {}).get("results", [])})
    return calls


def mixed_count(calls):
    tickers = {(c["args"].get("ticker") or "").upper() for c in calls}
    seen, n = set(), 0
    for c in calls:
        for it in c["results"]:
            content = it.get("content") or ""
            if content in seen:
                continue
            seen.add(content)
            if any(
                k not in tickers and any(re.search(rf"\b{re.escape(a)}\b", content) for a in al)
                for k, al in NAMES.items()
            ):
                n += 1
    return n


def segments(content):
    out = []
    for part in content.split("[...]"):
        part = part.strip()
        if part:
            out.extend(s.strip() for s in SPLIT_RE.split(part) if s.strip())
    return out


def main(raw_dir, dataset_csv, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ds = {r["id"]: r for r in csv.DictReader(open(dataset_csv, encoding="utf-8"))}
    packet, source = [], []
    for rid in ROWS:
        recs = [json.load(open(f)) for f in glob.glob(f"{raw_dir}/*/row{int(rid):02d}__{ARM}.json")]
        best = max(recs, key=lambda r: (mixed_count(tavily_calls(r)), -r["repetition"]))
        calls = tavily_calls(best)
        source.append({"row": rid, "repetition": best["repetition"], "calls": calls})
        articles, seen = [], set()
        for c in calls:
            for it in c["results"]:
                content = it.get("content") or ""
                key = hashlib.sha1(content.encode()).hexdigest()[:10]
                if key in seen:
                    continue
                seen.add(key)
                a_id = f"r{rid}-a{len(articles) + 1}"
                articles.append({
                    "article_id": a_id,
                    "content_sha1": key,
                    "title": it.get("title"),
                    "url": it.get("url"),
                    "sentences": [
                        {"sid": f"{a_id}-s{i + 1}", "text": s}
                        for i, s in enumerate(segments(content))
                    ],
                })
        packet.append({
            "row": rid,
            "question_zh": ds[rid]["question"],
            "target_companies": ds[rid]["company_universe"].split("|"),
            "tavily_tickers_used": sorted({(c["args"].get("ticker") or "").upper() for c in calls}),
            "articles": articles,
        })
    with open(out / "packet.jsonl", "w", encoding="utf-8") as f:
        for p in packet:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(out / "fixture_source_runs.json", "w", encoding="utf-8") as f:
        json.dump(source, f, ensure_ascii=False, indent=1)
    n_sent = sum(len(a["sentences"]) for p in packet for a in p["articles"])
    n_art = sum(len(p["articles"]) for p in packet)
    print(f"rows={len(packet)} articles={n_art} sentences={n_sent}")
    for p in packet:
        print(p["row"], len(p["articles"]), sum(len(a["sentences"]) for a in p["articles"]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
