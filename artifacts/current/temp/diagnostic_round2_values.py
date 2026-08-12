"""Read-only diagnostic (not a test) — prints concrete actual values for the
Round 2 Phase 2 verification report's Detail sections. All these facts are
already proven by exact-equality assertions in test_verification_round2_full.py;
this just surfaces the literal numbers for the report instead of re-deriving
them from "assertion passed."

Run with: PYTHONPATH=. python3 artifacts/current/temp/diagnostic_round2_values.py
"""

import json
from pathlib import Path

from backend.common.sec_core import FetchedFiling
from backend.ingestion.sec_text_pipeline import parser
from backend.ingestion.sec_text_pipeline.filing_store import LocalFilingStore
from backend.tests.ingestion.sec_text_pipeline.conftest import FakeTenK

PROBES = json.loads(
    Path(
        "backend/tests/ingestion/sec_text_pipeline/fixtures_detection_probes.json"
    ).read_text(encoding="utf-8")
)


def parse_probe(ticker, store):
    data = PROBES[ticker]
    degraded = data["section_item_attr"] == "missing"
    tenk = FakeTenK(
        sections_data={
            (f"Item {key.upper()}" if degraded else f"item_{key}"): {
                "item": "" if degraded else key,
                "text": text,
            }
            for key, text in data["sections"].items()
        },
        period_of_report=data["period_of_report"],
        filing_date=data["filing_date"],
    )
    bundle = FetchedFiling(
        tenk=tenk,
        accession_number=data["accession_number"],
        cik=data["cik"],
        company_name=data["company"],
        primary_document="primary.htm",
    )
    parser.fetch_filing_bundle = lambda *a, **k: bundle
    parser.fetch_filing_markdown = lambda *a, **k: "\n".join(data["heading_lines"])
    fiscal_year = int(data["period_of_report"][:4])
    return parser.parse_filing(ticker, fiscal_year=fiscal_year, store=store)


def get(filing, item):
    return next(i for i in filing.items if i.item == item)


store = LocalFilingStore(base_dir="/private/tmp/claude-501/-Users-dong-wyt-Documents-dev-projects-fin-lab-x-wt-text-fallback-detection/8920b4f9-ac0c-4b96-9c6d-975185110c20/scratchpad/round2_diag_store")

print("=== S-fallback-06 case2 / J-fallback-01: WMT 7A ===")
wmt = parse_probe("WMT", store)
wmt7a = get(wmt, "7a")
print(f"detection_source={wmt7a.detection_source!r} blocks={len(wmt7a.blocks)}")

print("\n=== S-fallback-07 step3: DIS 7 prelude length ===")
dis = parse_probe("DIS", store)
dis7 = get(dis, "7")
print(f"prelude_len={len(dis7.prelude)}")

print("\n=== S-fallback-08: full chain ===")
cat = parse_probe("CAT", store)
cat7 = get(cat, "7")
print(f"CAT 7: detection_source={cat7.detection_source!r} first2={[b.heading for b in cat7.blocks[:2]]}")

wmt1a = get(wmt, "1a")
print(f"WMT 1A: detection_source={wmt1a.detection_source!r} headings={[b.heading for b in wmt1a.blocks]}")

print(f"WMT 7A: detection_source={wmt7a.detection_source!r} blocks={len(wmt7a.blocks)}")

dis7a = get(dis, "7a")
print(f"DIS 7A: detection_source={dis7a.detection_source!r} blocks={len(dis7a.blocks)}")

msft = parse_probe("MSFT", store)
for key in ("1", "1a", "7", "7a"):
    item = get(msft, key)
    print(f"MSFT {key}: detection_source={item.detection_source!r} blocks={len(item.blocks)}")

print("\n=== S-fallback-10 / J-fallback-02: GE 1a FlatItem ===")
ge = parse_probe("GE", store)
ge1a = get(ge, "1a")
print(f"type={type(ge1a).__name__}")
raw = PROBES["GE"]["sections"]["1a"]
trimmed = parser._trim_section_text(raw, "1a")
print(f"trimmed_len={len(trimmed)} flat_text_len={len(ge1a.text)} strip_equal={ge1a.text.strip() == trimmed.strip()}")
