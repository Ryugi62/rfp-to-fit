"""① 공고 파싱 — 요건·평가지표를 쪽 번호와 인용문으로 뽑고, 인용이 그 쪽에 없으면 버린다."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.model import Criterion, Evidence, Requirement
from ..domain.quotes import verify_quote
from .ports import LLM, Document

SYSTEM = (
    "너는 국가 R&D 공고문을 읽는 전문기관 담당자다. 공고 원문에 있는 것만 뽑는다. 추측·보충 금지. "
    "모든 항목에 원문 쪽 번호(page)와 그 쪽에 실제로 있는 짧은 인용(quote, 10~40자, 원문 그대로 복사)을 단다. JSON만 출력한다."
)

PROMPT = """아래는 공고문을 쪽 단위로 표시한 텍스트다. [p.N] 표시가 쪽 번호다.

두 가지를 뽑아라.
1) requirements: 신청자가 지키지 않으면 탈락·감점·불이익이 생기는 요건(신청 자격, 참여 제한, 필수 제출서류, 마감 일시, 분량·서식 규정, 중복 지원 제한 등). 한 요건 = 한 행.
   category는 자격|제출서류|기간|형식|제한|기타 중 하나.
2) criteria: 평가항목(심사기준) 표의 대항목 행. name(원문 항목명), points(배점 숫자), description(원문 설명), stage(예선|본선|서면|발표|단일).

출력 형식:
{{"requirements":[{{"category":"","text":"","page":1,"quote":""}}],
  "criteria":[{{"name":"","points":0,"description":"","stage":"단일","page":1,"quote":""}}]}}

{extra}
공고문:
{body}"""


@dataclass
class Extraction:
    requirements: list[Requirement]
    criteria: list[Criterion]
    dropped: list[dict] = field(default_factory=list)   # 인용 검사 탈락(환각 의심)


def page_tagged(doc: Document) -> str:
    return "\n\n".join(f"[p.{i + 1}]\n{t}" for i, t in enumerate(doc.pages))


def _quote_ok(doc: Document, page, quote: str) -> int | None:
    """인용이 그 쪽(±1쪽 허용 — 표가 쪽 경계에 걸림)에 있으면 실제 쪽 번호를 돌려준다."""
    try:
        p = int(page)
    except (TypeError, ValueError):
        p = None
    order = [p, p - 1, p + 1] if p else []
    for cand in order:
        if cand and 1 <= cand <= len(doc.pages) and verify_quote(quote, doc.pages[cand - 1]):
            return cand
    for i, t in enumerate(doc.pages):   # 쪽 번호만 틀린 경우: 어디든 있으면 그 쪽으로 교정
        if verify_quote(quote, t):
            return i + 1
    return None


def extract_rfp(doc: Document, llm: LLM, extra_criteria: list[Criterion] | None = None) -> Extraction:
    data = llm.complete_json(SYSTEM, PROMPT.format(body=page_tagged(doc), extra=""))
    reqs, crits, dropped = [], [], []
    for i, r in enumerate(data.get("requirements", []), 1):
        page = _quote_ok(doc, r.get("page"), r.get("quote", ""))
        if page is None:
            dropped.append({"kind": "requirement", **r})
            continue
        reqs.append(Requirement(f"R{len(reqs) + 1}", r.get("category", "기타"), r.get("text", ""),
                                Evidence(doc.id, page, r.get("quote", ""))))
    for c in data.get("criteria", []):
        page = _quote_ok(doc, c.get("page"), c.get("quote", ""))
        if page is None:
            dropped.append({"kind": "criterion", **c})
            continue
        try:
            pts = float(c.get("points", 0))
        except (TypeError, ValueError):
            pts = 0.0
        crits.append(Criterion(f"C{len(crits) + 1}", c.get("name", ""), pts, c.get("description", ""),
                               Evidence(doc.id, page, c.get("quote", "")), c.get("stage", "단일") or "단일"))
    for c in extra_criteria or []:
        crits.append(Criterion(f"C{len(crits) + 1}", c.name, c.points, c.description, c.evidence, c.stage))
    return Extraction(reqs, crits, dropped)
