"""③ 점검 항목 생성 · 가상 평가위원 독립 채점 · ⑤ 보완 지정."""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

from ..domain.model import (
    CheckItem, Criterion, Finding, FindingKind, RemedyItem, ReviewerPersona, Verdict, VerdictLabel,
)
from .ports import LLM

# ---------- 점검 항목 ----------
RUBRIC_SYSTEM = "너는 국가 R&D 평가위원 교육 담당자다. 평가지표 원문만 근거로 점검 질문을 만든다. 특정 표현·어휘를 권하지 않는다. JSON만 출력한다."
RUBRIC_PROMPT = """아래 평가지표마다 심사위원이 제안서에서 확인할 점검 질문을 3개 만들어라.
- 질문은 지표 설명 원문과 공고의 작성 요건에서 나온 것이어야 하고, 제안서 본문을 읽으면 있다/없다로 확인할 수 있을 만큼 구체적이어야 한다.
  나쁜 예: 「혁신성을 확인할 수 있는 근거가 있는가」(막연함). 좋은 예: 「기존 도구·방법과 무엇이 다른지 비교 대상을 들어 제시하는가」.
- 가능하면 수치·방법·일정·주체·비교 대상처럼 확인 가능한 요소를 묻는다.
- 질문은 「~이 있는가/~하는가」 형태의 한 문장.

평가지표:
{criteria}

공고의 작성 요건(참고):
{guide}

출력: {{"items":[{{"criterion_id":"C1","question":""}}]}}"""


def _flatten_items(data) -> list[tuple[str, str]]:
    """모델마다 모양이 다르다: {items:[{criterion_id, question}]} 또는 {items:[{criterion_id, questions:[...]}]}."""
    rows = data.get("items", []) if isinstance(data, dict) else data
    out = []
    for it in rows or []:
        if not isinstance(it, dict):
            continue
        cid = str(it.get("criterion_id", "")).strip()
        qs = it.get("questions") or ([it["question"]] if it.get("question") else [])
        out += [(cid, q) for q in qs if isinstance(q, str) and q.strip()]
    return out


def build_rubric(criteria: list[Criterion], llm: LLM, guide: str = "") -> list[CheckItem]:
    listing = "\n".join(f"- {c.id} {c.name}({c.points:g}점): {c.description}" for c in criteria)
    data = llm.complete_json(RUBRIC_SYSTEM, RUBRIC_PROMPT.format(criteria=listing, guide=guide or "(없음)"))
    ids = {c.id for c in criteria}
    items, count = [], {}
    for cid, q in _flatten_items(data):
        if cid not in ids:
            continue
        count[cid] = count.get(cid, 0) + 1
        if count[cid] > 3:
            continue
        items.append(CheckItem(f"{cid}-{count[cid]}", cid, q.strip()))
    return items


# ---------- 독립 채점 ----------
REVIEW_SYSTEM = (
    "너는 국가 R&D 과제 평가위원이다. 너의 관점: {lens}\n"
    "규칙: (1) 다른 평가위원의 의견은 모른다. 너 혼자 판단한다. (2) 판정은 제안서 본문에 실제로 적힌 것만 근거로 한다. "
    "(3) 충족·부족 판정에는 제안서에서 그대로 복사한 인용(quote, 10~60자)을 반드시 단다. 인용할 문장이 없으면 누락이다. "
    "(4) 관대하지 않게, 실제 심사처럼 판정한다. JSON만 출력한다."
)
REVIEW_PROMPT = """평가지표와 점검 질문:
{items}

각 점검 질문마다 판정하라. label은 충족|부족|누락 중 하나.
- 충족: 질문에 대한 구체적 근거(수치·방법·일정·주체)가 본문에 있다.
- 부족: 언급은 있으나 구체성이 모자라 감점될 수준이다.
- 누락: 본문에 없다.
reason은 심사위원 메모처럼 한 문장(40자 이내).

출력: {{"verdicts":[{{"item_id":"C1-1","label":"충족","quote":"","reason":""}}]}}

제안서 본문:
<<<
{draft}
>>>"""

