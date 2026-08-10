"""Repo-anchored data path resolvers.

Import a resolver instead of hardcoding a ``data/...`` path. Each is
CWD-independent and overridable via its own env var.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"


def get_duckdb_path() -> Path:
    return Path(os.getenv("DUCKDB_PATH", str(DATA_DIR / "fundamentals.db")))


def get_sec_filings_html_dir() -> Path:
    return Path(os.getenv("SEC_FILINGS_HTML_DIR", str(DATA_DIR / "sec_filings_html")))


def get_sec_text_dir() -> Path:
    return Path(os.getenv("SEC_TEXT_DIR", str(DATA_DIR / "sec_text")))


def get_checkpoint_db_path() -> Path:
    return Path(os.getenv("CHECKPOINT_DB_PATH", str(DATA_DIR / "checkpoints.db")))
