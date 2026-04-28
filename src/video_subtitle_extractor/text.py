from __future__ import annotations

import re
from difflib import SequenceMatcher


_WHITESPACE_RE = re.compile(r"\s+")
_NOISE_RE = re.compile(r"^[\W_]+$", re.UNICODE)


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = _WHITESPACE_RE.sub("", text)
    text = text.strip()
    return text


def is_noise(text: str) -> bool:
    text = clean_text(text)
    if not text:
        return True
    if _NOISE_RE.match(text):
        return True
    return False


def text_similarity(left: str, right: str) -> float:
    left = clean_text(left)
    right = clean_text(right)
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def choose_better_text(left: str, right: str) -> str:
    left_clean = clean_text(left)
    right_clean = clean_text(right)
    if len(right_clean) > len(left_clean):
        return right_clean
    return left_clean