_LABELS = {l.value: l for l in VerdictLabel}


def review_one(persona: ReviewerPersona, criteria: list[Criterion], items: list[CheckItem], draft: str, llm: LLM) -> list[Verdict]:
    by_id = {c.id: c for c in criteria}
    listing = "\n".join(f"- {i.id} [{by_id[i.criterion_id].name} {by_id[i.criterion_id].points:g}점] {i.question}" for i in items)
    data = llm.complete_json(REVIEW_SYSTEM.format(lens=persona.lens), REVIEW_PROMPT.format(items=listing, draft=draft))
    valid_ids = {i.id for i in items}
    out = []
    for v in data.get("verdicts", []):
        if v.get("item_id") not in valid_ids:
            continue
        label = _LABELS.get(str(v.get("label", "")).strip(), VerdictLabel.MISSING)
        out.append(Verdict(persona.id, v["item_id"], label, str(v.get("quote", "") or ""), str(v.get("reason", "") or "")))
    return out


def review_all(personas: list[ReviewerPersona], criteria, items, draft: str, llm_for) -> list[Verdict]:
    """평가위원마다 따로 호출한다(서로의 답을 입력으로 받지 않음 — SPEC S2). llm_for(persona) → LLM."""
    with ThreadPoolExecutor(max_workers=len(personas) or 1) as ex:
        futs = [ex.submit(review_one, p, criteria, items, draft, llm_for(p)) for p in personas]
        results = []
        for f in futs:
            try:
                results.extend(f.result())
            except Exception:   # 한 평가위원이 실패해도 나머지로 집계(확인 불가로 드러남)
                continue
    return results


# ---------- 보완 지정 ----------
REMEDY_SYSTEM = (
    "너는 연구기획 코치다. 제안서 문장을 대신 쓰지 않는다. 무엇을(근거 종류) 어디에(절) 넣어야 하는지만 지정한다. JSON만 출력한다."
)
REMEDY_PROMPT = """아래 결핍 항목마다 보완 지정을 하나씩 만들어라.
- evidence_type: 수치|선행연구|일정|조직·역할|절차|데이터|기타 중 하나
- location: 제안서의 어느 절에 넣을지(아래 절 목록 중 하나, 없으면 「새 절」)
- why: 왜 필요한지 평가지표 원문을 들어 한 문장(50자 이내). 제안서에 넣을 문장 예시는 쓰지 마라.

결핍 항목:
{gaps}

제안서 절 목록:
{sections}

출력: {{"remedies":[{{"item_id":"","evidence_type":"","location":"","why":""}}]}}"""

_HEAD = re.compile(r"^\s{0,3}(#{1,4})\s+(.+)$|^\s*(\d+\))\s*(.+)$", re.M)


def sections_of(draft: str) -> list[str]:
    out = []
    for m in _HEAD.finditer(draft):
        title = (m.group(2) or f"{m.group(3)} {m.group(4)}").strip()
        out.append(title[:40])
    return out or ["본문"]


def remedy(findings: list[Finding], items: list[CheckItem], criteria: list[Criterion], draft: str, llm: LLM) -> list[RemedyItem]:
    targets = [f for f in findings if f.kind in (FindingKind.CONSENSUS_GAP, FindingKind.CONTESTED)]
    if not targets:
        return []
    by_item = {i.id: i for i in items}
    by_crit = {c.id: c for c in criteria}
    gaps = "\n".join(
        f"- {f.item_id} [{by_crit[by_item[f.item_id].criterion_id].name}] {by_item[f.item_id].question} ({f.kind.value})"
        for f in targets)
    data = llm.complete_json(REMEDY_SYSTEM, REMEDY_PROMPT.format(gaps=gaps, sections="\n".join(f"- {s}" for s in sections_of(draft))))
    ids = {f.item_id for f in targets}
    return [RemedyItem(r["item_id"], r.get("evidence_type", "기타"), r.get("location", "새 절"), r.get("why", ""))
            for r in data.get("remedies", []) if r.get("item_id") in ids]
