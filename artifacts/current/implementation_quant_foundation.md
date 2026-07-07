# Implementation Plan: Quant Data Pipeline Foundation Layer

> Design Reference: [design_quant_foundation.md](./design_quant_foundation.md) — 上位契約 [design_master.md](./design_master.md) §5–§7、§10。
>
> Planning Context: 本 PR 建立 yfinance / SEC XBRL 兩條子系統 pipeline 共用的 infrastructure：DuckDB connection、`schema.sql`（8 表 + 全欄位 `COMMENT`）、5 個 Pydantic row DTO、`upsert_rows()` / `normalize_fiscal_period()` / `ingestion_run()` / `with_retry()` / universe loader、error taxonomy、以及把既有 `sec_dense_pipeline/tracing.py` lift 到 `backend/utils/span_tracing.py` 做跨 pipeline 共用。不含任何 fetcher / transformer / CLI。

**Goal:** 建齊 quant data pipeline 共用基礎層，使後續 yfinance / SEC XBRL PR 只需專注各自 fetch / transform 邏輯。

**Architecture / Key Decisions:**
- `backend/ingestion/quant_data_pipeline/` 新 package，與既有 `sec_filing_pipeline` / `sec_dense_pipeline` 平行，**錯誤類別與 tracing policy 不共用繼承樹**（Design Master §7.6、§7.8）。
- `schema.sql` 手寫單檔（design §3.2 決策），用 pytest `test_schema_comments.py` 守 quarterly ↔ annual COMMENT mirror，不走 build script。
- `upsert_rows()` 採顯式欄位列表 SQL（design §5.2.2 方案 A），audit log self-explanatory 勝過簡潔。
- `traced_span()` **file-move**：從 `sec_dense_pipeline/tracing.py` 搬到 `backend/utils/span_tracing.py`（跨 pipeline 共用），連動更新 `retriever.py`、`vectorizer.py` 2 行 import。

**Tech Stack:** Python 3.11+, DuckDB (new dep), Pydantic v2, pandas (new dep), PyYAML, Langfuse (既有), pytest, `uv`。

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
| ---------- | ------- | ------ | ----------------- | ----- |
| duckdb | latest stable | Context7 `/duckdb/duckdb-python` | `con.register(name, df)` 註冊 pandas DataFrame 為 view；`con.unregister(name)` cleanup；`con.execute(sql)` 支援單字串多 statements；`ON CONFLICT ... DO UPDATE SET col = EXCLUDED.col` 語法 | DuckDB ≥0.9 內建 `ON CONFLICT`；register 是 zero-copy Arrow scan |
| pandas | any recent | Already transitive dep via other tooling; DuckDB 官方推薦 DataFrame bridge | `pd.DataFrame([dto.model_dump() for dto in rows])` 產 staging df | 用於 upsert helper 的 DataFrame 中介 |
| pydantic | ≥2.0（已在 pyproject）| pydantic v2 docs | `BaseModel.model_fields` 取 column list；`BaseModel.model_dump()` 產 dict | 已在 pyproject |
| pyyaml | ≥6.0.2（已在 pyproject）| 既有使用 | `yaml.safe_load(f)` | 已在 pyproject |
| langfuse | ≥4.0（已在 pyproject）| 既有 `sec_dense_pipeline/tracing.py` 實戰 | `langfuse.get_client().start_as_current_observation(name=...)` context manager；`_NoOpSpan.update()` 兼容 shape | file move，不重寫；已有 `uv.lock` 固定 |
| opentelemetry-api | 既有 transitive via langfuse | 既有 tracing.py | `otel_trace.get_current_span().get_span_context().is_valid` | 已透過 langfuse 4.x 帶入 |

**新增 package（本 PR）**：`duckdb`、`pandas` 進 `pyproject.toml` `[project.dependencies]`。其餘已存在。

## Constraints

- **Single-writer**：DuckDB 檔案鎖，foundation 不做 cross-process coordination（Design Master §12.1）。
- **Schema mirror 守護**：`quarterly_financials` ↔ `annual_financials` 共用欄位的 `COMMENT` 必須字對字一致（`fiscal_quarter` 為合法例外），違反 → `test_schema_comments.py` fail。
- **不在 scope**：任何 fetcher、transformer、CLI `__main__.py`、Alembic migration、`data/quant.db` seeding、SEC-only DTO（見 design §1 Out-of-Scope）。
- **不要動**：`sec_filing_pipeline/`（v2 RAG pipeline 既有）、`sec_dense_pipeline/collection_schema.py` / `retriever.py` / `vectorizer.py` 的邏輯（只改 2 行 import 到新 tracing 路徑）。
- **Language policy**：Plan 與 artifact 用繁中 + 英文術語；`README.md` 與 code comment 用英文（memory `feedback_readme_language.md`）。
- **套件管理**：一律 `uv`（memory `feedback_use_uv.md`），不用 `pip` / `poetry`。

---

## File Plan

