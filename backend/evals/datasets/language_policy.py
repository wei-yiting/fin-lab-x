"""BDD evaluation dataset for language policy compliance."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LangPolicyEvalCase:
    id: str
    description: str
    prompt: str
    prompt_language: str
    expect_tool: str | None
    expect_search_query_no_cjk: bool
    expect_response_cjk_min: float
    expect_response_cjk_max: float


LANGUAGE_POLICY_CASES: list[LangPolicyEvalCase] = [
    # --- Chinese prompt → English search, Chinese response ---
    LangPolicyEvalCase(
        id="LP-01",
        description="Chinese news query -> English search, Chinese response",
        prompt="微軟最近有什麼新聞？",
        prompt_language="zh",
        expect_tool="tavily_financial_search",
        expect_search_query_no_cjk=True,
        expect_response_cjk_min=0.20,
        expect_response_cjk_max=1.0,
    ),
    LangPolicyEvalCase(
        id="LP-02",
        description="Chinese earnings query -> English search, Chinese response",
        prompt="蘋果公司最新的財報表現如何？",
        prompt_language="zh",
        expect_tool="tavily_financial_search",
        expect_search_query_no_cjk=True,
        expect_response_cjk_min=0.20,
        expect_response_cjk_max=1.0,
    ),
    # --- English prompt → English search, English response ---
    LangPolicyEvalCase(
        id="LP-03",
        description="English news query -> English search, English response",
        prompt="What is the latest news about MSFT?",
        prompt_language="en",
        expect_tool="tavily_financial_search",
        expect_search_query_no_cjk=True,
        expect_response_cjk_min=0.0,
        expect_response_cjk_max=0.0,
    ),
    LangPolicyEvalCase(
        id="LP-04",
        description="English performance query -> English search, English response",
        prompt="How is AAPL performing recently?",
        prompt_language="en",
        expect_tool="tavily_financial_search",
        expect_search_query_no_cjk=True,
        expect_response_cjk_min=0.0,
        expect_response_cjk_max=0.0,
    ),
    # --- Chinese prompt → English ticker, Chinese response (no search) ---
    LangPolicyEvalCase(
        id="LP-05",
        description="Chinese price query -> English ticker, Chinese response",
        prompt="特斯拉現在股價多少？",
        prompt_language="zh",
        expect_tool="yfinance_stock_quote",
        expect_search_query_no_cjk=True,
        expect_response_cjk_min=0.20,
        expect_response_cjk_max=1.0,
    ),
    # --- English prompt → English ticker, English response (no search) ---
    LangPolicyEvalCase(
        id="LP-06",
        description="English price query -> English ticker, English response",
        prompt="What is TSLA's current price?",
        prompt_language="en",
        expect_tool="yfinance_stock_quote",
        expect_search_query_no_cjk=True,
        expect_response_cjk_min=0.0,
        expect_response_cjk_max=0.0,
    ),
    # --- Mixed language (CJK present) → English tool args, Chinese response ---
    LangPolicyEvalCase(
        id="LP-07",
        description="Mixed lang query (CJK present) -> English args, Chinese response",
        prompt="NVDA 最近表現如何？",
        prompt_language="zh",
        expect_tool=None,
        expect_search_query_no_cjk=True,
        expect_response_cjk_min=0.20,
        expect_response_cjk_max=1.0,
    ),
    # --- Ticker-only prompt → English args, English response ---
    LangPolicyEvalCase(
        id="LP-08",
        description="Ticker-only prompt -> English args, English response",
        prompt="GOOGL",
        prompt_language="en",
        expect_tool=None,
        expect_search_query_no_cjk=True,
        expect_response_cjk_min=0.0,
        expect_response_cjk_max=0.0,
    ),
]
