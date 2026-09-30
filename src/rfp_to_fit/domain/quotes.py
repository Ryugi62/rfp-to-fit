"""인용 실재 검사 — LLM이 댄 인용이 원문에 실제로 있는지 문자열로 확인한다(환각 차단)."""
from __future__ import annotations

import re

_STRIP = re.compile(r"[\s\*\#\>\|\-\·\,\.\:\;\"\'\“\”\‘\’\(\)\[\]「」『』…~`_]+")


def normalize(text: str) -> str:
    return _STRIP.sub("", text or "")


def verify_quote(quote: str, source: str, min_len: int = 4) -> bool:
    q = normalize(quote)
    if len(q) < min_len:
        return False
    return q in normalize(source)


_WORD = re.compile(r"[0-9A-Za-z가-힣]+")


def verify_quote_loose(quote: str, source: str, min_ratio: float = 0.85) -> bool:
    """표처럼 셀 순서가 섞이는 원문용: 인용의 낱말(2자 이상·숫자)이 그 쪽에 85% 이상 있으면 통과.
    공고 파싱에만 쓴다. 초안 인용(환각 차단)은 연속 문자열 검사(verify_quote)만 쓴다."""
    if verify_quote(quote, source):
        return True
    words = [w for w in _WORD.findall(quote or "") if len(w) >= 2 or w.isdigit()]
    if len(words) < 3:
        return False
    src = normalize(source)
    hit = sum(1 for w in words if w in src)
    return hit / len(words) >= min_ratio