| Operation | Path | Purpose |
| --------- | ---- | ------- |
| Update | `pyproject.toml` | 新增 `duckdb` 與 `pandas` runtime deps |
| Update | `.gitignore` | 加 `data/*.duckdb`、`data/*.db` rules |
| Create | `backend/utils/__init__.py` | 新 package |
| Create | `backend/utils/span_tracing.py` | lift from `sec_dense_pipeline/tracing.py`（file move，內容不變）|
| Delete | `backend/ingestion/sec_dense_pipeline/tracing.py` | 已 lift |
| Update | `backend/ingestion/sec_dense_pipeline/retriever.py` | import 改為 `backend.utils.span_tracing` |
| Update | `backend/ingestion/sec_dense_pipeline/vectorizer.py` | import 改為 `backend.utils.span_tracing` |
| Create | `backend/ingestion/quant_data_pipeline/__init__.py` | package root |
| Create | `backend/ingestion/quant_data_pipeline/README.md` | ships-with-code 文件（English）|
| Create | `backend/ingestion/quant_data_pipeline/config/ticker_universe.yaml` | canonical 10-ticker list |
| Create | `backend/ingestion/quant_data_pipeline/duck_db/__init__.py` | sub-package |
| Create | `backend/ingestion/quant_data_pipeline/duck_db/schema.sql` | 8 表 DDL + 全欄位 COMMENT |
| Create | `backend/ingestion/quant_data_pipeline/duck_db/connection.py` | `get_connection()` |
| Create | `backend/ingestion/quant_data_pipeline/duck_db/row_models.py` | 5 Pydantic DTO |
| Create | `backend/ingestion/quant_data_pipeline/duck_db/upsert.py` | `upsert_rows()` |
| Create | `backend/ingestion/quant_data_pipeline/calendar_to_fiscal_period.py` | `normalize_fiscal_period()` |
| Create | `backend/ingestion/quant_data_pipeline/ticker_universe_loader.py` | `load_ticker_universe()` |
| Create | `backend/ingestion/quant_data_pipeline/quant_pipeline_errors.py` | 6 exception classes |
| Create | `backend/ingestion/quant_data_pipeline/quant_ingestion_runs.py` | `ingestion_run()` + `RunReport` |
| Create | `backend/ingestion/quant_data_pipeline/quant_retry.py` | `with_retry()` |
| Create | `backend/tests/utils/__init__.py` | test package |
| Create | `backend/tests/utils/test_span_tracing.py` | `traced_span()` unit test |
| Create | `backend/tests/ingestion/quant_data_pipeline/__init__.py` | test package |
| Create | `backend/tests/ingestion/quant_data_pipeline/conftest.py` | `tmp_duckdb` fixture |
| Create | `backend/tests/ingestion/quant_data_pipeline/test_quant_pipeline_errors.py` | error class inheritance |
| Create | `backend/tests/ingestion/quant_data_pipeline/test_connection.py` | connection behaviour |
| Create | `backend/tests/ingestion/quant_data_pipeline/test_schema_comments.py` | quarterly ↔ annual COMMENT mirror |
| Create | `backend/tests/ingestion/quant_data_pipeline/test_upsert.py` | upsert helper |
| Create | `backend/tests/ingestion/quant_data_pipeline/test_calendar_to_fiscal_period.py` | 10 golden cases |
| Create | `backend/tests/ingestion/quant_data_pipeline/test_ticker_universe_loader.py` | loader |
| Create | `backend/tests/ingestion/quant_data_pipeline/test_quant_retry.py` | retry decorator |
| Create | `backend/tests/ingestion/quant_data_pipeline/test_quant_ingestion_runs.py` | context manager |
| Create | `backend/tests/ingestion/quant_data_pipeline/test_schema_roundtrip.py` | end-to-end smoke |

**Structure sketch:**

```text
backend/
├── utils/
│   ├── __init__.py
│   └── span_tracing.py                     # file-moved from sec_dense_pipeline/tracing.py
├── ingestion/
│   ├── sec_dense_pipeline/
│   │   ├── retriever.py                    # import updated
│   │   ├── vectorizer.py                   # import updated
│   │   └── (tracing.py removed)
│   └── quant_data_pipeline/
│       ├── __init__.py
│       ├── README.md
│       ├── config/ticker_universe.yaml
│       ├── duck_db/
│       │   ├── __init__.py
│       │   ├── connection.py
│       │   ├── schema.sql
│       │   ├── row_models.py
│       │   └── upsert.py
│       ├── calendar_to_fiscal_period.py
│       ├── ticker_universe_loader.py
│       ├── quant_pipeline_errors.py
│       ├── quant_ingestion_runs.py
│       └── quant_retry.py
└── tests/
    ├── utils/{__init__.py, test_span_tracing.py}
    └── ingestion/quant_data_pipeline/
        ├── conftest.py
        └── test_*.py (8 個)
```

---

### Task 1: Project setup — deps、gitignore、package skeleton

**Files:**

- Update: `pyproject.toml`
- Update: `.gitignore`
- Create: `backend/ingestion/quant_data_pipeline/__init__.py`
- Create: `backend/ingestion/quant_data_pipeline/duck_db/__init__.py`
- Create: `backend/tests/ingestion/quant_data_pipeline/__init__.py`
- Create: `backend/tests/utils/__init__.py`
- Create: `backend/utils/__init__.py`

**What & Why:** 先把 infrastructure 打平（依賴、檔案系統忽略、package 目錄），後續每個 task 才能 `import backend.ingestion.quant_data_pipeline.*`。Infrastructure-only，用 build/install 驗證。

**Implementation Notes:**

- `pyproject.toml` `[project.dependencies]` 追加：`"duckdb>=1.0.0"` 與 `"pandas>=2.0.0"`。保留原有 ordering、不動其他 deps。
- `.gitignore` 檔尾追加（若對應規則尚未存在）：
  ```gitignore
  # Quant data pipeline local DuckDB files
  data/*.duckdb
  data/*.db
  ```
