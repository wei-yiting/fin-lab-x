"""Tests for the text_to_sql tool: read-only guard, repair loop, return contract."""

import json
from datetime import date
from pathlib import Path

import duckdb
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langgraph.constants import TAG_NOSTREAM

from backend.agent_engine.tools import text_to_sql as tts
from backend.common.errors import ConfigurationError
from backend.ingestion.fundamentals_pipeline.duck_db.connection import get_connection
from backend.ingestion.fundamentals_pipeline.duck_db.row_models import (
    CompanyRow,
    YFinanceQuarterlyRow,
)
from backend.ingestion.fundamentals_pipeline.duck_db.upsert import upsert_rows

GOOD_SQL = "SELECT ticker, total_revenue_usd FROM quarterly_metrics ORDER BY ticker"


@pytest.fixture
def store(tmp_path) -> Path:
    path = tmp_path / "fundamentals.db"
    with get_connection(str(path)) as conn:
        upsert_rows(
            conn,
            "companies",
            ["ticker"],
            [
                CompanyRow(
                    ticker="AAA", company_name="A", fy_end_month=12, fy_end_day=31
                )
            ],
        )
        upsert_rows(
            conn,
            "quarterly_financials",
            ["ticker", "fiscal_year", "fiscal_quarter"],
            [
                YFinanceQuarterlyRow(
                    ticker="AAA",
                    fiscal_year=2026,
                    fiscal_quarter=2,
                    period_end=date(2026, 6, 30),
                    total_revenue_usd=100,
                )
            ],
        )
    return path


def _script(monkeypatch, *replies: str) -> None:
    """Make the SQL model answer with ``replies`` in order (and fail if asked more)."""
    model = GenericFakeChatModel(messages=iter([AIMessage(r) for r in replies]))
    monkeypatch.setattr(tts, "get_sql_model", lambda: model)


def _fenced(sql: str) -> str:
    return f"```sql\n{sql}\n```"


# --- Layer 1: parser guard ---------------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1",
        "WITH x AS (SELECT 1 AS a) SELECT a FROM x",
        "SELECT * FROM period_metrics(2026, 1, 3)",
    ],
)
def test_guard_accepts_single_select(sql):
    tts.validate_read_only_sql(sql)


@pytest.mark.parametrize(
    "sql, fragment",
    [
        ("INSERT INTO companies VALUES ('X')", "INSERT"),
        ("DROP TABLE companies", "DROP"),
        ("COPY companies TO 'out.csv'", "COPY"),
        ("ATTACH 'other.db'", "ATTACH"),
        ("SET enable_external_access = true", "SET"),
        ("SELECT 1; DROP TABLE companies", "Exactly one"),
        ("SELEC 1", "does not parse"),
    ],
)
def test_guard_rejects_everything_else(sql, fragment):
    with pytest.raises(tts.UnsafeSqlError, match=fragment):
        tts.validate_read_only_sql(sql)


# --- Layers 2-3: engine-level read-only connection ---------------------------


def test_select_cannot_read_local_files(store):
    with pytest.raises(duckdb.PermissionException):
        tts.run_read_only_query(store, "SELECT * FROM read_csv('/etc/passwd')")


def test_connection_rejects_writes_and_reenabling_external_access(store):
    with tts._connect_read_only(store) as conn:
        with pytest.raises(duckdb.Error):
            conn.execute("DELETE FROM companies")
        with pytest.raises(duckdb.InvalidInputException):
            conn.execute("SET enable_external_access = true")


def test_rows_are_capped(store):
    columns, rows, truncated = tts.run_read_only_query(
        store, "SELECT * FROM range(100) AS t(n)"
    )
    assert columns == ["n"]
    assert len(rows) == tts.MAX_ROWS
    assert truncated is True


def test_missing_database_is_an_infrastructure_error(tmp_path):
    with pytest.raises(ConfigurationError):
        tts.answer_question("anything", db_path=tmp_path / "absent.db")


# --- Repair loop ---------------------------------------------------------------


def test_error_is_fed_back_and_repaired(store, monkeypatch):
    _script(
        monkeypatch,
        _fenced("SELECT ticker, revenue FROM quarterly_metrics"),
        _fenced(GOOD_SQL),
    )
    result = tts.answer_question("Revenue?", db_path=store)
    assert result["status"] == "ok"
    assert result["sql"] == GOOD_SQL
    assert result["rows"] == [{"ticker": "AAA", "total_revenue_usd": 100}]
    assert len(result["attempts"]) == 1
    assert "revenue" in result["attempts"][0]["error"]
    assert "coverage" not in result


def test_unsafe_sql_is_retried_like_an_error(store, monkeypatch):
    _script(monkeypatch, _fenced("DROP TABLE companies"), _fenced(GOOD_SQL))
    result = tts.answer_question("Revenue?", db_path=store)
    assert result["status"] == "ok"
    assert "Only a read-only SELECT" in result["attempts"][0]["error"]


