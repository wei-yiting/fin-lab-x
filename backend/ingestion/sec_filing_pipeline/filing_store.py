from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Protocol, runtime_checkable

import yaml

from backend.ingestion.sec_filing_pipeline.filing_models import (
    FilingMetadata,
    FilingType,
    ParsedFiling,
)

FRONTMATTER_DELIMITER = "---"


@runtime_checkable
class FilingStore(Protocol):
    def save(self, filing: ParsedFiling) -> None: ...

    def get(
        self, ticker: str, filing_type: FilingType, fiscal_year: int
    ) -> ParsedFiling | None: ...

    def exists(
        self, ticker: str, filing_type: FilingType, fiscal_year: int
    ) -> bool: ...

    def list_filings(self, ticker: str, filing_type: FilingType) -> list[int]: ...


class LocalFilingStore:
    def __init__(self, base_dir: str = "data/sec_filings") -> None:
        self._base_dir = Path(base_dir)

    def _filing_dir(self, ticker: str, filing_type: FilingType) -> Path:
        return self._base_dir / ticker.upper() / str(filing_type)

    def _filing_path(
        self, ticker: str, filing_type: FilingType, fiscal_year: int
    ) -> Path:
        return self._filing_dir(ticker, filing_type) / f"{fiscal_year}.md"

    def save(self, filing: ParsedFiling) -> None:
        ticker = filing.metadata.ticker.upper()
        path = self._filing_path(
            ticker, filing.metadata.filing_type, filing.metadata.fiscal_year
        )
        os.makedirs(path.parent, exist_ok=True)

        meta_dict = filing.metadata.model_dump()
        meta_dict["ticker"] = ticker
        meta_dict["filing_type"] = str(filing.metadata.filing_type)

        frontmatter = yaml.dump(
            meta_dict, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        content = (
            f"{FRONTMATTER_DELIMITER}\n"
            f"{frontmatter}"
            f"{FRONTMATTER_DELIMITER}\n\n"
            f"{filing.markdown_content}"
        )

        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent, suffix=".tmp", prefix=".filing_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def get(
        self, ticker: str, filing_type: FilingType, fiscal_year: int
    ) -> ParsedFiling | None:
        path = self._filing_path(ticker, filing_type, fiscal_year)
        if not path.exists():
            return None

        text = path.read_text(encoding="utf-8")
        metadata, markdown_content = _parse_frontmatter(text)
        return ParsedFiling(metadata=metadata, markdown_content=markdown_content)

    def exists(self, ticker: str, filing_type: FilingType, fiscal_year: int) -> bool:
        return self._filing_path(ticker, filing_type, fiscal_year).exists()

    def list_filings(self, ticker: str, filing_type: FilingType) -> list[int]:
        directory = self._filing_dir(ticker, filing_type)
        if not directory.exists():
            return []

        years: list[int] = []
        for entry in directory.iterdir():
            if entry.suffix != ".md":
                continue
            try:
                years.append(int(entry.stem))
            except ValueError:
                continue
        return sorted(years)


def _parse_frontmatter(text: str) -> tuple[FilingMetadata, str]:
    stripped = text.lstrip("\n")
    if not stripped.startswith(FRONTMATTER_DELIMITER):
        msg = "Missing YAML frontmatter delimiter"
        raise ValueError(msg)

    after_first = stripped[len(FRONTMATTER_DELIMITER) :].lstrip("\n")
    end_idx = after_first.index(FRONTMATTER_DELIMITER)
    yaml_block = after_first[:end_idx]
    body = after_first[end_idx + len(FRONTMATTER_DELIMITER) :].lstrip("\n")

    meta_dict = yaml.safe_load(yaml_block)
    metadata = FilingMetadata(**meta_dict)
    return metadata, body
