"""Sentence-boundary segmenter for LLM reasoning text.

Splits a streaming delta feed into discrete sentences so the frontend can
render reasoning incrementally without any language-processing logic on its
side (design doc D3).
"""

from __future__ import annotations

import re
from collections.abc import Iterator


# Matches half-width sentence-ending punctuation (.!?) followed by whitespace.
# The look-behind (?<!\d) prevents splitting on decimal numbers like "3.14".
# Capturing the trailing whitespace (not lookahead) lets us advance past it so
# the next sentence doesn't start with a leading space.
_HALF_WIDTH_BOUNDARY = re.compile(r"(?<!\d)[.!?](\s)")

# Full-width CJK sentence-ending punctuation and newline — terminate immediately
# without requiring trailing whitespace. Named "immediate" because \n is not
# itself full-width punctuation but shares the same no-whitespace-required rule.
_IMMEDIATE_BOUNDARY = re.compile(r"[。！？\n]")


def _split_into_sentences(text: str) -> list[str]:
    """Return (sentence, ..., remainder) pieces after splitting on terminators.

    Each emitted element corresponds to one completed sentence.  The last
    element is always the trailing fragment that has no terminator yet
    (may be an empty string).
    """
    parts: list[str] = []
    pos = 0
    length = len(text)

    while pos < length:
        # Find the earliest boundary from current position.
        hw_match = _HALF_WIDTH_BOUNDARY.search(text, pos)
        im_match = _IMMEDIATE_BOUNDARY.search(text, pos)

        # Determine which boundary comes first.
        if hw_match and im_match:
            if hw_match.start() <= im_match.start():
                first = hw_match
            else:
                first = im_match
        elif hw_match:
            first = hw_match
        elif im_match:
            first = im_match
        else:
            break  # No more boundaries — rest is the trailing fragment.

        terminator_char = text[first.start()]

        if terminator_char == "\n":
            # Strip newline (layout artifact) and a single preceding \r so CRLF
            # input doesn't leak \r into the emitted sentence.
            sentence = text[pos : first.start()]
            if sentence.endswith("\r"):
                sentence = sentence[:-1]
        else:
            # Include the punctuation character in the emitted sentence.
            sentence = text[pos : first.start() + 1]

        # For half-width boundaries the match includes the trailing whitespace
        # (captured group), so first.end() already skips past it — the next
        # sentence won't start with a leading space.
        terminator_end = first.end()

        parts.append(sentence)
        pos = terminator_end

    parts.append(text[pos:])  # Trailing fragment (possibly empty).
    return parts


class ReasoningSegmenter:
    SOFT_EMIT_CHAR_THRESHOLD = 80  # D26 — prevents infinite buffering in CJK text

    def __init__(self) -> None:
        self._buffer: str = ""

    def feed(self, delta: str) -> Iterator[str]:
        """Append delta, yield each completed sentence.

        A sentence is either:
        - terminator-bounded (half-width .!? + whitespace, or full-width 。！？, or \\n), or
        - soft-emitted when the buffer reaches SOFT_EMIT_CHAR_THRESHOLD without
          a terminator (D26 fallback for Gemini 繁中 reasoning with no 。).
        """
        self._buffer += delta
        pieces = _split_into_sentences(self._buffer)

        # All pieces except the last are completed sentences.
        for sentence in pieces[:-1]:
            if sentence:  # Skip empty strings produced by consecutive terminators.
                yield sentence

        remainder = pieces[-1]

        # D26: soft-emit when buffer accumulates ≥ threshold chars with no terminator.
        if len(remainder) >= self.SOFT_EMIT_CHAR_THRESHOLD:
            yield remainder
            self._buffer = ""
        else:
            self._buffer = remainder

    def flush(self) -> str | None:
        """Return and clear the remaining buffer.

        Returns None when the buffer is empty (idempotent).
        """
        content = self._buffer or None
        self._buffer = ""
        return content

    def reset(self) -> None:
        self._buffer = ""