def test_empty_result_is_not_retried_and_carries_coverage(store, monkeypatch):
    # A single scripted reply: a retry would exhaust the fake model and raise.
    _script(monkeypatch, _fenced("SELECT * FROM companies WHERE ticker = 'TSM'"))
    result = tts.answer_question("TSMC revenue?", db_path=store)
    assert result["status"] == "no_rows"
    assert result["attempts"] == []
    assert result["coverage"] == {
        "tickers": ["AAA"],
        "quarterly_period_end_range": ["2026-06-30", "2026-06-30"],
        "annual_fiscal_year_range": [None, None],
        "valuations_as_of": None,
    }


def test_gives_up_after_max_attempts(store, monkeypatch):
    _script(monkeypatch, *[_fenced("SELECT nope FROM companies")] * tts.MAX_ATTEMPTS)
    result = tts.answer_question("?", db_path=store)
    assert result["status"] == "failed"
    assert len(result["attempts"]) == tts.MAX_ATTEMPTS
    assert result["sql"] == "SELECT nope FROM companies"
    assert result["rows"] == []
    assert "coverage" in result


def test_unanswerable_stops_without_sql(store, monkeypatch):
    _script(monkeypatch, "UNANSWERABLE: employee count is not in the schema")
    result = tts.answer_question("How many employees?", db_path=store)
    assert result["status"] == "failed"
    assert result["sql"] is None
    assert result["attempts"] == [
        {"sql": "", "error": "UNANSWERABLE: employee count is not in the schema"}
    ]


# --- Schema prompt and tool surface ------------------------------------------


def test_schema_prompt_shows_only_queryable_objects(store):
    schema = tts.build_schema_prompt(store)
    for relation in tts.QUERYABLE_RELATIONS:
        assert f"CREATE TABLE {relation} (" in schema
    assert "TABLE MACRO period_metrics(" in schema
    assert "CREATE TABLE quarterly_financials" not in schema
    assert "segment_financials" not in schema
    # View columns inherit their base-table comments.
    assert "total_revenue_usd BIGINT, -- Total revenue in USD" in schema


def test_tool_returns_contract_through_tool_call(store, monkeypatch):
    monkeypatch.setattr(tts, "get_duckdb_path", lambda: store)
    _script(monkeypatch, _fenced(GOOD_SQL))
    message = tts.text_to_sql.invoke(
        {
            "args": {"question": "Revenue of AAA?"},
            "name": "text_to_sql",
            "type": "tool_call",
            "id": "call-1",
        }
    )
    payload = json.loads(message.content)
    assert payload["status"] == "ok"
    assert payload["sql"] == GOOD_SQL
    assert set(payload) == {
        "status",
        "question",
        "sql",
        "columns",
        "rows",
        "truncated",
        "attempts",
        "citation_id",
        "tables",
        "derivations",
    }
    assert payload["citation_id"] == "sql://call-1"


class _TagRecorder(BaseCallbackHandler):
    def __init__(self) -> None:
        self.chat_model_tags: list[list[str]] = []

    def on_chat_model_start(self, serialized, messages, *, tags=None, **kwargs):
        self.chat_model_tags.append(list(tags or []))


def test_sql_generation_is_traced_but_never_streamed(store, monkeypatch):
    """The inner LLM inherits the caller's callbacks (nested trace) but carries
    LangGraph's nostream tag so its SQL tokens never reach the answer stream."""
    _script(monkeypatch, _fenced(GOOD_SQL))
    recorder = _TagRecorder()
    tts.answer_question("Revenue?", db_path=store, config={"callbacks": [recorder]})
    assert recorder.chat_model_tags and all(
        TAG_NOSTREAM in tags for tags in recorder.chat_model_tags
    )


def test_derivations_come_from_view_ddl_and_need_their_inputs_selected():
    selected = ["ticker", "gross_margin_pct", "gross_profit_usd", "total_revenue_usd"]
    assert tts.derivations_for(selected) == [
        {
            "column": "gross_margin_pct",
            "expression": "gross_profit_usd / total_revenue_usd * 100",
            "inputs": ["gross_profit_usd", "total_revenue_usd"],
        }
    ]
    assert tts.derivations_for(["ticker", "gross_margin_pct"]) == []


def test_relations_in_lists_only_queryable_objects_once():
    sql = (
        "SELECT * FROM annual_metrics a JOIN companies c USING (ticker) "
        "JOIN annual_metrics b USING (ticker) WHERE x IN (SELECT 1 FROM duckdb_tables())"
    )
    assert tts.relations_in(sql) == ["annual_metrics", "companies"]
