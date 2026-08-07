"""Repo-anchored data path configuration — single definition point.

Every consumer that needs a data directory or file imports its resolver from
here instead of hardcoding a CWD-relative default. ``REPO_ROOT`` anchors off
this module's own file location, not the process's current working
directory, so the resolved paths are identical whether the process starts
from the repo root, a subdirectory, /tmp, an IDE run configuration, or cron.

Each resolver re-reads its env var on every call (mirroring
``fundamentals_pipeline.duck_db.connection.get_connection``'s existing
pattern) so tests can ``monkeypatch.setenv`` and see the override take
effect without reloading the module.
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
