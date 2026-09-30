"""RFP-to-Fit 도메인 모델 — 순수 파이썬(외부 import 없음). 이름은 SPEC.md 유비쿼터스 언어와 1:1."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class Evidence:
    source: str          # 문서 id (예: rfp, draft)
    page: int | None     # 공고 쪽 번호(1부터). 초안이면 None
    quote: str           # 원문에 실제로 있는 짧은 인용


@dataclass(frozen=True)
class Requirement:
    id: str
    category: str        # 자격|제출서류|기간|형식|제한|기타
    text: str
    evidence: Evidence


@dataclass(frozen=True)
class Criterion:
    id: str
    name: str
    points: float
    description: str
    evidence: Evidence
    stage: str = "단일"


@dataclass(frozen=True)
class CheckItem:
    id: str
    criterion_id: str
    question: str


@dataclass(frozen=True)
class ReviewerPersona:
    id: str
    name: str
    lens: str            # 무엇을 먼저 보는가(역할 유형 — 특정인 모델링 금지)
    model: str = ""      # 이 평가위원을 돌리는 LLM(독립성 = 모델 다양성)


class VerdictLabel(str, Enum):
    MET = "충족"
    WEAK = "부족"
    MISSING = "누락"


VALUE = {VerdictLabel.MET: 1.0, VerdictLabel.WEAK: 0.5, VerdictLabel.MISSING: 0.0}


@dataclass(frozen=True)
class Verdict:
    reviewer_id: str
    item_id: str
    label: VerdictLabel
    quote: str           # 초안 인용(충족·부족이면 필수)
    reason: str


class FindingKind(str, Enum):
    CONSENSUS_GAP = "합의 결핍"
    CONTESTED = "논쟁 지점"
    MET = "충족"
    UNVERIFIABLE = "확인 불가"


@dataclass
class Finding:
    item_id: str
    kind: FindingKind
    gap_ratio: float
    valid: int
    demoted: int
    verdicts: list[Verdict] = field(default_factory=list)


@dataclass
class FitRow:
    criterion: Criterion
    expected_points: float
    per_reviewer: dict[str, float]
    findings: list[Finding]

    @property
    def spread(self) -> float:
        vals = list(self.per_reviewer.values())
        return (max(vals) - min(vals)) if vals else 0.0


@dataclass
class FitTable:
    rows: list[FitRow]

    @property
    def total_points(self) -> float:
        return sum(r.criterion.points for r in self.rows)

    @property
    def expected_total(self) -> float:
        return sum(r.expected_points for r in self.rows)

    def findings(self, kind: FindingKind) -> list[Finding]:
        return [f for r in self.rows for f in r.findings if f.kind == kind]


@dataclass(frozen=True)
class RemedyItem:
    item_id: str
    evidence_type: str   # 수치|선행연구|일정|조직·역할|절차|데이터|기타
    location: str        # 넣을 위치(초안의 절 이름)
    why: str             # 왜 필요한가(지표 원문 근거)
