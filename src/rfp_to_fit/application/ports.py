"""포트 — 애플리케이션이 바깥(LLM·문서)에 기대하는 인터페이스. 구현은 adapters/."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LLM(Protocol):
    name: str

    def complete_json(self, system: str, prompt: str) -> dict | list: ...


@dataclass(frozen=True)
class Document:
    id: str
    pages: list[str]     # 쪽 단위 텍스트(1쪽 = pages[0])

    @property
    def text(self) -> str:
        return "\n".join(self.pages)
