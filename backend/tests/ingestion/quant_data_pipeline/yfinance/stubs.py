"""Test stubs for the yfinance client.

Provides a minimal ``TickerLike`` implementation usable across yfinance
subsystem tests. Kept deliberately small in Task 3 — later tasks (dto_builder,
refresh_orchestrator) can extend it without touching this file's public shape.
"""

from dataclasses import dataclass, field

import pandas as pd

from backend.ingestion.quant_data_pipeline.yfinance.yfinance_client import (
    TickerFactory,
    TickerLike,
)


@dataclass
class StubTicker:
    """Minimal ``TickerLike`` implementation for tests.

    Set ``raise_on_attrs`` to ``{"info": SomeError(...)}`` to make access to
    ``stub.info`` raise that exception — used by ``_classify`` tests so each
    fetch-path can exercise its error-mapping branch.
    """

    info: dict = field(default_factory=dict)
    quarterly_income_stmt: pd.DataFrame = field(default_factory=pd.DataFrame)
    quarterly_balance_sheet: pd.DataFrame = field(default_factory=pd.DataFrame)
    quarterly_cashflow: pd.DataFrame = field(default_factory=pd.DataFrame)
    income_stmt: pd.DataFrame = field(default_factory=pd.DataFrame)
    balance_sheet: pd.DataFrame = field(default_factory=pd.DataFrame)
    cashflow: pd.DataFrame = field(default_factory=pd.DataFrame)
    raise_on_attrs: dict[str, Exception] = field(default_factory=dict)

    def __getattribute__(self, name: str):
        # Guard against accessing raise_on_attrs before dataclass init populates
        # __dict__ — without this, the dataclass-generated __init__ would
        # recurse infinitely when assigning the first field.
        raw_dict = object.__getattribute__(self, "__dict__")
        raise_on_attrs = raw_dict.get("raise_on_attrs", {})
        if name in raise_on_attrs:
            raise raise_on_attrs[name]
        return object.__getattribute__(self, name)


def make_stub_factory(stub: StubTicker) -> TickerFactory:
    """Return a ``TickerFactory`` that always returns the given stub."""

    def _factory(_ticker: str) -> TickerLike:
        return stub  # type: ignore[return-value]

    return _factory
