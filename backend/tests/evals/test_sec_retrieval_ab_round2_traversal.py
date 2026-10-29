from __future__ import annotations


def test_visible_text_ignores_non_visible_content_and_preserves_reading_order() -> None:
    try:
        from backend.evals.scenarios.sec_retrieval_ab.curation.round2_traversal import (
            visible_text,
        )
    except ImportError:
        actual = None
    else:
        actual = visible_text(
            """
            <html><head><style>.secret { display: none }</style></head><body>
              <h1>Annual &amp; Report</h1>
              <ix:hidden><p>duplicate hidden fact</p></ix:hidden>
              <p>First <b>visible</b> paragraph.</p>
              <script>ignore_me()</script>
              <table><tr><td>Cell A</td><td>Cell B</td></tr></table>
            </body></html>
            """
        )

    assert actual == "Annual & Report\n\nFirst visible paragraph.\n\nCell A | Cell B"


def test_visible_text_does_not_count_void_elements_toward_hidden_depth() -> None:
    from backend.evals.scenarios.sec_retrieval_ab.curation.round2_traversal import (
        visible_text,
    )

    actual = visible_text(
        """
        <html>
          <head><meta charset="utf-8"><style>.hidden { display: none }</style></head>
          <body><p>Visible filing text.</p></body>
        </html>
        """
    )

    assert actual == "Visible filing text."


def test_extract_primary_10k_selects_exact_form_from_complete_submission() -> None:
    from backend.evals.scenarios.sec_retrieval_ab.curation.round2_traversal import (
        extract_primary_10k,
    )

    submission = """
    <DOCUMENT>
    <TYPE>EX-99.1
    <FILENAME>release.htm
    <TEXT><html>release</html></TEXT>
    </DOCUMENT>
    <DOCUMENT>
    <TYPE>10-K
    <FILENAME>axon-20251231.htm
    <TEXT><html><body>annual report</body></html></TEXT>
    </DOCUMENT>
    """

    filename, document = extract_primary_10k(submission)

    assert filename == "axon-20251231.htm"
    assert document == "<html><body>annual report</body></html>"


def test_neutral_windows_cover_text_once_without_gaps_or_overlaps() -> None:
    from backend.evals.scenarios.sec_retrieval_ab.curation.round2_traversal import (
        neutral_windows,
    )

    windows = neutral_windows("abcdefghij", window_size=4)

    assert [(window.start, window.end) for window in windows] == [
        (0, 4),
        (4, 8),
        (8, 10),
    ]
    assert "".join(window.text for window in windows) == "abcdefghij"
    assert [window.window_id for window in windows] == ["W0001", "W0002", "W0003"]


def test_extract_primary_10k_removes_edgar_xbrl_transport_wrapper() -> None:
    from backend.evals.scenarios.sec_retrieval_ab.curation.round2_traversal import (
        extract_primary_10k,
    )

    submission = """
    <DOCUMENT>
    <TYPE>10-K
    <FILENAME>annual.htm
    <TEXT><XBRL><html><body>annual report</body></html></XBRL></TEXT>
    </DOCUMENT>
    """

    _, document = extract_primary_10k(submission)

    assert document == "<html><body>annual report</body></html>"
