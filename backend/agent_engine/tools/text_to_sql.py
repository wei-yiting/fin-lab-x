"""text_to_sql: natural-language question → read-only DuckDB query over the fundamentals store.

The Orchestrator passes a self-contained English question. Inside the tool a fixed
generate → validate → execute → repair loop runs (ADR-0022):

    attempt 1..MAX_ATTEMPTS:
        LLM writes SQL from the schema prompt (+ earlier failed attempts)
        validate: exactly one SELECT statement (DuckDB's own parser)
        execute on a read-only, external-access-disabled connection
        error → feed the error text into the next attempt; rows → stop

Only errors are retried. An empty result is a valid answer and returns at once with
store coverage, so the loop never loosens a query until it "finds" something.
Infrastructure failures (missing database, LLM API errors) raise and surface through
the Orchestrator's tool-error middleware.
"""

import datetime as dt
import decimal
import functools
import math
import re
from pathlib import Path
from typing import Annotated, Any, Literal, NotRequired, TypedDict

import duckdb
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import InjectedToolCallId
from langgraph.config import get_stream_writer
from langgraph.constants import TAG_NOSTREAM
from pydantic import BaseModel, Field

from backend.common.data_paths import get_duckdb_path
from backend.common.errors import ConfigurationError, FinLabError

# Same model as the quant Orchestrator; moving this into the Workflow Profile config
# is tracked as a follow-up (DEV-226).
SQL_GENERATION_MODEL = "gpt-5.6-luna"
SQL_GENERATION_REASONING_EFFORT = "low"
MAX_ATTEMPTS = 3
MAX_ROWS = 50

# The only objects the LLM is shown. Raw financial tables are covered by the
# metrics views; SEC-only tables are empty until the SEC XBRL subsystem (DEV-225).
QUERYABLE_RELATIONS = (
    "companies",
    "market_valuations",
    "quarterly_metrics",
    "annual_metrics",
)
QUERYABLE_MACROS = ("period_metrics",)
# View columns copied from a base table inherit that table's column comment.
_VIEW_BASE_TABLES = {
    "quarterly_metrics": "quarterly_financials",
    "annual_metrics": "annual_financials",
}

_PROMPT_PATH = Path(__file__).with_name("text_to_sql_prompt.md")
_SQL_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_UNANSWERABLE_RE = re.compile(r"^\s*UNANSWERABLE:\s*(.+)$", re.MULTILINE)


class UnsafeSqlError(FinLabError):
    """Generated SQL is not exactly one read-only SELECT statement."""


class Attempt(TypedDict):
    sql: str
    error: str


class TextToSqlResult(TypedDict):
    status: Literal["ok", "no_rows", "failed"]
    question: str
    sql: str | None
    columns: list[str]
    rows: list[dict[str, Any]]
    truncated: bool
    attempts: list[Attempt]
    coverage: NotRequired[dict[str, Any]]


def validate_read_only_sql(sql: str) -> None:
    """Layer 1 of the read-only guard: DuckDB's parser must see one SELECT.

    PRAGMA/DESCRIBE/SUMMARIZE parse as SELECT and are harmless reads. Layers 2-3
    (read-only connection, external access disabled) live in ``_connect_read_only``.
    """
    with duckdb.connect() as parser:
        try:
            statements = parser.extract_statements(sql)
        except duckdb.Error as exc:
            raise UnsafeSqlError(f"SQL does not parse: {exc}") from exc
    if len(statements) != 1:
        raise UnsafeSqlError(
            f"Exactly one SQL statement is allowed, got {len(statements)}."
        )
    if statements[0].type != duckdb.StatementType.SELECT:
        raise UnsafeSqlError(
            f"Only a read-only SELECT is allowed, got {statements[0].type.name}."
        )


def _connect_read_only(db_path: Path) -> duckdb.DuckDBPyConnection:
    if not db_path.exists():
        raise ConfigurationError(
            "Fundamentals database not found; run "
            "`python -m backend.scripts.ingest_yfinance_fundamentals` first."
        )
    # external access off blocks read_csv/ATTACH/COPY/httpfs and cannot be
    # re-enabled by SQL while the connection lives.
    return duckdb.connect(
        str(db_path), read_only=True, config={"enable_external_access": False}
    )


