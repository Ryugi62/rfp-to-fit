"""① 공고 파싱 — 요건·평가지표를 쪽 번호와 인용문으로 뽑고, 인용이 그 쪽에 없으면 버린다."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.model import Criterion, Evidence, Requirement
from ..domain.quotes import verify_quote_loose as verify_quote
from .ports import LLM, Document

SYSTEM = (
    "너는 국가 R&D 공고문을 읽는 전문기관 담당자다. 공고 원문에 있는 것만 뽑는다. 추측·보충 금지. "
    "모든 항목에 원문 쪽 번호(page)와 그 쪽에 실제로 있는 짧은 인용(quote, 10~40자, 원문 그대로 복사)을 단다. JSON만 출력한다."
)

PROMPT = """아래는 공고문을 쪽 단위로 표시한 텍스트다. [p.N] 표시가 쪽 번호다.

두 가지를 빠짐없이 뽑아라. 적게 뽑는 것이 가장 큰 실패다.
1) requirements: 신청자가 지키지 않으면 탈락·감점·불이익이 생기는 모든 요건. 한 요건 = 한 행으로 잘게 나눈다.
   - 신청 자격·기관 요건·참여 제한(각각 한 행), 접수 방법·시스템, 마감·기간·일정, 제출서류(서류 하나당 한 행, 번호 목록이면 번호마다),
     작성 항목·분량·서식 규정(계획서·기획서 항목마다 한 행), 지원 한도·부담 비율·간접비, 선정 제외·감점 조건(예: 몇 점 미만 제외), 사전조치·위험관리 등 반드시 써야 하는 내용.
   - category는 자격|제출서류|기간|형식|제한|기타 중 하나.
   - consequence: 이 요건을 어기면 원문상 어떻게 되는가 — 탈락|감점|불이익|해당없음. 사업 소개·일반 안내·권고·선정 후 의무처럼 신청 단계에서 어겨도 탈락·감점이 없는 문장은 해당없음.
2) criteria: 평가항목(심사기준) 표의 대항목 행. name은 표 맨 왼쪽 항목명 열의 2~8자 짧은 이름(예: 적합성·혁신성·연구역량) 그대로 — 설명 문구(「~의 명확성 및 ~」)를 name에 넣지 말고 description에 넣는다. points(배점 숫자), description(원문 설명), stage. stage 규칙: 평가 단계가 나뉘면 예선|본선|서면|발표, **평가표가 과제 유형(트랙·분야)별로 따로 있으면 그 유형 이름**(예: 「공동비즈니스형」), 평가표가 하나뿐이면 단일. 한 stage 안의 배점 합은 그 표의 총점과 같아야 한다.
   [표] 아래 행 단위 표가 있으면 그것을 우선 읽는다.

출력 형식:
{{"requirements":[{{"category":"","consequence":"탈락","text":"","page":1,"quote":""}}],
  "criteria":[{{"name":"","points":0,"description":"","stage":"단일","page":1,"quote":""}}]}}

{extra}
공고문:
{body}"""


@dataclass
class Extraction:
    requirements: list[Requirement]
    criteria: list[Criterion]
    dropped: list[dict] = field(default_factory=list)   # 인용 검사 탈락(환각 의심)


FAILURES: list[str] = []


def _safe(llm: LLM, body: str) -> dict:
    for _ in range(2):
        try:
            d = llm.complete_json(SYSTEM, PROMPT.format(body=body, extra=""))
            if isinstance(d, dict):
                return d
        except Exception as e:   # 실패한 묶음은 기록해 화면에 「일부 쪽 미처리」로 드러낸다
            FAILURES.append(f"{body[:12]!r}: {str(e)[:160]}")
    return {}


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


CHUNK = 3


def _chunks(doc: Document, size: int = CHUNK) -> list[str]:
    tagged = [f"[p.{i + 1}]\n{t}" for i, t in enumerate(doc.pages)]
    return ["\n\n".join(tagged[i:i + size]) for i in range(0, len(tagged), size)]


def _dedupe(rows: list[dict], key) -> list[dict]:
    from ..domain.quotes import normalize
    seen, out = set(), []
    for r in rows:
        k = normalize(key(r))[:60]
        if k and k not in seen:
            seen.add(k)
            out.append(r)
    return out


def split_tables(crits: list[Criterion], total: float = 100.0) -> list[Criterion]:
    """한 단계에 평가표 여러 개가 섞여 배점 합이 100을 넘으면, 문서 순서대로 합이 100이 되는 곳에서 끊어 「표1·표2」로 나눈다."""
    from dataclasses import replace
    out: list[Criterion] = []
    for stage in dict.fromkeys(c.stage for c in crits):
        group = [c for c in crits if c.stage == stage]
        if sum(c.points for c in group) <= total + 1e-6:
            out += group
            continue
        n, acc, buf = 1, 0.0, []
        for c in group:
            buf.append(c)
            acc += c.points
            if abs(acc - total) < 1e-6:
                out += [replace(x, stage=f"{stage}·표{n}") for x in buf]
                n, acc, buf = n + 1, 0.0, []
        out += [replace(x, stage=f"{stage}·표{n}") for x in buf]
    return out


def extract_rfp(doc: Document, llm: LLM, extra_criteria: list[Criterion] | None = None) -> Extraction:
    """쪽 묶음(3쪽)마다 병렬로 뽑아 합친다 — 긴 공고에서 뒤쪽 요건이 빠지는 문제를 막는다."""
    from concurrent.futures import ThreadPoolExecutor
    parts = _chunks(doc)
    with ThreadPoolExecutor(max_workers=min(8, len(parts))) as ex:
        results = list(ex.map(lambda body: _safe(llm, body), parts))
    data = {"requirements": _dedupe([r for d in results for r in d.get("requirements", [])], lambda r: r.get("text", "")),
            "criteria": _dedupe([c for d in results for c in d.get("criteria", [])],
                                lambda c: f'{c.get("stage", "")}{c.get("name", "")}{c.get("points", "")}')}
    reqs, crits, dropped = [], [], []
    for i, r in enumerate(data.get("requirements", []), 1):
        page = _quote_ok(doc, r.get("page"), r.get("quote", ""))
        if page is None:
            dropped.append({"kind": "requirement", **r})
            continue
        reqs.append(Requirement(f"R{len(reqs) + 1}", r.get("category", "기타"), r.get("text", ""),
                                Evidence(doc.id, page, r.get("quote", "")), str(r.get("consequence", "") or "").strip()))
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
    return Extraction(reqs, split_tables(crits), dropped)
