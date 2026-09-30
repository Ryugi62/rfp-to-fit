"""② 선행 탐색 — 초안에서 영문 검색어를 뽑아 검색 포트(MCP)로 선행연구를 찾고, 평가위원에게 참고 목록으로 준다."""
from __future__ import annotations

from typing import Protocol

from .ports import LLM

KW_SYSTEM = "너는 연구 문헌 검색 전문가다. JSON만 출력한다."
KW_PROMPT = """아래 제안서가 해결하려는 문제와 방법을 그대로 겨냥하는 영문 학술 검색어 2개를 만들어라.
각 3~5단어, 논문 제목에 나올 법한 구체적 표현(예: "LLM peer review grant proposals"). 일반어(multi-agent system 등) 단독 금지.
출력: {{"queries":["",""]}}

제안서 앞부분:
{head}"""


class PriorArtSearch(Protocol):
    name: str

    def search(self, query: str, n: int = 5) -> list[dict]: ...


FILTER_PROMPT = """제안서 요약과 논문 제목 목록이다. 제안서의 문제·방법과 직접 관련된 논문의 번호만 골라라(관련 없으면 빈 목록).
출력: {{"keep":[0,2]}}

제안서 요약:
{head}

논문:
{titles}"""


def find_prior_art(draft: str, llm: LLM, search: PriorArtSearch, per_query: int = 8) -> tuple[list[str], list[dict]]:
    data = llm.complete_json(KW_SYSTEM, KW_PROMPT.format(head=draft[:2500]))
    qs = [q for q in (data.get("queries", []) if isinstance(data, dict) else []) if isinstance(q, str) and q.strip()][:2]
    seen, works = set(), []
    for q in qs:
        try:
            for w in search.search(q, per_query):
                key = w.get("doi") or w.get("title")
                if key and key not in seen:
                    seen.add(key)
                    works.append({**w, "query": q})
        except Exception:
            continue
    if works:   # 키워드 검색은 잡음이 많다 → 제목으로 관련성만 걸러낸다(판정이 아니라 참고 자료 선별)
        titles = "\n".join(f"{i}. {w['title']}" for i, w in enumerate(works))
        try:
            keep = llm.complete_json(KW_SYSTEM, FILTER_PROMPT.format(head=draft[:1200], titles=titles))
            idx = [int(i) for i in (keep.get("keep", []) if isinstance(keep, dict) else []) if str(i).isdigit()]
            works = [works[i] for i in idx if 0 <= i < len(works)]
        except Exception:
            pass
    return qs, works[:6]


def as_context(works: list[dict]) -> str:
    if not works:
        return ""
    lines = [f"- {w['title']} ({w.get('year')}, {w.get('doi') or 'DOI 없음'})" for w in works]
    return ("참고: 공개 학술 DB(OpenAlex)에서 찾은 관련 선행연구다. 혁신성·차별성 판정 때 제안서가 이들과 무엇이 다른지 "
            "밝히는지만 본다(목록 자체를 인용하지 마라).\n" + "\n".join(lines))
