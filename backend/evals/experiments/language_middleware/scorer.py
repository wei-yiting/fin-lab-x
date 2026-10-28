"""Deterministic answer-language scorer (no LLM).

Script counts decide CJK vs Latin; for Latin-script answers, function-word
counts separate English from the Romance/Germanic languages the bug produced
(Spanish was observed). Chinese answers reuse the ``language_policy``
scenario's Simplified-character check.
"""

from __future__ import annotations

import re
from typing import Any

from backend.evals.scenarios.language_policy.scorer import response_no_simplified_chars

_HAN = re.compile(r"[一-鿿㐀-䶿豈-﫿]")
_KANA = re.compile(r"[぀-ヿ]")
_HANGUL = re.compile(r"[가-힯]")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")
_LATIN_WORD = re.compile(r"[A-Za-zÀ-ÿ]+")
# Markdown link targets and bare URLs carry English words regardless of the
# answer language, so they are stripped before counting.
_URL = re.compile(r"\(https?://[^)]*\)|https?://\S+|\[\d+\]:.*$", re.M)

_STOPWORDS = {
    "en": {
        "the",
        "and",
        "of",
        "to",
        "is",
        "in",
        "that",
        "for",
        "are",
        "with",
        "this",
        "its",
        "it",
        "as",
        "which",
        "on",
        "by",
        "but",
        "not",
        "be",
    },
    "es": {
        "el",
        "la",
        "los",
        "las",
        "de",
        "del",
        "que",
        "y",
        "en",
        "es",
        "por",
        "para",
        "con",
        "una",
        "un",
        "su",
        "sus",
        "como",
        "más",
        "pero",
    },
    "pt": {
        "o",
        "os",
        "da",
        "do",
        "das",
        "dos",
        "que",
        "e",
        "em",
        "não",
        "uma",
        "um",
        "para",
        "com",
        "mais",
        "seu",
        "sua",
        "como",
    },
    "fr": {
        "le",
        "la",
        "les",
        "des",
        "du",
        "et",
        "est",
        "une",
        "un",
        "que",
        "pour",
        "dans",
        "sur",
        "pas",
        "avec",
        "ses",
        "qui",
    },
    "de": {
        "der",
        "die",
        "das",
        "und",
        "ist",
        "nicht",
        "mit",
        "den",
        "dem",
        "ein",
        "eine",
        "für",
        "auf",
        "zu",
        "von",
        "sich",
    },
    "it": {
        "il",
        "lo",
        "gli",
        "della",
        "di",
        "che",
        "e",
        "è",
        "per",
        "una",
        "un",
        "con",
        "non",
        "sono",
        "come",
        "più",
    },
}

# An English answer may quote a few Han characters (e.g. a company's Chinese
# name); more than this share of letters means the answer drifted.
_MAX_HAN_SHARE_FOR_EN = 0.02
_MIN_HAN_SHARE_FOR_ZH = 0.30


def detect_language(text: str) -> dict[str, Any]:
    body = _URL.sub(" ", text)
    han = len(_HAN.findall(body))
    kana = len(_KANA.findall(body))
    hangul = len(_HANGUL.findall(body))
    cyrillic = len(_CYRILLIC.findall(body))
    words = [w.lower() for w in _LATIN_WORD.findall(body)]
    latin_letters = sum(len(w) for w in words)
    # Weight a CJK character as ~2 Latin letters of content so ratios are
    # comparable across scripts.
    cjk_units = 2 * (han + kana + hangul)
    total = cjk_units + latin_letters
    han_share = (2 * han / total) if total else 0.0
    stop_counts = {
        lang: sum(1 for w in words if w in sw) for lang, sw in _STOPWORDS.items()
    }

    if total == 0:
        detected = "empty"
    elif kana >= 10 and kana >= 0.1 * (han + kana):
        detected = "ja"
    elif hangul >= 10:
        detected = "ko"
    elif cyrillic > latin_letters:
        detected = "ru"
    elif cjk_units > latin_letters:
        detected = "zh"
    else:
        best = max(stop_counts, key=lambda k: stop_counts[k])
        detected = best if stop_counts[best] > 0 else "latin-unknown"
    return {
        "detected": detected,
        "han": han,
        "kana": kana,
        "hangul": hangul,
        "cyrillic": cyrillic,
        "latin_letters": latin_letters,
        "han_share": round(han_share, 4),
        "stopwords": stop_counts,
    }


def score_answer(response: str | None, expected_lang: str) -> dict[str, Any]:
    if not response:
        return {"pass": False, "detected": "no_answer", "reason": "empty or errored"}
    info = detect_language(response)
    if expected_lang == "en":
        ok = (
            info["detected"] == "en"
            and info["han_share"] <= _MAX_HAN_SHARE_FOR_EN
            and info["kana"] == 0
            and info["hangul"] == 0
        )
        if info["detected"] == "zh":
            simp = response_no_simplified_chars(
                {"response": response}, {"cjk_min": 0.3}, input=None
            )
            info["detected"] = (
                "zh-Hant" if simp is not None and simp.score == 1 else "zh-Hans"
            )
        return {"pass": ok, **info}
    simp = response_no_simplified_chars(
        {"response": response}, {"cjk_min": 0.3}, input=None
    )
    is_traditional = simp is not None and simp.score == 1
    if info["detected"] == "zh":
        info["detected"] = "zh-Hant" if is_traditional else "zh-Hans"
    ok = info["detected"] == "zh-Hant" and info["han_share"] >= _MIN_HAN_SHARE_FOR_ZH
    return {
        "pass": ok,
        "simplified_check": simp.metadata if simp is not None else None,
        **info,
    }
