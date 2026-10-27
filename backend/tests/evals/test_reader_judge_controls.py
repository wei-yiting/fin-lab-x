from backend.evals.experiments.reader_model_reasoning.judge import (
    mask,
    strip_evidence,
    truncate,
)

ANSWER = (
    "**結論：風險主要來自滑石粉訴訟。**\n\n"
    "公司保留約 34 億美元準備金 [1]。\n"
    "案件數仍可能增加，尾部風險很大。\n"
    "根據 [SEC 10-K Item 7，Johnson & Johnson] 的揭露，管理層無法估計上限。\n"
    "詳見 https://example.com/news 的報導。\n\n"
    "[1]: https://example.com/news\n"
)


def test_strip_evidence_drops_digit_sentences_citations_and_sources():
    stripped = strip_evidence(ANSWER)

    assert "34" not in stripped
    assert "[1]" not in stripped
    assert "https://" not in stripped
    assert "SEC 10-K" not in stripped
    assert "案件數仍可能增加，尾部風險很大。" in stripped
    assert "結論：風險主要來自滑石粉訴訟。" in stripped


def test_truncate_keeps_whole_leading_sentences_only():
    long_answer = "第一句結論。" + "後續論證很長。" * 50

    out = truncate(long_answer, share=0.05)

    assert out.startswith("第一句結論。")
    assert len(out) <= max(len("第一句結論。"), int(len(long_answer) * 0.05))
    assert out.endswith("。")


def test_truncate_keeps_at_least_one_sentence():
    assert (
        truncate("唯一一句很長的結論沒有結尾", share=0.01)
        == "唯一一句很長的結論沒有結尾"
    )


def test_mask_hides_search_chunk_ids():
    assert mask("見 `sec://JNJ/10-K/2025/item7#c12`。") == "見 SEC 10-K excerpt。"
