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
