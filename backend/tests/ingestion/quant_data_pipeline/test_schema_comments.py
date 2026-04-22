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
