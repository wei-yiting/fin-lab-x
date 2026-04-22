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
    (column name, type, nullability, default) except fiscal_quarter, which only
    exists in quarterly_financials.
    """
    rows = tmp_duckdb.execute(
        """
        SELECT table_name, column_name, data_type, is_nullable, column_default
        FROM duckdb_columns()
        WHERE table_name IN ('quarterly_financials', 'annual_financials')
        """
    ).fetchall()
    by_table: dict[str, dict[str, tuple]] = {}
    for table, col, dtype, nullable, default in rows:
        by_table.setdefault(table, {})[col] = (dtype, nullable, default)

    q = by_table["quarterly_financials"]
    a = by_table["annual_financials"]

    # fiscal_quarter is the only allowed asymmetry
    assert "fiscal_quarter" in q
    assert "fiscal_quarter" not in a

    shared = (set(q) & set(a))
    mismatches = [
        (col, q[col], a[col]) for col in sorted(shared) if q[col] != a[col]
    ]
    assert not mismatches, (
        "Schema mirror drift (type/nullable/default) between quarterly and annual:\n"
        + "\n".join(
            f"- {col}\n  Q: {qv}\n  A: {av}" for col, qv, av in mismatches
        )
    )
