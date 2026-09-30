"""개인정보 가림 — 초안을 외부 LLM에 보내기 전에 주민번호·전화·이메일·생년월일을 가린다(기획서 윤리 약속)."""
from __future__ import annotations

import re

_DATE = r"(?:19|20)?\d{2}\s*[.\-/년]\s*\d{1,2}\s*[.\-/월]\s*\d{1,2}\s*[.일]?"

# 날짜는 일정·마감에도 흔하다 → 생년월일은 「생년월일·출생·생일」 표지 바로 뒤이거나 「…생」으로 끝날 때만 가린다
_RULES = [
    ("주민번호", re.compile(r"\b\d{6}\s*-\s*[1-4]\d{6}\b"), None),
    ("전화", re.compile(r"\b0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b"), None),
    ("이메일", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), None),
    ("생년월일", re.compile(r"((?:생년월일|출생일?|생일)\s*[:：]?\s*)" + _DATE), r"\1"),
    ("생년월일", re.compile(r"\b" + _DATE + r"(?=\s*생)"), None),
]


def mask_pii(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for name, rx, keep in _RULES:
        text, n = rx.subn((keep or "") + f"[{name} 가림]", text)
        if n:
            counts[name] = counts.get(name, 0) + n
    return text, counts
