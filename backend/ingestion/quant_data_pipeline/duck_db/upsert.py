from typing import TypeVar
from uuid import uuid4

import pandas as pd
from duckdb import DuckDBPyConnection
from pydantic import BaseModel

_T = TypeVar("_T", bound=BaseModel)


def upsert_rows(
    conn: DuckDBPyConnection,
    table: str,
    pk_columns: list[str],
    rows: list[_T],
) -> int:
    if not rows:
        return 0
    columns = list(type(rows[0]).model_fields.keys())
    if "updated_at" in columns:
        raise ValueError(
            "Row DTO must not declare updated_at; it is managed by upsert_rows()"
        )
    non_pk = [c for c in columns if c not in pk_columns]
    # DuckDB's binder parses bare CURRENT_TIMESTAMP as a column reference inside
    # ON CONFLICT DO UPDATE SET, so use now() (CURRENT_TIMESTAMP() doesn't exist).
    set_clause = ", ".join(
        [f"{c} = EXCLUDED.{c}" for c in non_pk]
        + ["updated_at = now()"]
    )
    staging_name = f"__quant_upsert_staging_{uuid4().hex[:8]}"
    sql = (
        f"INSERT INTO {table} ({', '.join(columns)}) "
        f"SELECT {', '.join(columns)} FROM {staging_name} "
        f"ON CONFLICT ({', '.join(pk_columns)}) DO UPDATE SET {set_clause}"
    )
    df = pd.DataFrame([r.model_dump() for r in rows])
    conn.register(staging_name, df)
    try:
        conn.execute(sql)
    finally:
        conn.unregister(staging_name)
    return len(rows)