def _to_json_value(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def run_read_only_query(
    db_path: Path, sql: str
) -> tuple[list[str], list[dict[str, Any]], bool]:
    """Validate and execute ``sql``; returns (columns, rows ≤ MAX_ROWS, truncated)."""
    validate_read_only_sql(sql)
    with _connect_read_only(db_path) as conn:
        cursor = conn.execute(sql)
        columns = [d[0] for d in cursor.description]
        fetched = cursor.fetchmany(MAX_ROWS + 1)
    rows = [
        {c: _to_json_value(v) for c, v in zip(columns, row, strict=True)}
        for row in fetched[:MAX_ROWS]
    ]
    return columns, rows, len(fetched) > MAX_ROWS


@functools.lru_cache(maxsize=4)
def build_schema_prompt(db_path: Path) -> str:
    """Render the LLM-visible schema from the database's own COMMENTs."""
    with _connect_read_only(db_path) as conn:
        comments = {
            (t, c): comment
            for t, c, comment in conn.execute(
                "SELECT table_name, column_name, comment FROM duckdb_columns()"
            ).fetchall()
        }
        blocks: list[str] = []
        for relation in QUERYABLE_RELATIONS:
            (relation_comment,) = conn.execute(
                "SELECT comment FROM duckdb_tables() WHERE table_name = $1"
                " UNION ALL SELECT comment FROM duckdb_views() WHERE view_name = $1",
                [relation],
            ).fetchone()
            columns = conn.execute(
                "SELECT column_name, data_type FROM duckdb_columns()"
                " WHERE table_name = $1 AND column_name <> 'updated_at'"
                " ORDER BY column_index",
                [relation],
            ).fetchall()
            base = _VIEW_BASE_TABLES.get(relation)
            lines = []
            for i, (name, data_type) in enumerate(columns):
                comment = comments.get((relation, name)) or comments.get((base, name))
                separator = "," if i < len(columns) - 1 else ""
                lines.append(
                    f"    {name} {data_type}{separator}"
                    + (f" -- {comment}" if comment else "")
                )
            blocks.append(
                f"-- {relation_comment}\nCREATE TABLE {relation} (\n"
                + "\n".join(lines)
                + "\n);"
            )
        for macro in QUERYABLE_MACROS:
            (macro_comment,) = conn.execute(
                "SELECT comment FROM duckdb_functions() WHERE function_name = $1",
                [macro],
            ).fetchone()
            output = conn.execute(
                f"DESCRIBE SELECT * FROM {macro}(2000, 1, 1)"
            ).fetchall()
            blocks.append(
                f"-- TABLE MACRO {macro}(cal_year INTEGER, q_from INTEGER, q_to INTEGER)\n"
                f"-- {macro_comment}\n"
                f"-- Output columns: {', '.join(row[0] for row in output)}"
            )
    return "\n\n".join(blocks)


def store_coverage(db_path: Path) -> dict[str, Any]:
    """What the store holds, attached to no_rows / failed results."""
    with _connect_read_only(db_path) as conn:
        tickers = [
            r[0]
            for r in conn.execute("SELECT ticker FROM companies ORDER BY 1").fetchall()
        ]
        q_min, q_max = conn.execute(
            "SELECT min(period_end), max(period_end) FROM quarterly_metrics"
        ).fetchone()
        fy_min, fy_max = conn.execute(
            "SELECT min(fiscal_year), max(fiscal_year) FROM annual_metrics"
        ).fetchone()
        (as_of,) = conn.execute(
            "SELECT max(as_of_date) FROM market_valuations"
        ).fetchone()
    return {
        "tickers": tickers,
        "quarterly_period_end_range": [_to_json_value(q_min), _to_json_value(q_max)],
        "annual_fiscal_year_range": [fy_min, fy_max],
        "valuations_as_of": _to_json_value(as_of),
    }


def get_sql_model() -> BaseChatModel:
    # Test-patching seam: tests replace this factory with a scripted fake model.
    return init_chat_model(
        SQL_GENERATION_MODEL,
        model_provider="openai",
        reasoning={"effort": SQL_GENERATION_REASONING_EFFORT},
        use_responses_api=True,
    )


def _sql_messages(question: str, schema: str, failed: list[Attempt]) -> list[Any]:
    system = _PROMPT_PATH.read_text().replace("{schema}", schema)
    human = f"Question: {question}"
    for i, attempt in enumerate(failed, start=1):
        human += (
            f"\n\nFailed attempt {i}:\n```sql\n{attempt['sql']}\n```\n"
            f"Error: {attempt['error']}"
        )
    return [SystemMessage(system), HumanMessage(human)]


def _extract_sql(text: str) -> str:
    match = _SQL_FENCE_RE.search(text)
    return (match.group(1) if match else text).strip().rstrip(";").strip()


def answer_question(
    question: str,
    *,
    db_path: Path | None = None,
    config: RunnableConfig | None = None,
    on_attempt: Any = None,
) -> TextToSqlResult:
    """Run the fixed repair loop for one question (the evaluable unit, ADR-0022)."""
    path = db_path or get_duckdb_path()
    schema = build_schema_prompt(path)
    model = get_sql_model()
    failed: list[Attempt] = []

    def attempt(_: Any, config: RunnableConfig) -> dict[str, Any]:
        # nostream: the SQL-writing tokens must not leak into the user-visible answer
        # stream (LangGraph streams every chat model run that inherits callbacks).
        reply = model.with_config(tags=[TAG_NOSTREAM]).invoke(
            _sql_messages(question, schema, failed), config=config
        )
        unanswerable = _UNANSWERABLE_RE.search(reply.text)
        if unanswerable:
            return {"unanswerable": unanswerable.group(1).strip()}
        sql = _extract_sql(reply.text)
        try:
            columns, rows, truncated = run_read_only_query(path, sql)
        except (UnsafeSqlError, duckdb.Error) as exc:
            return {"sql": sql, "error": str(exc)}
        return {"sql": sql, "columns": columns, "rows": rows, "truncated": truncated}

    for number in range(1, MAX_ATTEMPTS + 1):
        if on_attempt:
            on_attempt(number)
        outcome = (
            RunnableLambda(attempt)
            .with_config(run_name=f"text_to_sql_attempt_{number}")
            .invoke(question, config=config)
        )
        if "unanswerable" in outcome:
            failed.append(
                {"sql": "", "error": f"UNANSWERABLE: {outcome['unanswerable']}"}
            )
            break
        if "error" in outcome:
            failed.append({"sql": outcome["sql"], "error": outcome["error"]})
            continue
        result: TextToSqlResult = {
            "status": "ok" if outcome["rows"] else "no_rows",
            "question": question,
            "sql": outcome["sql"],
            "columns": outcome["columns"],
            "rows": outcome["rows"],
            "truncated": outcome["truncated"],
            "attempts": failed,
        }
        if not outcome["rows"]:
            result["coverage"] = store_coverage(path)
        return result

    return {
        "status": "failed",
        "question": question,
        "sql": failed[-1]["sql"] or None,
        "columns": [],
        "rows": [],
        "truncated": False,
        "attempts": failed,
        "coverage": store_coverage(path),
    }


class TextToSqlInput(BaseModel):
    """Input schema for the text_to_sql tool."""

    question: str = Field(
        ...,
        description=(
            "One self-contained question in English, with tickers and the period "
            "spelled out (resolve follow-ups like 'and last year?' before calling). "
            "E.g. 'Gross margin of every covered company in its latest reported quarter'."
        ),
    )


@tool("text_to_sql", args_schema=TextToSqlInput)
def text_to_sql(
    question: str,
    config: RunnableConfig,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> TextToSqlResult:
    """Answer a structured financial-data question from the FinLab-X fundamentals store (DuckDB, sourced from yfinance) by generating and running a read-only SQL query.

    Covers the Ticker universe only (~23 large US companies: AAPL MSFT GOOGL AMZN NVDA TSLA META JPM V MA WMT COST KO PEP JNJ XOM DIS NFLX INTC NKE CRM BRK.B CAT): quarterly (~5 latest) and annual (~4 fiscal years) income statement, balance sheet and cash flow; derived ratios (gross/operating/net/FCF margin, R&D intensity, debt-to-equity, current ratio); calendar-quarter windows; valuation snapshot (P/E, forward P/E, P/B, P/S, EV/EBITDA, PEG, dividend yield, beta, market cap). One call can compare many companies and periods.

    Returns status ok | no_rows | failed, the SQL that ran, rows (≤50), and failed attempts. no_rows/failed include the store's coverage. Not for real-time prices or 10-K text.
    """
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None

    def report(number: int) -> None:
        if writer:
            writer(
                {
                    "status": "generating_sql",
                    "message": f"Writing SQL (attempt {number}/{MAX_ATTEMPTS})...",
                    "toolName": "text_to_sql",
                    "toolCallId": tool_call_id,
                }
            )

    return answer_question(question, config=config, on_attempt=report)
