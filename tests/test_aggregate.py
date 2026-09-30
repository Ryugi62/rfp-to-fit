from rfp_to_fit.domain.aggregate import aggregate_item, build_fit_table, effective_label, trimmed_mean
from rfp_to_fit.domain.model import (
    CheckItem, Criterion, Evidence, FindingKind, ReviewerPersona, Verdict, VerdictLabel,
)

DRAFT = "정확도 목표: 요건 추출 재현율 90% 이상. 일정: 10월 1일 제출."
REAL = "요건 추출 재현율 90%"
FAKE = "정밀도 99%를 이미 달성했다"


def v(rid, label, quote=""):
    return Verdict(rid, "C1-1", label, quote, "r")


# ---------- trimmed_mean ----------
def test_trimmed_mean_no_trim_below_five():
    assert trimmed_mean([0, 100]) == 50
    assert trimmed_mean([0, 10, 20, 100]) == 32.5
    assert trimmed_mean([7]) == 7


def test_trimmed_mean_drops_exactly_one_max_and_one_min_at_five_or_more():
    assert trimmed_mean([0, 10, 20, 30, 100]) == 20
    assert trimmed_mean([10, 10, 20, 30, 30]) == 20           # 동점이어도 하나씩만
    assert trimmed_mean([0, 10, 10, 10, 10, 1000]) == 10      # 6명


def test_trimmed_mean_empty_is_zero():
    assert trimmed_mean([]) == 0.0


# ---------- effective_label ----------
def test_effective_label_rules():
    assert effective_label(v("P", VerdictLabel.MET, REAL), DRAFT) == VerdictLabel.MET
    assert effective_label(v("P", VerdictLabel.MET, FAKE), DRAFT) is None         # 가짜 인용 충족 → 강등
    assert effective_label(v("P", VerdictLabel.MET, ""), DRAFT) is None           # 인용 없는 충족 → 강등
    assert effective_label(v("P", VerdictLabel.WEAK, FAKE), DRAFT) == VerdictLabel.MISSING
    assert effective_label(v("P", VerdictLabel.WEAK, REAL), DRAFT) == VerdictLabel.WEAK
    assert effective_label(v("P", VerdictLabel.MISSING, ""), DRAFT) == VerdictLabel.MISSING


# ---------- 경계값 ----------
def test_gap_ratio_exactly_80_percent_is_consensus_gap():
    vs = [v(f"P{i}", VerdictLabel.MISSING) for i in range(4)] + [v("P4", VerdictLabel.MET, REAL)]
    f = aggregate_item("C1-1", vs, DRAFT)
    assert f.gap_ratio == 0.8 and f.kind == FindingKind.CONSENSUS_GAP


def test_gap_ratio_exactly_20_percent_is_met():
    vs = [v("P0", VerdictLabel.MISSING)] + [v(f"P{i}", VerdictLabel.MET, REAL) for i in range(1, 5)]
    f = aggregate_item("C1-1", vs, DRAFT)
    assert f.gap_ratio == 0.2 and f.kind == FindingKind.MET


def test_gap_ratio_between_20_and_80_is_contested():
    vs = [v("P0", VerdictLabel.MISSING), v("P1", VerdictLabel.WEAK, REAL)] + [v(f"P{i}", VerdictLabel.MET, REAL) for i in range(2, 5)]
    f = aggregate_item("C1-1", vs, DRAFT)
    assert f.gap_ratio == 0.4 and f.kind == FindingKind.CONTESTED


def test_exactly_half_valid_is_still_judged():
    vs = [v("P0", VerdictLabel.MET, FAKE), v("P1", VerdictLabel.MET, FAKE),
          v("P2", VerdictLabel.MISSING), v("P3", VerdictLabel.MISSING)]
    f = aggregate_item("C1-1", vs, DRAFT)
    assert f.valid == 2 and f.demoted == 2 and f.kind == FindingKind.CONSENSUS_GAP


def test_fewer_than_half_valid_is_unverifiable():
    vs = [v("P0", VerdictLabel.MET, FAKE), v("P1", VerdictLabel.MET, FAKE), v("P2", VerdictLabel.MISSING)]
    f = aggregate_item("C1-1", vs, DRAFT)
    assert f.kind == FindingKind.UNVERIFIABLE and f.valid == 1 and f.demoted == 2


def test_no_verdicts_is_unverifiable():
    assert aggregate_item("C1-1", [], DRAFT).kind == FindingKind.UNVERIFIABLE


# ---------- 대조표: 6명이면 최고·최저 제외 ----------
def test_fit_table_trims_outlier_reviewers_with_six_personas():
    crit = [Criterion("C1", "실현가능성", 20, "d", Evidence("rfp", 3, "q"))]
    items = [CheckItem("C1-1", "C1", "q")]
    ps = [ReviewerPersona(f"P{i}", f"n{i}", "l") for i in range(6)]
    labels = [VerdictLabel.MET, VerdictLabel.WEAK, VerdictLabel.WEAK, VerdictLabel.WEAK, VerdictLabel.WEAK, VerdictLabel.MISSING]
    vs = [Verdict(f"P{i}", "C1-1", lab, REAL if lab != VerdictLabel.MISSING else "", "r") for i, lab in enumerate(labels)]
    row = build_fit_table(crit, items, ps, vs, DRAFT).rows[0]
    assert row.per_reviewer["P0"] == 20 and row.per_reviewer["P5"] == 0
    assert row.expected_points == 10          # 20·0 제외, 10×4 평균
    assert row.spread == 20
