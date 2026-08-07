from backend.common.config import (
    REPO_ROOT,
    get_checkpoint_db_path,
    get_duckdb_path,
    get_sec_filings_html_dir,
    get_sec_text_dir,
)
from backend.ingestion.sec_filing_pipeline_html.filing_store import (
    LocalFilingStore as HtmlFilingStore,
)
from backend.ingestion.sec_text_pipeline.filing_store import (
    LocalFilingStore as TextFilingStore,
)


def test_resolves_repo_root_independent_of_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert get_sec_filings_html_dir() == REPO_ROOT / "data" / "sec_filings_html"
    assert get_sec_text_dir() == REPO_ROOT / "data" / "sec_text"
    assert get_duckdb_path() == REPO_ROOT / "data" / "fundamentals.db"
    assert get_checkpoint_db_path() == REPO_ROOT / "data" / "checkpoints.db"


def test_env_override_sec_filings_html_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("SEC_FILINGS_HTML_DIR", str(tmp_path))
    assert get_sec_filings_html_dir() == tmp_path


def test_env_override_sec_text_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("SEC_TEXT_DIR", str(tmp_path))
    assert get_sec_text_dir() == tmp_path


def test_env_override_duckdb_path(monkeypatch, tmp_path):
    target = tmp_path / "custom.db"
    monkeypatch.setenv("DUCKDB_PATH", str(target))
    assert get_duckdb_path() == target


def test_env_override_checkpoint_db_path(monkeypatch, tmp_path):
    target = tmp_path / "custom_checkpoints.db"
    monkeypatch.setenv("CHECKPOINT_DB_PATH", str(target))
    assert get_checkpoint_db_path() == target


def test_html_filing_store_write_path_matches_config_default():
    assert HtmlFilingStore()._base_dir == get_sec_filings_html_dir()


def test_text_filing_store_write_path_matches_config_default():
    assert TextFilingStore()._base_dir == get_sec_text_dir()
