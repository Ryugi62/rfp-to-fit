"""개인정보 가림 — 초안을 외부 LLM에 보내기 전에 주민번호·전화·이메일·생년월일을 가린다(기획서 윤리 약속)."""
from __future__ import annotations

import re

_RULES = [
    ("주민번호", re.compile(r"\b\d{6}\s*-\s*[1-4]\d{6}\b")),
    ("전화", re.compile(r"\b0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b")),
    ("이메일", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("생년월일", re.compile(r"\b(?:19|20)?\d{2}\s*[.\-/년]\s*\d{1,2}\s*[.\-/월]\s*\d{1,2}\s*[.일]?(?=\s*(?:\n|$|생|\)))")),
]


def mask_pii(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for name, rx in _RULES:
        text, n = rx.subn(f"[{name} 가림]", text)
        if n:
            counts[name] = n
    return text, counts
