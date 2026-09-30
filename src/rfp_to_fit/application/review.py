"""③ 점검 항목 생성 · 가상 평가위원 독립 채점 · ⑤ 보완 지정."""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

from ..domain.model import (
    CheckItem, Criterion, Finding, FindingKind, RemedyItem, ReviewerPersona, ReviewerStance, Verdict, VerdictLabel,
)
from .ports import LLM

# ---------- 점검 항목 ----------
RUBRIC_SYSTEM = "너는 국가 R&D 평가위원 교육 담당자다. 평가지표 원문만 근거로 점검 질문을 만든다. 특정 표현·어휘를 권하지 않는다. JSON만 출력한다."
RUBRIC_PROMPT = """아래 평가지표마다 심사위원이 제안서(기획서) 본문을 읽으며 확인할 점검 질문을 3개 만들어라.
- 질문은 평가지표 설명 원문의 요소를 하나씩 쪼갠 것이다. 예: 「창의성 및 차별성」 → 기존 방법과의 비교 대상 제시 / 새로운 핵심 기제 / 그 근거.
- 공고의 작성 요건 중 이 지표와 내용이 겹치는 것(예: 「AI 윤리 및 신뢰성」 작성 항목 → 윤리성 지표)은 질문에 반영한다.
- 제외: 신청서 서식·분야 표시·제출 여부·발표자료·프로토타입 제출처럼 제안서 본문 밖의 행정 요건(요건 매트릭스가 따로 본다).
- 한 지표의 3개 질문은 서로 다른 근거 종류(수치·방법·일정·주체·비교 대상·위험 대응 등)를 묻는다.
- 막연한 질문 금지. 나쁜 예: 「혁신성을 확인할 수 있는 근거가 있는가」. 좋은 예: 「기존 도구·방법과 무엇이 다른지 비교 대상을 들어 제시하는가」.
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
    "(3) 충족·부족 판정에는 제안서 본문에서 한 글자도 바꾸지 않고 복사한 연속 구간(quote, 10~40자)을 단다. 줄이거나 이어 붙이거나 질문 문장을 인용하면 무효다. 인용할 곳이 없으면 누락이다. "
    "(4) 관대하지 않게, 실제 심사처럼 판정한다. JSON만 출력한다."
)
REVIEW_PROMPT = """평가지표와 점검 질문:
{items}

각 점검 질문마다 판정하라. label은 충족|부족|누락 중 하나.
- 충족: 이 질문에 **직접** 답하는 구체적 근거(수치·방법·일정·주체·비교 대상)가 본문 한 곳에 명시돼 있다.
- 부족: 관련 단어가 나오기만 하거나, 다른 목적의 문장에서 간접적으로 추론해야 하거나, 구체성이 모자라다.
- 누락: 본문에 없다.
실제 심사처럼 엄격하게: 애매하면 충족이 아니라 부족이다.
reason은 심사위원 메모처럼 한 문장(40자 이내).

마지막으로, 실제 심사위원처럼 항목 합산과 별개로 이 제안서에 대한 전체 인상을 정하라:
stance.decision = 선정|보류|탈락, stance.key_point = 너의 관점에서 당락을 가를 한 가지(40자 이내).

출력: {{"verdicts":[{{"item_id":"C1-1","label":"충족","quote":"","reason":""}}],
       "stance":{{"decision":"보류","key_point":""}}}}

