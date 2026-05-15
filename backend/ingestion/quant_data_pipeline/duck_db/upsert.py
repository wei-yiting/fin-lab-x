from collections.abc import Iterable
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
    *,
    coalesce_columns: Iterable[str] | None = None,
) -> int:
    """Bulk-upsert Pydantic row DTOs into a table with column-level merge.

    The DTO defines which columns this call writes; the SQL ``DO UPDATE SET``
    clause lists only those columns, so columns owned by other subsystems on
    the same row survive untouched. ``updated_at`` is managed by this helper
    (DTOs must not declare it).

    Args:
        conn: Open DuckDB connection with schema applied.
        table: Target table name.
        pk_columns: Columns forming the conflict target.
        rows: Same-typed Pydantic DTOs; ``[]`` short-circuits to 0.
        coalesce_columns: Optional columns whose UPDATE clause uses
            ``COALESCE(EXCLUDED.col, <table>.col)`` instead of plain
            ``EXCLUDED.col``. A ``None`` incoming value preserves the
            already-stored value, which protects against transient upstream
            hiccups (e.g. yfinance returning NaN mid-day). Default ``None``
            keeps the current overwrite semantics for all non-PK columns.
            Empty iterables are treated the same as ``None``. Must not
            include any PK column.

    Returns:
        Number of input rows processed (not DB-reported affected rows).

    Raises:
        ValueError: DTO declares ``updated_at`` (helper-managed column),
            ``coalesce_columns`` includes a PK column, or ``coalesce_columns``
            references a name not present on the row DTO.
    """
    cols_to_coalesce = set(coalesce_columns) if coalesce_columns else set()
    pk_in_coalesce = cols_to_coalesce & set(pk_columns)
    if pk_in_coalesce:
        raise ValueError("coalesce_columns must not include PK columns")

    if not rows:
        return 0
    # DTO drives the column set: same-typed DTOs are assumed, so the first
    # row's class determines which columns participate in INSERT and the
    # DO UPDATE SET clause.
    columns = list(type(rows[0]).model_fields.keys())
    if "updated_at" in columns:
        raise ValueError(
            "Row DTO must not declare updated_at; it is managed by upsert_rows()"
        )

    known_columns = set(columns)
    for name in cols_to_coalesce:
        if name not in known_columns:
            raise ValueError(f"coalesce_columns contains unknown column: {name}")

    non_pk = [c for c in columns if c not in pk_columns]
    # DuckDB's binder parses bare CURRENT_TIMESTAMP as a column reference inside
    # ON CONFLICT DO UPDATE SET, so use now() (CURRENT_TIMESTAMP() doesn't exist).
    set_clause = ", ".join(
        [
            f"{c} = COALESCE(EXCLUDED.{c}, {table}.{c})"
            if c in cols_to_coalesce
            else f"{c} = EXCLUDED.{c}"
            for c in non_pk
        ]
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
