"""Questions for the answer-language eval: English questions that should pull a
10-K into context, plus Traditional Chinese controls.

``d*`` rows are from ``scenarios/baseline_behavior_diagnostic/dataset.csv``
(SEC/mixed ``expected_best_source``); ``s*`` are the English starter prompts
added in #82; ``z*`` are the matching rows of the zh diagnostic dataset and
the #82 UAT question.
"""

QUESTIONS: list[dict[str, str]] = [
    {
        "qid": "d06",
        "expected_lang": "en",
        "source": "diagnostic#6 SEC",
        "tickers": "JNJ",
        "question": "Analyze Johnson & Johnson's biggest current litigation risk, and distinguish between costs that are already visible and parts that may or may not continue to expand.",
    },
    {
        "qid": "d07",
        "expected_lang": "en",
        "source": "diagnostic#7 mixed",
        "tickers": "GOOGL",
        "question": "With Google's antitrust risk right now, which parts are already happening and which parts are still only potential pressure?",
    },
    {
        "qid": "d08",
        "expected_lang": "en",
        "source": "diagnostic#8 SEC",
        "tickers": "JPM",
        "question": "For a large bank like JPMorgan, do the current regulatory and capital requirements already show signs of long-term damage in the official disclosures?",
    },
    {
        "qid": "d11",
        "expected_lang": "en",
        "source": "diagnostic#11 SEC",
        "tickers": "WMT",
        "question": "How does Walmart itself frame the long-term role of its e-commerce and advertising businesses?",
    },
    {
        "qid": "d12",
        "expected_lang": "en",
        "source": "diagnostic#12 SEC",
        "tickers": "XOM",
        "question": "Analyze how Exxon officially describes energy-transition risk and how that is balanced against shareholder returns.",
    },
    {
        "qid": "d13",
        "expected_lang": "en",
        "source": "diagnostic#13 SEC",
        "tickers": "V|MA",
        "question": "Analyze whether Visa's and Mastercard's official disclosures directly support the claim that regulation will compress the profitability of the card-network business.",
    },
    {
        "qid": "d15",
        "expected_lang": "en",
        "source": "diagnostic#15 SEC",
        "tickers": "COST",
        "question": "What is Costco's real profit engine, and how important is the membership fee?",
    },
    {
        "qid": "d16",
        "expected_lang": "en",
        "source": "diagnostic#16 SEC",
        "tickers": "V",
        "question": "Why is Visa often viewed as a more stable business than a traditional lending bank?",
    },
    {
        "qid": "d17",
        "expected_lang": "en",
        "source": "diagnostic#17 mixed",
        "tickers": "AMZN",
        "question": "Analyze whether Amazon's advertising business should already be considered a high-quality profit engine.",
    },
    {
        "qid": "d18",
        "expected_lang": "en",
        "source": "diagnostic#18 SEC",
        "tickers": "KO|PEP",
        "question": "If you only look at pricing power and business-structure quality, which company looks cleaner: Coca-Cola or Pepsi?",
    },
    {
        "qid": "s1",
        "expected_lang": "en",
        "source": "#82 starter riskVsNews",
        "tickers": "NVDA",
        "question": "Which of the export-control and China risks NVIDIA flags in its latest 10-K are already showing up in recent news, and which are still only potential? Cite the filing and the news for each.",
    },
    {
        "qid": "s2",
        "expected_lang": "en",
        "source": "#82 starter narrativeVsNumbers",
        "tickers": "MSFT",
        "question": "Microsoft attributes its cloud growth to AI demand. Do its revenue growth and gross margin trends support that story, or is AI infrastructure spending eroding margins?",
    },
    {
        "qid": "s3",
        "expected_lang": "en",
        "source": "#82 starter crossCompanyDisclosure",
        "tickers": "AAPL|GOOGL",
        "question": "Compare the antitrust exposure Apple and Alphabet disclose in their latest 10-Ks: which specific cases does each name, and whose revenue is more directly at risk?",
    },
    {
        "qid": "z06",
        "expected_lang": "zh-Hant",
        "source": "diagnostic_zh#6",
        "tickers": "JNJ",
        "question": "分析嬌生最近最大的官司風險，區分已經看得到的成本，和還不確定會不會繼續擴大的部分。",
    },
    {
        "qid": "z11",
        "expected_lang": "zh-Hant",
        "source": "diagnostic_zh#11",
        "tickers": "WMT",
        "question": "沃爾瑪自己怎麼定位電商和廣告業務的長期角色？",
    },
    {
        "qid": "z15",
        "expected_lang": "zh-Hant",
        "source": "diagnostic_zh#15",
        "tickers": "COST",
        "question": "好市多真正的賺錢核心到底是什麼？會員費的重要性有多高？",
    },
    {
        "qid": "zU",
        "expected_lang": "zh-Hant",
        "source": "#82 UAT",
        "tickers": "AAPL|GOOGL",
        "question": "比較蘋果與 Alphabet 最新 10-K 對反壟斷風險的揭露",
    },
]
