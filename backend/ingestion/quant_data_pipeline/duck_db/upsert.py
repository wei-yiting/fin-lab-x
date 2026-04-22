from typing import TypeVar

import pandas as pd
from duckdb import DuckDBPyConnection
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def upsert_rows(
    conn: DuckDBPyConnection,
    table: str,
    pk_columns: list[str],
    rows: list[T],
) -> int:
    if not rows:
        return 0
    columns = list(type(rows[0]).model_fields.keys())
    assert "updated_at" not in columns, (
        "Row DTO must not declare updated_at; it is managed by upsert_rows()"
    )
    non_pk = [c for c in columns if c not in pk_columns]
    set_clause = ", ".join(
        [f"{c} = EXCLUDED.{c}" for c in non_pk]
        + ["updated_at = now()"]
    )
    sql = (
        f"INSERT INTO {table} ({', '.join(columns)}) "
        f"SELECT {', '.join(columns)} FROM staging "
        f"ON CONFLICT ({', '.join(pk_columns)}) DO UPDATE SET {set_clause}"
    )
    df = pd.DataFrame([r.model_dump() for r in rows])
    conn.register("staging", df)
    try:
        conn.execute(sql)
    finally:
        conn.unregister("staging")
    return len(rows)
