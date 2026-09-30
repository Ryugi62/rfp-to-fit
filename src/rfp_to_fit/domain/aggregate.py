"""독립 판정 → 합의 결핍 / 논쟁 지점 / 충족 / 확인 불가 집계와 심사기준 대조표."""
from __future__ import annotations

from .model import (
    VALUE, CheckItem, Criterion, Finding, FindingKind, FitRow, FitTable,
    ReviewerPersona, Verdict, VerdictLabel,
)
from .quotes import verify_quote

CONSENSUS = 0.8
CONTEST = 0.2


def effective_label(v: Verdict, draft: str) -> VerdictLabel | None:
    """인용 검사 후 유효 라벨. 충족인데 인용이 없거나 가짜면 None(강등), 부족인데 인용이 가짜면 누락."""
    if v.label == VerdictLabel.MET:
        return v.label if verify_quote(v.quote, draft) else None
    if v.label == VerdictLabel.WEAK and not verify_quote(v.quote, draft):
        return VerdictLabel.MISSING
    return v.label


def aggregate_item(item_id: str, verdicts: list[Verdict], draft: str) -> Finding:
    labels = [effective_label(v, draft) for v in verdicts]
    valid = [l for l in labels if l is not None]
    demoted = len(labels) - len(valid)
    if not verdicts or len(valid) * 2 < len(verdicts):
        return Finding(item_id, FindingKind.UNVERIFIABLE, 0.0, len(valid), demoted, verdicts)
    gaps = sum(1 for l in valid if l != VerdictLabel.MET)
    ratio = gaps / len(valid)
    if ratio >= CONSENSUS:
        kind = FindingKind.CONSENSUS_GAP
    elif ratio > CONTEST:
        kind = FindingKind.CONTESTED
    else:
        kind = FindingKind.MET
    return Finding(item_id, kind, ratio, len(valid), demoted, verdicts)


def trimmed_mean(vals: list[float]) -> float:
    """실제 심사처럼 5명 이상이면 최고점·최저점을 하나씩 빼고 평균한다."""
    if not vals:
        return 0.0
    v = sorted(vals)
    if len(v) >= 5:
        v = v[1:-1]
    return sum(v) / len(v)


def build_fit_table(criteria: list[Criterion], items: list[CheckItem], personas: list[ReviewerPersona],
                    verdicts: list[Verdict], draft: str) -> FitTable:
    rows = []
    for c in criteria:
        c_items = [i for i in items if i.criterion_id == c.id]
        findings = [aggregate_item(i.id, [v for v in verdicts if v.item_id == i.id], draft) for i in c_items]
        per = {}
        for p in personas:
            vals = []
            for i in c_items:
                mine = [v for v in verdicts if v.item_id == i.id and v.reviewer_id == p.id]
                if not mine:
                    continue
                lab = effective_label(mine[0], draft)
                vals.append(VALUE[lab] if lab is not None else 0.0)
            if vals:
                per[p.id] = sum(vals) / len(vals) * c.points
        expected = trimmed_mean(list(per.values()))
        rows.append(FitRow(c, expected, per, findings))
    return FitTable(rows)