- 全部 `__init__.py` 建為**空檔**（package marker）。
- `data/` 目錄**不**在本 task 手動建立，`get_connection()` runtime 以 `parents=True, exist_ok=True` 自行建立（見 Task 4）。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv sync` | 成功；`duckdb` 與 `pandas` 出現在 `uv.lock` | 確認新 deps 解析 |
| Targeted | `uv run python -c "import duckdb, pandas"` | 無 error、無輸出 | Python 可 import |
| Targeted | `git check-ignore data/quant.db data/test.duckdb` | 兩路徑皆 match（exit 0，stdout 列出） | gitignore 規則有生效 |
| Broader | `uv run pytest backend/tests -q` | 與本 task 前的結果相同（無 regression） | 新增 deps 不破 suite |

**Execution Checklist** (infrastructure-only — build/install verification):

- [ ] Update `pyproject.toml` — 加 `duckdb>=1.0.0`、`pandas>=2.0.0`
- [ ] Update `.gitignore` — 加 `data/*.duckdb`、`data/*.db`
- [ ] Create `backend/utils/__init__.py`（空檔）
- [ ] Create `backend/ingestion/quant_data_pipeline/__init__.py`（空檔）
- [ ] Create `backend/ingestion/quant_data_pipeline/duck_db/__init__.py`（空檔）
- [ ] Create `backend/tests/ingestion/quant_data_pipeline/__init__.py`（空檔）
- [ ] Create `backend/tests/utils/__init__.py`（空檔）
- [ ] Run `uv sync` 並確認 lock file 更新
- [ ] Run `uv run python -c "import duckdb, pandas"` 確認 import 成功
- [ ] Run `git check-ignore data/quant.db data/test.duckdb` 確認規則
- [ ] Run full pytest baseline 確認無 regression
- [ ] Commit: `chore(quant-pipeline): bootstrap package layout and new deps (duckdb, pandas)`

---

### Task 2: Error taxonomy (葉節點、零 internal deps)

**Files:**

- Create: `backend/ingestion/quant_data_pipeline/quant_pipeline_errors.py`
- Tests: `backend/tests/ingestion/quant_data_pipeline/test_quant_pipeline_errors.py`

**What & Why:** 整個 foundation 其他模組都要 raise 這 6 個 class；先落地讓後續任何 task 都能 import。Pure class hierarchy，TDD 最小 unit test 即可。

**Implementation Notes:**

- 6 個 class：`QuantPipelineError`（base）、`TransientError`、`TickerNotFoundError`、`DataValidationError`、`ConfigurationError`、`SchemaError`。
- 所有 subclass 直接繼承 `QuantPipelineError`（**扁平結構**，design §6）。
- 每個 class 加 **一行 docstring** 說明語意與 retryable/non-retryable（符合 design master §7.6）。
- **不要**繼承 `SECPipelineError`（design §6.2：平行不繼承）。

**Critical Contract:**

```python
class QuantPipelineError(Exception):
    """Base for all quant data pipeline errors."""

class TransientError(QuantPipelineError):
    """Retryable: net blip / 5xx / rate limit."""

class TickerNotFoundError(QuantPipelineError):
    """Non-retryable: ticker absent from source."""

class DataValidationError(QuantPipelineError):
    """Non-retryable: extracted data violates schema invariants."""

class ConfigurationError(QuantPipelineError):
    """Non-retryable: missing env var / invalid universe yaml."""

class SchemaError(QuantPipelineError):
    """Non-retryable: DB schema missing or corrupted at connect time."""
```

**Test Strategy:** 一個 parametrize 測試證明 5 個 subclass 都是 `QuantPipelineError` 的 subclass、且都是 `Exception` 的 subclass。另一個測試確保 `TransientError` 與 `TickerNotFoundError` **不**互為 subclass（sibling only）——守護 error handling 路徑分流邏輯。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/ingestion/quant_data_pipeline/test_quant_pipeline_errors.py -v` | 2 tests pass | Hierarchy 正確 |

**Execution Checklist:**

- [ ] 🔴 Write `test_quant_pipeline_errors.py`：parametrize 5 subclasses × `issubclass(cls, QuantPipelineError)`；sibling non-inheritance check
- [ ] 🔴 Run targeted test → 確認 **fail**（module missing）
- [ ] 🟢 Implement `quant_pipeline_errors.py` 6 classes
- [ ] 🔵 Review: docstring 齊全、class order 與 design §6 一致
- [ ] 🔵 Rerun targeted test → 確認 pass
- [ ] Commit: `feat(quant-pipeline): add error taxonomy (QuantPipelineError + 5 subclasses)`

---

### Task 3: schema.sql + connection.py + conftest + mirror 守護

**Files:**

- Create: `backend/ingestion/quant_data_pipeline/duck_db/schema.sql`
- Create: `backend/ingestion/quant_data_pipeline/duck_db/connection.py`
- Create: `backend/tests/ingestion/quant_data_pipeline/conftest.py`
- Tests: `backend/tests/ingestion/quant_data_pipeline/test_connection.py`
- Tests: `backend/tests/ingestion/quant_data_pipeline/test_schema_comments.py`

**What & Why:** DDL + connection bootstrap + schema 層契約測試一起交付。`schema.sql` 與 `get_connection()` 在設計上是一體（connection 自動 apply DDL），mirror 測試也只有在 connection 能 bootstrap 之後才跑得起來，所以這三件事共一個 checkpoint。

**Implementation Notes:**

- `schema.sql` 依 Design Master §6 順序寫 8 張表：`companies` → `market_valuations` → `quarterly_financials` → `annual_financials` → `segment_financials` → `geographic_revenue` → `customer_concentration` → `ingestion_runs`（加 `idx_runs_pipeline_ticker_started` index）。
- 每張表 DDL **逐字** 對應 design_master.md §6 區塊中的 `CREATE TABLE` + 後續所有 `COMMENT ON COLUMN`。`annual_financials` 的 COMMENT 必須與 `quarterly_financials` 逐欄對應字對字一致（除 `fiscal_quarter` 不存在）。
- 全部 `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`（重跑 `get_connection()` 無副作用）。
- `connection.py`：
  - `_SCHEMA_SQL_PATH = Path(__file__).parent / "schema.sql"` 相對當前檔案解析。
  - `get_connection(db_path=None, *, ensure_schema=True)`：
    - `db_path=None` → `os.getenv("DUCKDB_PATH", "data/quant.db")`。
    - `Path(path).parent.mkdir(parents=True, exist_ok=True)`。
    - `duckdb.connect(path)`。
    - `ensure_schema=True` 時：若 `_SCHEMA_SQL_PATH` 不存在 → raise `SchemaError("schema.sql missing at <path>")`；否則 `conn.execute(text)`；execute 失敗也轉 `SchemaError`（`raise SchemaError(...) from exc`）。
  - 回傳的 `DuckDBPyConnection` 為 DuckDB 原生物件（支援 `with ... as conn:`）。
- `conftest.py` 提供 `tmp_duckdb` fixture（function scope）：`tmp_path / "test.db"` → `get_connection(..., ensure_schema=True)` → yield → `conn.close()`。

**Critical Contract:**

```python
# connection.py
def get_connection(
    db_path: str | None = None,
    *,
    ensure_schema: bool = True,
) -> DuckDBPyConnection:
    path = db_path or os.getenv("DUCKDB_PATH", "data/quant.db")
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
```

```python
# test_schema_comments.py — mirror 守護
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
```

**Test Strategy:**

- `test_connection.py`：
  - **正常路徑**：`get_connection(tmp_path / "x.db")` → `conn.execute("SELECT 1")` 回 `(1,)`；`data/` 被自動建立。
  - **ensure_schema=True**：bootstrap 後 `SELECT count(*) FROM duckdb_tables() WHERE table_name='companies'` 等於 1；全 8 張表名都在。
  - **ensure_schema=False**：bootstrap 不跑（`duckdb_tables` 為空）。
  - **env var fallback**：`DUCKDB_PATH` 指到 tmp 路徑，`get_connection()` 不傳參數時讀到該路徑。
  - **SchemaError**：把 `_SCHEMA_SQL_PATH` monkeypatch 到不存在的路徑，`get_connection(...)` raise `SchemaError`；monkeypatch 到「裡面放一段 invalid SQL」的 tmp 檔，同樣 raise `SchemaError`，且 `__cause__` 是 `duckdb.Error`。
- `test_schema_comments.py`：上面 snippet——mirror 契約（design §3.3）。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/ingestion/quant_data_pipeline/test_connection.py backend/tests/ingestion/quant_data_pipeline/test_schema_comments.py -v` | 全 pass | 證 schema.sql bootstrap 與 mirror 正確 |
| Targeted | `uv run python -c "from backend.ingestion.quant_data_pipeline.duck_db.connection import get_connection; c = get_connection(':memory:'); print(c.execute(\"SELECT count(*) FROM duckdb_tables()\").fetchone())"` | 輸出 `(8,)` | schema bootstrap ≥ 8 張表 |

**Execution Checklist:**

- [ ] 🔴 Write `conftest.py` `tmp_duckdb` fixture
- [ ] 🔴 Write `test_connection.py`（5 cases 如上）與 `test_schema_comments.py`
- [ ] 🔴 Run targeted tests → 確認 **fail**（schema.sql / connection.py missing）
- [ ] 🟢 Write `schema.sql` 8 張表 DDL + 全 COMMENT（逐字對應 design_master §6；annual 欄位 COMMENT 從 quarterly 複製）
- [ ] 🟢 Write `connection.py` `get_connection()`
- [ ] 🟢 Run targeted tests → 確認 pass（包含 mirror 守護）
- [ ] 🔵 Review schema.sql：欄位順序、NOT NULL、PK、index 與 design §6 完全一致
- [ ] 🔵 Rerun targeted tests → still pass
- [ ] Commit: `feat(quant-pipeline): DuckDB schema.sql + get_connection + mirror guard`

---

### Task 4: Row DTOs + `upsert_rows()` helper

**Files:**

- Create: `backend/ingestion/quant_data_pipeline/duck_db/row_models.py`
- Create: `backend/ingestion/quant_data_pipeline/duck_db/upsert.py`
- Tests: `backend/tests/ingestion/quant_data_pipeline/test_upsert.py`

**What & Why:** DTO 定義寫入契約（欄位名與 DDL column 對齊、不含 `updated_at`），`upsert_rows()` 把 DTO batch 變成 idempotent `INSERT ... ON CONFLICT DO UPDATE`。兩者一組交付，DTO 單獨沒消費者。

**Implementation Notes:**

- `row_models.py` 5 個 DTO（design §4.1）：
  - `CompanyRow`（`companies` 全欄位除 `updated_at`）
  - `MarketValuationRow`（`market_valuations` 全欄位除 `updated_at`）
  - `YFinanceQuarterlyRow`（`quarterly_financials` 中 yfinance-sourced 欄位；**不含** `product_revenue_usd`、`service_revenue_usd`、`current_rpo_usd`、`noncurrent_rpo_usd`、`total_lease_obligation_usd`、`updated_at`）
  - `YFinanceAnnualRow`（同 quarterly，扣 `fiscal_quarter`）
  - `IngestionRunRow`（`ingestion_runs` 全欄位；`run_id` 允許 caller 傳，`ingestion_run()` context manager 自己產 UUID）
- 每個 DTO 一行 docstring 說明 owner、對應表、排除欄位。
- Field 型別：PK 欄位（`ticker: str`、`fiscal_year: int` …）required；非 PK 依 DDL nullable `| None = None`。`period_end: date`（DDL NOT NULL）、`period_start: date | None = None`。Money 欄位 `int | None = None`（DDL `BIGINT`，overflow 留給 DuckDB 擲錯）。
- `upsert.py` `upsert_rows()`：
  - **空 list 短路**：`if not rows: return 0`（不 register、不 SQL）。
  - 從 `type(rows[0]).model_fields` 拿 column list（不用 `df.columns` 以避免 pandas 篩掉 all-None 欄位的風險）。
  - **Assert**：column list 不得包含 `"updated_at"`；若違反，raise `AssertionError`（programmer error）。
  - 組 SQL 走 design §5.2.2 **方案 A**（INSERT / SELECT / SET 三處都列欄位）。SET 子句尾加 `updated_at = CURRENT_TIMESTAMP`。
  - `df = pd.DataFrame([r.model_dump() for r in rows])` → `conn.register("staging", df)` → `conn.execute(sql)` → `finally: conn.unregister("staging")`。
  - Return `len(rows)`（非 DuckDB affected count）。

**Critical Contract:**

```python
# upsert.py
def upsert_rows(
    conn: DuckDBPyConnection,
    table: str,
    pk_columns: list[str],
    rows: list[T],  # T bound=BaseModel
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
        + ["updated_at = CURRENT_TIMESTAMP"]
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
```

**Test Strategy:** 使用 `tmp_duckdb` fixture。

- **空 list 短路**：`upsert_rows(conn, "companies", ["ticker"], [])` → 回 `0`、`companies` 仍空。
- **Insert 正常路徑**：`CompanyRow(ticker="MSFT", ...)` upsert → `SELECT * FROM companies` 回 1 筆、`updated_at` 非 NULL。
- **Idempotent update**：相同 PK 但 `sector` 改值兩次，第二次 upsert 後 `sector` 為新值、`updated_at` 更新（大於第一次的 timestamp）。
- **Column-level merge（核心契約）**：
  1. 先 insert 完整 `quarterly_financials` row（所有欄位有值；先走 raw SQL 模擬 SEC 將來的寫入：含 `product_revenue_usd`、`current_rpo_usd`）。
  2. 用 `YFinanceQuarterlyRow`（不含 `product_revenue_usd` / `current_rpo_usd`）upsert 同一 PK。
  3. `SELECT product_revenue_usd, current_rpo_usd FROM quarterly_financials WHERE ...` → 原 SEC 寫的值**仍保留**；yfinance 欄位（如 `total_revenue_usd`）反映新值。
- **`updated_at` 自動維護**：DTO 不 declare `updated_at`；手動組一個含 `updated_at` 欄位的假 DTO，confirm `AssertionError`。
- **PK 必填**：pydantic 本身會擲 `ValidationError`（confirm via `pytest.raises`）——這部分不是 upsert_rows 責任，但測一次保守。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/ingestion/quant_data_pipeline/test_upsert.py -v` | 全 pass | upsert 契約正確 |

**Execution Checklist:**

- [ ] 🔴 Write `test_upsert.py`（5 cases 如上；用 `tmp_duckdb` fixture）
- [ ] 🔴 Run targeted test → 確認 **fail**（module missing）
- [ ] 🟢 Implement `row_models.py` 5 個 DTO（對照 design §4.1、不含 `updated_at`）
- [ ] 🟢 Implement `upsert.py` `upsert_rows()` per critical contract
- [ ] 🔵 Review：DTO 欄位集合 ⊂ DDL 欄位、無 `updated_at`、assertion 有 raise
- [ ] 🔵 Rerun targeted test → still pass
- [ ] Commit: `feat(quant-pipeline): row DTOs + upsert_rows() with column-level merge`

---

### Task 5: `normalize_fiscal_period()` (pure function)

**Files:**

- Create: `backend/ingestion/quant_data_pipeline/calendar_to_fiscal_period.py`
- Tests: `backend/tests/ingestion/quant_data_pipeline/test_calendar_to_fiscal_period.py`

**What & Why:** yfinance / SEC 兩子系統把日曆日期轉成 `(fiscal_year, fiscal_quarter)` 的唯一管道。純函式、零依賴，最適合 pytest parametrize + golden cases。

**Implementation Notes:**

- `normalize_fiscal_period(period_end: date, fiscal_year_end_month: int) -> tuple[int, int]`，月精度（忽略 day）。
- Algorithm 對照 design master §7.4：
  1. `if period_end.month <= fye_month`: `fy = period_end.year`，else `fy = period_end.year + 1`、`fye_month += 12`。
  2. `months_before = fye_month - period_end.month`。
  3. `if months_before % 3 != 0`: raise `ValueError(f"period_end {period_end} not quarter-aligned to FYE month {fiscal_year_end_month}: delta={months_before} months")`。
  4. `quarter = 4 - months_before // 3`；return `(fy, quarter)`。
- 錯誤類型用 Python 內建 `ValueError`（design §5.3）——helper-level validation；子系統若需轉型自己包成 `DataValidationError`。

**Test Strategy:** Parametrize Design Master §7.4 的 10 個 golden cases：

| Ticker | FYE | period_end | Expected |
|---|---|---|---|
| AAPL | 9 | 2024-06-30 | (2024, 3) |
| AAPL | 9 | 2024-09-28 | (2024, 4) |
| AAPL | 9 | 2024-12-31 | (2025, 1) |
| AMZN | 12 | 2024-03-31 | (2024, 1) |
| AMZN | 12 | 2024-12-31 | (2024, 4) |
| MSFT | 6 | 2024-06-30 | (2024, 4) |
| MSFT | 6 | 2024-09-30 | (2025, 1) |
| NVDA | 1 | 2024-01-28 | (2024, 4) |
| NVDA | 1 | 2024-04-30 | (2025, 1) |
| CRM | 1 | 2025-01-31 | (2025, 4) |

加 **2 個 error cases**：非季度邊界（e.g. `period_end=2024-07-15` + `fye=9`，delta 2 個月）→ `pytest.raises(ValueError)`；FYE=9 + period_end=2024-11-30（delta 10 個月）→ raise。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/ingestion/quant_data_pipeline/test_calendar_to_fiscal_period.py -v` | 12 tests pass（10 golden + 2 error）| 所有 FYE × period_end 案例正確 |

**Execution Checklist:**

- [ ] 🔴 Write `test_calendar_to_fiscal_period.py`（`@pytest.mark.parametrize` 10 golden + 2 error）
- [ ] 🔴 Run targeted test → 確認 **fail**
- [ ] 🟢 Implement `calendar_to_fiscal_period.py` per algorithm
- [ ] 🔵 Review：錯誤訊息含 `period_end` 與 `delta`、回傳 tuple order 正確
- [ ] 🔵 Rerun → still pass
- [ ] Commit: `feat(quant-pipeline): normalize_fiscal_period with 10 golden cases`

---

### Task 6: Ticker universe YAML + loader

**Files:**

- Create: `backend/ingestion/quant_data_pipeline/config/ticker_universe.yaml`
- Create: `backend/ingestion/quant_data_pipeline/ticker_universe_loader.py`
- Tests: `backend/tests/ingestion/quant_data_pipeline/test_ticker_universe_loader.py`

**What & Why:** 宣告 foundation 時期 canonical 10 tickers（跨產業壓測 schema）並提供 loader。下游三類 consumer（CLI batch、`validate` subcommand、agent 邊界檢查）會在子系統 PR 消費。

**Implementation Notes:**

- `ticker_universe.yaml` 完全按 design §5.7：10 ticker + 每個加 `#` 行內註解標 industry。
  ```yaml
  tickers:
    - MSFT   # Software + Cloud
    - NVDA   # Semiconductor
    - CRM    # SaaS
    - WMT    # Retail
    - JPM    # Banking
    - BRK.B  # Insurance / Holdco
    - JNJ    # Pharma / Healthcare
    - KO     # Consumer staples
    - XOM    # Integrated Energy
    - CAT    # Industrial
  ```
- `ticker_universe_loader.py`：
  - `_UNIVERSE_PATH = Path(__file__).parent / "config" / "ticker_universe.yaml"`。
  - `load_ticker_universe(path: Path | None = None) -> list[str]`：`yaml.safe_load` → 取 `"tickers"` key → `[t.upper() for t in ...]`。
  - 缺 `tickers` key / yaml parse 失敗 / 檔案不存在 → raise `ConfigurationError(<descriptive msg>)`（從 `yaml.YAMLError` / `KeyError` / `FileNotFoundError` `raise ... from exc`）。

**Test Strategy:**

- **Happy path**：呼叫 loader 預設路徑 → 回傳 10 ticker list、`"BRK.B"` 等 uppercase、order 與 YAML 相同。
- **Custom path**：寫入 tmp YAML `tickers: [aapl, googl]` → 回傳 `["AAPL", "GOOGL"]`。
- **缺 key**：tmp YAML `{"foo": "bar"}` → `pytest.raises(ConfigurationError)`。
- **Parse error**：tmp file 寫 `":::invalid"` → `pytest.raises(ConfigurationError)`，`__cause__` 為 `yaml.YAMLError`。
- **File missing**：不存在路徑 → `pytest.raises(ConfigurationError)`。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/ingestion/quant_data_pipeline/test_ticker_universe_loader.py -v` | 全 pass | Loader + error paths 正確 |

**Execution Checklist:**

- [ ] 🔴 Write `test_ticker_universe_loader.py`（5 cases 如上）
- [ ] 🔴 Run → **fail**
- [ ] 🟢 Write `ticker_universe.yaml`、`ticker_universe_loader.py`
- [ ] 🔵 Review：ticker order 與 design §5.7 表格一致；行尾 comment 產業標記齊全
- [ ] 🔵 Rerun → pass
- [ ] Commit: `feat(quant-pipeline): ticker universe yaml + loader (10 cross-industry tickers)`

---

### Task 7: `with_retry()` decorator

**Files:**

- Create: `backend/ingestion/quant_data_pipeline/quant_retry.py`
- Tests: `backend/tests/ingestion/quant_data_pipeline/test_quant_retry.py`

**What & Why:** 子系統 fetcher 在遭遇 `TransientError`（子系統 subclass 也算）時走 exponential backoff。Foundation 只提供機制（design §5.5），不做 pacing。

**Implementation Notes:**

- `with_retry(max_attempts: int = 3, base_delay_seconds: float = 1.0)` → decorator factory。
- Backoff：`base_delay_seconds * (2 ** attempt)`（attempts 0/1/2 → 1/2/4s 預設；子系統 override 例如 `base_delay_seconds=60.0`）。
- **只 retry `TransientError` 及其 subclass**；其他 exception 立即 propagate。
- 每次 retry 前 `logger.warning("Transient error on attempt %d/%d for %s: %s. Retrying in %.1fs.", ...)`。
- Max attempts 用盡後 `raise last_exc`（保留 traceback）。
- **不**把 retry_count 寫進 `ingestion_runs.metadata`（那是 caller 的事，design §5.5 與 §7 reserved keys 都說子系統自行 count）。

**Test Strategy:**

- **No error**：函式第一次就成功 → wrapper 只呼叫一次、直接回傳值。
- **Eventually succeeds**：前 2 次 raise `TransientError`、第 3 次成功 → wrapper 回傳；`time.sleep` 被 mock（monkeypatch）為記錄呼叫參數的 fake，assert delays `[1.0, 2.0]`。
- **Exhausts attempts**：每次都 raise `TransientError("boom")` → `pytest.raises(TransientError, match="boom")`；sleep 呼叫 2 次（attempt 0 / 1 之後）。
- **Non-transient not retried**：raise `ValueError` → 立即 propagate、sleep 未呼叫。
- **Custom params**：`@with_retry(max_attempts=2, base_delay_seconds=0.5)` → sleep 只呼叫一次（在 attempt 0 後）、delay=0.5。
- **Subclass of TransientError**：在測試內 define `class FakeRateLimit(TransientError): pass`，raise 後仍被 retry。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/ingestion/quant_data_pipeline/test_quant_retry.py -v` | 6 tests pass | Retry behaviour 正確 |

**Execution Checklist:**

- [ ] 🔴 Write `test_quant_retry.py`（monkeypatch `time.sleep`）
- [ ] 🔴 Run → **fail**
- [ ] 🟢 Implement `quant_retry.py` `with_retry()`
- [ ] 🔵 Review：`@wraps(fn)` 保留 signature、log level=warning、traceback 保留
- [ ] 🔵 Rerun → pass
- [ ] Commit: `feat(quant-pipeline): with_retry() exponential-backoff decorator for TransientError`

---

### Task 8: `ingestion_run()` + `RunReport` + end-to-end roundtrip smoke

**Files:**

- Create: `backend/ingestion/quant_data_pipeline/quant_ingestion_runs.py`
- Tests: `backend/tests/ingestion/quant_data_pipeline/test_quant_ingestion_runs.py`
- Tests: `backend/tests/ingestion/quant_data_pipeline/test_schema_roundtrip.py`

**What & Why:** Context manager 是 foundation 對 auditability 的主 API，也同時是驗證「schema + connection + DTO + upsert 全鏈 OK」的 E2E smoke 最自然的 driver。兩件事一組 deliver。

**Implementation Notes:**

- `RunReport`：
  ```python
  @dataclass
  class RunReport:
      rows_written_total: int = 0
      metadata: dict[str, Any] = field(default_factory=dict)
  ```
- `@contextmanager` `ingestion_run(conn, pipeline, ticker, *, target_filing_type=None, target_fiscal_year=None, target_fiscal_quarter=None, target_accession_number=None) -> Iterator[RunReport]`：
  - `run_id = str(uuid4())`；`started_at = datetime.now(UTC)`。
  - `report = RunReport()`；`try: yield report; _write(...status='success'...)`；`except Exception as exc: _write(...status='error', error_class=type(exc).__name__, error_message=str(exc), rows_written_total=0, metadata=report.metadata...); raise`。
  - `_write_run()` 內部 helper 組 `INSERT INTO ingestion_runs (...) VALUES (...)`：`metadata` 用 `json.dumps(report.metadata)` 串成 JSON 字串、DuckDB `JSON` 欄位接。
  - **不經過 `upsert_rows()`**（ingestion_runs 沒 conflict 場景、`run_id` 每次 UUID），直接走 prepared statement 避 SQL injection。用 `conn.execute(sql, [params...])` positional。

**Critical Contract:**

```python
@contextmanager
def ingestion_run(
    conn: DuckDBPyConnection,
    pipeline: str,
    ticker: str,
    *,
    target_filing_type: str | None = None,
    target_fiscal_year: int | None = None,
    target_fiscal_quarter: int | None = None,
    target_accession_number: str | None = None,
) -> Iterator[RunReport]:
    run_id = str(uuid4())
    started_at = datetime.now(UTC)
    report = RunReport()
    try:
        yield report
    except Exception as exc:
        _insert_run(
            conn, run_id, pipeline, ticker,
            target_filing_type, target_fiscal_year,
            target_fiscal_quarter, target_accession_number,
            started_at, datetime.now(UTC),
            status="error",
            error_class=type(exc).__name__,
            error_message=str(exc),
            rows_written_total=0,
            metadata=report.metadata,
        )
        raise
    _insert_run(
        conn, run_id, pipeline, ticker,
        target_filing_type, target_fiscal_year,
        target_fiscal_quarter, target_accession_number,
        started_at, datetime.now(UTC),
        status="success",
        error_class=None, error_message=None,
        rows_written_total=report.rows_written_total,
        metadata=report.metadata,
    )
```

**Test Strategy:**

`test_quant_ingestion_runs.py`（用 `tmp_duckdb` fixture）：
- **Success path**：`with ingestion_run(conn, "yfinance", "NVDA") as report: report.rows_written_total = 5; report.metadata["periods_covered"] = {"quarterly": ["2025Q3"]}` → `SELECT ...` 回 1 筆 row：`status='success'`、`rows_written_total=5`、`error_class IS NULL`、`metadata::JSON->>'periods_covered'` 內容正確；`started_at <= finished_at`。
- **Error path**：`with ingestion_run(...): raise TickerNotFoundError("NVDA not found")` → `pytest.raises(TickerNotFoundError)`；DB 仍寫了 1 筆 row：`status='error'`、`error_class='TickerNotFoundError'`、`error_message='NVDA not found'`、`rows_written_total=0`、`metadata` 保留 exception 前填的 partial。
- **Partial metadata preserved on error**：`with ... as report: report.metadata["api_latency_ms"] = {"info": 120}; raise RuntimeError("boom")` → error row 的 `metadata` 仍含 `api_latency_ms`、`rows_written_total=0`（不信 caller）。
- **SEC 預留 kwargs**：`with ingestion_run(conn, "sec_xbrl", "NVDA", target_filing_type="10-K", target_fiscal_year=2024, target_accession_number="0001045810-24-000316") as report: pass` → DB 對應欄位正確。
- **Distinct run_id**：連開兩次 → 兩筆 row 的 `run_id` 不同。

`test_schema_roundtrip.py` — **end-to-end smoke**（用 `tmp_duckdb` fixture）：
1. `upsert_rows(conn, "companies", ["ticker"], [CompanyRow(ticker="MSFT", company_name="Microsoft", sector="Technology", industry="Software", fy_end_month=6, fy_end_day=30)])` → 回 1。
2. `SELECT * FROM companies WHERE ticker='MSFT'` → 所有欄位正確、`updated_at` 非 NULL。
3. 用 `normalize_fiscal_period(date(2024, 9, 30), 6)` → `(2025, 1)`；據此組一筆 `YFinanceQuarterlyRow` upsert 進 `quarterly_financials`、回 1。
4. `with ingestion_run(conn, "yfinance", "MSFT") as report: report.rows_written_total = 2` 包住前兩步（可用一個 restructured sub-test 做）。
5. `SELECT count(*) FROM ingestion_runs WHERE pipeline='yfinance' AND ticker='MSFT' AND status='success'` → 1。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/ingestion/quant_data_pipeline/test_quant_ingestion_runs.py backend/tests/ingestion/quant_data_pipeline/test_schema_roundtrip.py -v` | 全 pass | Audit context + end-to-end smoke 皆 OK |

**Execution Checklist:**

- [ ] 🔴 Write `test_quant_ingestion_runs.py`（5 cases）
- [ ] 🔴 Write `test_schema_roundtrip.py`（E2E smoke）
- [ ] 🔴 Run targeted → **fail**（module missing）
- [ ] 🟢 Implement `quant_ingestion_runs.py` per critical contract
- [ ] 🔵 Review：UTC timestamp、JSON metadata serialization、exception re-raise、prepared statement params 對齊
- [ ] 🔵 Rerun → pass
- [ ] Commit: `feat(quant-pipeline): ingestion_run context manager + end-to-end roundtrip`

---

### Flow Verification: Foundation public API smoke

> Tasks 2–8 完成後，foundation 對下游 PR 交付的全套 symbol 已到位。此 flow 以 public-API 黑箱視角驗證 import 與基本呼叫 shape 正確，作為子系統 PR 接手前的 contract gate。

| #   | Method                        | Step                                                                                                                                              | Expected Result                                                                                                  |
| --- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 1   | Runtime / import check        | `uv run python -c "from backend.ingestion.quant_data_pipeline.duck_db.connection import get_connection; from backend.ingestion.quant_data_pipeline.duck_db.upsert import upsert_rows; from backend.ingestion.quant_data_pipeline.duck_db.row_models import CompanyRow, MarketValuationRow, YFinanceQuarterlyRow, YFinanceAnnualRow, IngestionRunRow; from backend.ingestion.quant_data_pipeline.calendar_to_fiscal_period import normalize_fiscal_period; from backend.ingestion.quant_data_pipeline.ticker_universe_loader import load_ticker_universe; from backend.ingestion.quant_data_pipeline.quant_ingestion_runs import ingestion_run, RunReport; from backend.ingestion.quant_data_pipeline.quant_retry import with_retry; from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import QuantPipelineError, TransientError, TickerNotFoundError, DataValidationError, ConfigurationError, SchemaError; print('ok')"` | stdout `ok`，無 ImportError | 完整 public API surface（design §5）可 import                                                                |
| 2   | Database / state check         | `uv run python -c "from backend.ingestion.quant_data_pipeline.duck_db.connection import get_connection; c = get_connection(':memory:'); print(sorted(r[0] for r in c.execute('SELECT table_name FROM duckdb_tables()').fetchall()))"` | 輸出包含 `['annual_financials','companies','customer_concentration','geographic_revenue','ingestion_runs','market_valuations','quarterly_financials','segment_financials']`（8 張表） | schema bootstrap 完整 |
| 3   | Assertion script              | `uv run python -c "from backend.ingestion.quant_data_pipeline.ticker_universe_loader import load_ticker_universe; u = load_ticker_universe(); assert u == ['MSFT','NVDA','CRM','WMT','JPM','BRK.B','JNJ','KO','XOM','CAT'], u; print('ok')"`                                      | stdout `ok`                                                                                                      | Canonical 10 ticker 清單與 design §5.7 一致                                                                  |
| 4   | Targeted pytest               | `uv run pytest backend/tests/ingestion/quant_data_pipeline -v`                                                                                    | 全部綠                                                                                                           | Foundation 所有 unit / contract / smoke 齊綠                                                                 |

- [ ] All flow verifications pass

---

### Task 9: Lift `tracing.py` → `backend/utils/span_tracing.py` 並更新 sec_dense_pipeline imports

**Files:**

- Create: `backend/utils/span_tracing.py`（內容 = `sec_dense_pipeline/tracing.py` 原檔）
- Delete: `backend/ingestion/sec_dense_pipeline/tracing.py`
- Update: `backend/ingestion/sec_dense_pipeline/retriever.py`（import 路徑）
- Update: `backend/ingestion/sec_dense_pipeline/vectorizer.py`（import 路徑）
- Tests: `backend/tests/utils/test_span_tracing.py`

**What & Why:** `traced_span()` 內容 generic、已在 `sec_dense_pipeline` 實戰。本 PR **file move**（不 rewrite）讓 foundation 與 SEC RAG pipeline 共用同一份；`test_span_tracing.py` 補回 sec_dense_pipeline 本來沒寫的單元 coverage（design §8.4）。放最後避免早期 task 還沒建立全套 test suite 時就動到既有 pipeline。

**Implementation Notes:**

- `backend/utils/span_tracing.py` 內容**逐字複製**現行 `backend/ingestion/sec_dense_pipeline/tracing.py`（design §5.6、§13）。不改行為、不改 `_NoOpSpan` shape。
- 刪 `backend/ingestion/sec_dense_pipeline/tracing.py`。
- `retriever.py` 與 `vectorizer.py` 目前的 `from backend.ingestion.sec_dense_pipeline.tracing import traced_span`（或類似路徑）改為 `from backend.utils.span_tracing import traced_span`；**只改 import**，不動邏輯。
- `test_span_tracing.py` 兩 case（design §8.4）：
  - **Case 1 — no outer span**：monkeypatch `opentelemetry.trace.get_current_span` 回 invalid-context fake（`get_span_context().is_valid == False`）；`with traced_span("foo") as span: span.update(output={"x": 1}); span.update_trace(metadata={})` 不擲錯；monkeypatch `langfuse.get_client` 回 `Mock`，assert 沒被呼叫。
  - **Case 2 — outer span active**：monkeypatch `get_current_span` 回 valid fake（`is_valid == True`），monkeypatch `get_client` 回 mock client；`with traced_span("yf_fetch"): pass` → `mock_client.start_as_current_observation.assert_called_once_with(name="yf_fetch")`。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/utils/test_span_tracing.py -v` | 2 tests pass | No-op / active span 兩路徑正確 |
| Broader | `uv run grep -rn "from backend.ingestion.sec_dense_pipeline.tracing" backend/` (via Grep) | 無 match（舊 import 已全部改掉）| 沒遺漏 import call site |
| Broader | `uv run pytest backend/tests/ingestion/sec_dense_pipeline -v` | 與遷移前相同的 pass/skip 結果 | sec_dense_pipeline 本身 suite 不 regress |
| Broader | `uv run pytest backend/tests -q -m "not eval and not sec_integration and not integration"` | 與遷移前相同的 pass/skip 結果（除了新增的 foundation + `test_span_tracing.py` 全綠）| 全 repo 無 regression |

**Execution Checklist:**

- [ ] 🔴 Write `backend/tests/utils/test_span_tracing.py`（2 cases 如上）
- [ ] 🔴 Run → **fail**（`backend.utils.span_tracing` 尚未存在）
- [ ] 🟢 `git mv backend/ingestion/sec_dense_pipeline/tracing.py backend/utils/span_tracing.py`（保留 blame）
- [ ] 🟢 Update `retriever.py` import → `from backend.utils.span_tracing import traced_span`
- [ ] 🟢 Update `vectorizer.py` import → `from backend.utils.span_tracing import traced_span`
- [ ] 🟢 Confirm 沒有其他 call site（`grep "sec_dense_pipeline.tracing"` 應空）
- [ ] 🔵 Rerun `test_span_tracing.py` → pass
- [ ] 🔵 Rerun `backend/tests/ingestion/sec_dense_pipeline` → 與遷移前同結果
- [ ] 🔵 Rerun full default pytest → 與遷移前同結果
- [ ] Commit: `refactor(tracing): lift traced_span from sec_dense_pipeline to backend/utils for cross-pipeline reuse`

---

### Flow Verification: `sec_dense_pipeline` 遷移後行為無 regression

> Task 9 完成後，跨 pipeline tracing util 到位。此 flow 確保 file move 沒有破壞 sec_dense_pipeline 原本的 tracing hook。

| #   | Method              | Step                                                                                               | Expected Result                                                                                                                                          |
| --- | ------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Runtime / import    | `uv run python -c "from backend.utils.span_tracing import traced_span; from backend.ingestion.sec_dense_pipeline.retriever import *; from backend.ingestion.sec_dense_pipeline.vectorizer import *; print('ok')"` | stdout `ok`；無 ImportError                                                                                                                              |
| 2   | Log grep            | `rg "from backend\.ingestion\.sec_dense_pipeline\.tracing" backend/` (via Grep)                    | 無 match                                                                                                                                                 |
| 3   | Targeted pytest     | `uv run pytest backend/tests/utils/test_span_tracing.py backend/tests/ingestion/sec_dense_pipeline -v`   | 全部綠（含任何預期 skip）                                                                                                                                 |

- [ ] All flow verifications pass

---

### Task 10: Package README

**Files:**

- Create: `backend/ingestion/quant_data_pipeline/README.md`

**What & Why:** Ships-with-code 文件，供子系統 PR 作者與後續維護者閱讀；**英文**（memory `feedback_readme_language.md`）。不引用 `artifacts/` 路徑（memory `feedback_no_commit_artifacts.md`）。

**Implementation Notes:**

README 結構對齊 design §12，每節內容簡短且可自含：

1. **Purpose** — "Shared infrastructure for yfinance and SEC XBRL quant ETL pipelines: DuckDB connection/schema, row DTOs, idempotent upsert, retry, audit trail, ticker universe."
2. **Quick start** — 最小 snippet：`get_connection()` + `CompanyRow(...)` + `upsert_rows(...)` 包在 `ingestion_run(...)` 內，約 10 行。
3. **Public API** — 表格列出 symbol → import path → 一句功能：
   - `get_connection`、`upsert_rows`、5 個 row DTO（`duck_db/`）
   - `normalize_fiscal_period`、`load_ticker_universe`、`ingestion_run` + `RunReport`、`with_retry`、6 個 exception class
   - `traced_span` 明確標註來自 `backend.utils.span_tracing`（跨 pipeline util）
4. **Conventions**:
   - DuckDB is single-writer; batch CLI must serialize across tickers.
   - `updated_at` is managed by `upsert_rows()`; do not declare it in row DTOs.
   - `span_tracing.py` lives in `backend/utils/` (cross-pipeline util); `quant_retry.py` lives here (pipeline-scoped).
5. **Adding a new DTO** — declare fields matching DDL columns; exclude `updated_at`; pass `pk_columns` when calling `upsert_rows()`.
6. **Extending error taxonomy** — subsystem subclasses `TransientError` / `TickerNotFoundError` / `DataValidationError`; prefix class name with pipeline (e.g. `YFinanceRateLimitError(TransientError)`).
7. **Testing** — `pytest backend/tests/ingestion/quant_data_pipeline/`；`conftest.py` ships `tmp_duckdb` fixture reusable by subsystem tests.
8. **Schema evolution** — iteration-phase policy: edit `schema.sql` → drop local `data/quant.db` → re-run ETL; no Alembic yet.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | Manual read-through of `README.md` | 8 個小節齊全、全英文、不引用 `artifacts/`、Quick-start snippet 可 copy-paste 執行 | 符合 design §12 與 memory `feedback_readme_language.md` / `feedback_no_commit_artifacts.md` |
| Targeted | `uv run python - <<'EOF' ...`（貼入 README Quick start snippet）`EOF` | 無 error、`SELECT count(*) FROM companies` 回 1 | README snippet 不是幻想、實際可跑 |

**Execution Checklist:**

- [ ] Draft `README.md` 8 sections（English）
- [ ] Copy Quick-start snippet to shell、以 `uv run python` 跑過一次 → 無 error
- [ ] Re-read 全文確認無中文、無 `artifacts/` reference
- [ ] Commit: `docs(quant-pipeline): package README with public API, conventions, and quick start`

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] 每個 Task 的 targeted verification 已執行且 pass
- [ ] `uv run pytest backend/tests/ingestion/quant_data_pipeline -v` 全綠
- [ ] `uv run pytest backend/tests/utils -v` 全綠
- [ ] `uv run pytest backend/tests -q`（default marker：排除 eval / integration / sec_integration）全綠
- [ ] `uv run ruff check backend/utils backend/ingestion/quant_data_pipeline backend/tests/utils backend/tests/ingestion/quant_data_pipeline` 無 error
- [ ] `uv run pyright backend/utils backend/ingestion/quant_data_pipeline`（或 repo 預設 pyright config）無 error
- [ ] `uv sync` 可重跑成功、`uv.lock` 已 commit

### Flow Level (Behavioral)

- [ ] Flow: Foundation public API smoke — PASS / FAIL
- [ ] Flow: `sec_dense_pipeline` 遷移後行為無 regression — PASS / FAIL

### Summary

- [ ] Code + Flow 兩層全過 → 可交付後續子系統 PR
- [ ] 任何失敗已記錄原因與下一步
