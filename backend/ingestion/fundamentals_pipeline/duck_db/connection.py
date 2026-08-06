from pathlib import Path

import duckdb
from duckdb import DuckDBPyConnection

from backend.common.config import get_duckdb_path
from backend.ingestion.fundamentals_pipeline.errors import SchemaError

_SCHEMA_SQL_PATH = Path(__file__).parent / "schema.sql"


def get_connection(
    db_path: str | None = None,
    *,
    ensure_schema: bool = True,
) -> DuckDBPyConnection:
    path = db_path or str(get_duckdb_path())
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(path)
    if ensure_schema:
        if not _SCHEMA_SQL_PATH.exists():
            raise SchemaError(f"schema.sql missing at {_SCHEMA_SQL_PATH}")
        try:
            conn.execute(_SCHEMA_SQL_PATH.read_text())
        except duckdb.Error as exc:
            raise SchemaError("Failed to apply schema.sql") from exc
    return conn