제안서 본문:
<<<
{draft}
>>>"""

_LABELS = {l.value: l for l in VerdictLabel}


def rows_of(data, key: str) -> list[dict]:
    """모델이 {key:[...]} 대신 [...]만 돌려줘도 받는다. dict가 아닌 원소는 버린다."""
    rows = data.get(key, []) if isinstance(data, dict) else data
    return [r for r in (rows or []) if isinstance(r, dict)]


def review_one(persona: ReviewerPersona, criteria: list[Criterion], items: list[CheckItem], draft: str, llm: LLM,
               context: str = "", with_stance: bool = False):
    by_id = {c.id: c for c in criteria}
    listing = "\n".join(f"- {i.id} [{by_id[i.criterion_id].name} {by_id[i.criterion_id].points:g}점] {i.question}" for i in items)
    prompt = REVIEW_PROMPT.format(items=listing + (f"\n\n[참고 자료 — 인용 금지]\n{context}" if context else ""), draft=draft)
    data = llm.complete_json(REVIEW_SYSTEM.format(lens=persona.lens), prompt)
    valid_ids = {i.id for i in items}
    out = []
    for v in rows_of(data, "verdicts"):
        if v.get("item_id") not in valid_ids:
            continue
        label = _LABELS.get(str(v.get("label", "")).strip(), VerdictLabel.MISSING)
        out.append(Verdict(persona.id, v["item_id"], label, str(v.get("quote", "") or ""), str(v.get("reason", "") or "")))
    if not with_stance:
        return out
    st = data.get("stance") if isinstance(data, dict) else None
    stance = None
    if isinstance(st, dict) and str(st.get("decision", "")).strip() in ("선정", "보류", "탈락"):
        stance = ReviewerStance(persona.id, str(st["decision"]).strip(), str(st.get("key_point", "") or "")[:80])
    return out, stance


def review_all(personas: list[ReviewerPersona], criteria, items, draft: str, llm_for, context: str = "",
               with_stance: bool = False):
    """평가위원마다 따로 호출한다(서로의 답을 입력으로 받지 않음 — SPEC S2). llm_for(persona) → LLM.
    실패한 평가위원은 순차로 한 번 더 시도하고, 그래도 실패하면 failed에 남긴다(조용히 버리지 않는다).
    with_stance=True면 (verdicts, stances, failed)를 돌려준다."""
    def one(p):
        return review_one(p, criteria, items, draft, llm_for(p), context, True)

    results, stances, failed = [], [], []
    with ThreadPoolExecutor(max_workers=len(personas) or 1) as ex:
        futs = {p.id: ex.submit(one, p) for p in personas}
    retry = []
    for p in personas:
        try:
            vs, stc = futs[p.id].result()
            if not vs:
                raise ValueError("판정 0개")
            results.extend(vs)
            if stc:
                stances.append(stc)
        except Exception:
            retry.append(p)
    for p in retry:   # 한도(429)·형식 오류는 대개 일시적 — 순차로 한 번 더
        try:
            vs, stc = one(p)
            if not vs:
                raise ValueError("판정 0개")
            results.extend(vs)
            if stc:
                stances.append(stc)
        except Exception:
            failed.append(p.id)
    return (results, stances, failed) if with_stance else results


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
            for r in rows_of(data, "remedies") if r.get("item_id") in ids]


# ---------- 재질의(자기 교정) ----------
RECHECK_PROMPT = """너의 이전 판정 중 아래 항목은 인용이 제안서 원문에서 확인되지 않아 무효 처리되었다.
각 항목을 다시 판정하라. 충족·부족이면 제안서 본문에서 한 글자도 바꾸지 않은 연속 구간(10~40자)을 인용하라. 그런 구간이 없으면 누락이다.

항목:
{items}

출력: {{"verdicts":[{{"item_id":"","label":"충족","quote":"","reason":""}}]}}

제안서 본문:
<<<
{draft}
>>>"""


def recheck(personas: list[ReviewerPersona], criteria, items: list[CheckItem], verdicts: list[Verdict], draft: str, llm_for,
            is_invalid) -> list[Verdict]:
    """인용 검사에 걸린 판정만 그 평가위원에게 다시 묻는다(최대 1회). 다른 평가위원의 답은 여전히 보여주지 않는다."""
    by_item = {i.id: i for i in items}
    by_crit = {c.id: c for c in criteria}
    redo: dict[str, list[Verdict]] = {}
    for v in verdicts:
        if is_invalid(v):
            redo.setdefault(v.reviewer_id, []).append(v)
    if not redo:
        return verdicts
    pmap = {p.id: p for p in personas}

    def ask(pid: str, bad: list[Verdict]) -> list[Verdict]:
        p = pmap[pid]
        listing = "\n".join(f"- {v.item_id} [{by_crit[by_item[v.item_id].criterion_id].name}] {by_item[v.item_id].question}" for v in bad)
        data = llm_for(p).complete_json(REVIEW_SYSTEM.format(lens=p.lens), RECHECK_PROMPT.format(items=listing, draft=draft))
        ids = {v.item_id for v in bad}
        return [Verdict(pid, x["item_id"], _LABELS.get(str(x.get("label", "")).strip(), VerdictLabel.MISSING),
                        str(x.get("quote", "") or ""), "[재질의] " + str(x.get("reason", "") or ""))
                for x in rows_of(data, "verdicts") if x.get("item_id") in ids]

    fixed: dict[tuple[str, str], Verdict] = {}
    with ThreadPoolExecutor(max_workers=len(redo)) as ex:
        for fut in [ex.submit(ask, pid, bad) for pid, bad in redo.items()]:
            try:
                for v in fut.result():
                    fixed[(v.reviewer_id, v.item_id)] = v
            except Exception:
                continue
    return [fixed.get((v.reviewer_id, v.item_id), v) for v in verdicts]
