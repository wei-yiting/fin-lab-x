def test_quarterly_annual_columns_have_identical_comments(tmp_duckdb):
    rows = tmp_duckdb.execute("""
        SELECT table_name, column_name, comment
        FROM duckdb_columns()
        WHERE table_name IN ('quarterly_financials','annual_financials')
    """).fetchall()
    by_table: dict[str, dict[str, str]] = {}
    for table, col, comment in rows:
        by_table.setdefault(table, {})[col] = comment or ""

    q = by_table["quarterly_financials"]
    a = by_table["annual_financials"]
    shared = (set(q) & set(a)) - {"fiscal_quarter"}
    mismatches = [
        (c, q[c], a[c]) for c in sorted(shared) if q[c] != a[c]
    ]
    assert not mismatches, (
        "COMMENT drift between quarterly_financials and annual_financials:\n"
        + "\n".join(f"- {c}\n  Q: {qc!r}\n  A: {ac!r}" for c, qc, ac in mismatches)
    )


def test_every_column_has_a_comment(tmp_duckdb):
    quant_tables = (
        'companies', 'market_valuations',
        'quarterly_financials', 'annual_financials',
        'segment_financials', 'geographic_revenue',
        'customer_concentration', 'ingestion_runs',
    )
    rows = tmp_duckdb.execute(
        f"""
        SELECT table_name, column_name, comment
        FROM duckdb_columns()
        WHERE table_name IN {quant_tables}
        """
    ).fetchall()
    missing = [
        (table, col) for table, col, comment in rows
        if comment is None or comment.strip() == ""
    ]
    assert not missing, (
        "Columns missing COMMENT ON COLUMN:\n"
        + "\n".join(f"- {t}.{c}" for t, c in missing)
    )


def test_quarterly_annual_full_schema_mirror(tmp_duckdb):
    """
    quarterly_financials and annual_financials must be identical in every respect
    (column name, type, nullability, default, and column order) except fiscal_quarter,
    which only exists in quarterly_financials.
    """
    rows = tmp_duckdb.execute(
        """
        SELECT table_name, column_name, column_index, data_type, is_nullable, column_default
        FROM duckdb_columns()
        WHERE table_name IN ('quarterly_financials', 'annual_financials')
        ORDER BY table_name, column_index
        """
    ).fetchall()

    q: list[tuple] = []  # [(name, dtype, nullable, default), ...]
    a: list[tuple] = []
    for table, col, _idx, dtype, nullable, default in rows:
        meta = (col, dtype, nullable, default)
        if table == "quarterly_financials":
            q.append(meta)
        else:
            a.append(meta)

    # Only allowed asymmetry: fiscal_quarter exists in quarterly, not annual.
    assert any(col == "fiscal_quarter" for col, *_ in q), (
        "quarterly_financials must declare fiscal_quarter"
    )
    assert not any(col == "fiscal_quarter" for col, *_ in a), (
        "annual_financials must not declare fiscal_quarter"
    )

    q_without_fq = [m for m in q if m[0] != "fiscal_quarter"]

    assert [m[0] for m in q_without_fq] == [m[0] for m in a], (
        "Column name list (with fiscal_quarter removed from quarterly) must be "
        "identical between quarterly_financials and annual_financials, "
        "preserving column order."
    )

    mismatches = [
        (qm, am) for qm, am in zip(q_without_fq, a, strict=True) if qm != am
    ]
    assert not mismatches, (
        "Column metadata drift (type/nullable/default) between quarterly and annual:\n"
        + "\n".join(f"- Q: {qm}\n  A: {am}" for qm, am in mismatches)
    )
