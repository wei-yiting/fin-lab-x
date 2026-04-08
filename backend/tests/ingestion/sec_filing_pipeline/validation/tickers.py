"""Ticker catalogues for the validation harness.

EXISTING_23: Tickers already covered by R-13 hard-gate baseline.
DISCOVERY_5: Stratified random sample (seed=408) from the discovery 47 catalog,
             one per sector cluster, used for cross-vendor edge-case smoke.
"""

from __future__ import annotations

CLASS_A_12 = (
    "NVDA",
    "AAPL",
    "GOOGL",
    "AMZN",
    "MSFT",
    "TSLA",
    "CRM",
    "KO",
    "BA",
    "JNJ",
    "JPM",
    "XOM",
)

CLASS_B_10 = (
    "BRK.B",
    "UNH",
    "CAT",
    "HD",
    "T",
    "DIS",
    "BAC",
    "AMT",
    "NEE",
    "WMT",
)

CLASS_C_1 = ("INTC",)

EXISTING_23 = CLASS_A_12 + CLASS_B_10 + CLASS_C_1

# Stratified random sample, seed=408 — 1 ticker per sector cluster.
# Reproducible via tests/ingestion/sec_filing_pipeline/validation/test_validation_harness.py.
DISCOVERY_5 = (
    "PG",     # Staples
    "USB",    # Banks (regional)
    "ALL",    # Insurance
    "BRK.A",  # Berkshire (annual letter blended into 10-K)
    "SLB",    # Energy / oilfield services
)

ALL_28 = EXISTING_23 + DISCOVERY_5


def resolve_ticker_set(name: str) -> tuple[str, ...]:
    """Resolve a CLI ticker-set name to a tuple of tickers.

    Accepts well-known names ('existing23', 'discovery5', 'all28', 'class_a',
    'class_b', 'class_c') or a comma-separated literal list ('NVDA,AAPL').
    """
    name = name.strip()
    table = {
        "existing23": EXISTING_23,
        "discovery5": DISCOVERY_5,
        "all28": ALL_28,
        "class_a": CLASS_A_12,
        "class_b": CLASS_B_10,
        "class_c": CLASS_C_1,
    }
    if name in table:
        return table[name]
    if "," in name:
        return tuple(t.strip() for t in name.split(",") if t.strip())
    # Single ticker
    return (name,)
