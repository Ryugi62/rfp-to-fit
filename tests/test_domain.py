from rfp_to_fit.domain.model import (
    CheckItem, Criterion, Evidence, FindingKind, ReviewerPersona, Verdict, VerdictLabel,
)
from rfp_to_fit.domain.quotes import normalize, verify_quote
from rfp_to_fit.domain.aggregate import aggregate_item, build_fit_table

DRAFT = "우리는 공개 RFP 3건으로 요건 추출 재현율 90% 이상을 측정한다.\n역할: 대표는 파서, 팀원은 화면."


def _v(rid, label, quote=""):
    return Verdict(reviewer_id=rid, item_id="C1-1", label=label, quote=quote, reason="r")


def test_verify_quote_ignores_whitespace_and_punctuation():
    assert verify_quote("요건 추출  재현율 90% 이상을", DRAFT)
    assert verify_quote("역할: 대표는 파서", DRAFT)


def test_verify_quote_rejects_invented_text():
    assert not verify_quote("정밀도 80% 이상을 달성했다", DRAFT)
    assert not verify_quote("", DRAFT)


def test_normalize_strips_markdown_and_spaces():
    assert normalize("**요건**  추출\n재현율") == "요건추출재현율"


def test_consensus_gap_when_all_reviewers_flag():
    verdicts = [_v(f"P{i}", VerdictLabel.MISSING) for i in range(5)]
    f = aggregate_item("C1-1", verdicts, DRAFT)
    assert f.kind == FindingKind.CONSENSUS_GAP
    assert f.gap_ratio == 1.0


def test_contested_when_reviewers_split():
    verdicts = [_v("P0", VerdictLabel.MISSING), _v("P1", VerdictLabel.WEAK),
                _v("P2", VerdictLabel.MET, "요건 추출 재현율 90%"), _v("P3", VerdictLabel.MET, "재현율 90% 이상"),
                _v("P4", VerdictLabel.MET, "공개 RFP 3건")]
    f = aggregate_item("C1-1", verdicts, DRAFT)
    assert f.kind == FindingKind.CONTESTED


def test_met_when_majority_met_with_real_quotes():
    verdicts = [_v(f"P{i}", VerdictLabel.MET, "요건 추출 재현율 90%") for i in range(5)]
    f = aggregate_item("C1-1", verdicts, DRAFT)
    assert f.kind == FindingKind.MET


def test_hallucinated_met_quote_is_demoted():
    # 5명 중 3명이 없는 문장을 인용하며 충족이라 함 → 유효 2(부족) → 합의 결핍
    verdicts = [_v("P0", VerdictLabel.MET, "정밀도 80%를 이미 달성"),
                _v("P1", VerdictLabel.MET, "특허 3건 출원 완료"),
                _v("P2", VerdictLabel.MET, "예산 5억 원"),
                _v("P3", VerdictLabel.MISSING), _v("P4", VerdictLabel.MISSING)]
    f = aggregate_item("C1-1", verdicts, DRAFT)
    assert f.demoted == 3
    assert f.kind == FindingKind.UNVERIFIABLE  # 유효 판정 2/5 < 절반


def test_fit_table_expected_score_scales_by_points():
    crit = [Criterion(id="C1", name="실현가능성", points=25, description="d", evidence=Evidence("rfp", 1, "q"))]
    items = [CheckItem(id="C1-1", criterion_id="C1", question="q1"), CheckItem(id="C1-2", criterion_id="C1", question="q2")]
    personas = [ReviewerPersona(id=f"P{i}", name=f"n{i}", lens="l") for i in range(2)]
    verdicts = [
        Verdict("P0", "C1-1", VerdictLabel.MET, "요건 추출 재현율 90%", "r"),
        Verdict("P0", "C1-2", VerdictLabel.MISSING, "", "r"),
        Verdict("P1", "C1-1", VerdictLabel.MET, "요건 추출 재현율 90%", "r"),
        Verdict("P1", "C1-2", VerdictLabel.WEAK, "역할: 대표는 파서", "r"),
    ]
    table = build_fit_table(crit, items, personas, verdicts, DRAFT)
    row = table.rows[0]
    # MET=1, WEAK=0.5, MISSING=0 → P0 = (1+0)/2, P1 = (1+0.5)/2 → 평균 0.625 × 25
    assert abs(row.expected_points - 15.625) < 1e-6
    assert row.per_reviewer["P0"] == 12.5
    assert table.total_points == 25


def test_loose_quote_accepts_table_cells_split_across_lines():
    from rfp_to_fit.domain.quotes import verify_quote_loose
    page = "§ 문제 정의의 명확성 및 대회 § 문제 해결 성과\n적합성 20 10\n취지와의 부합성"
    assert verify_quote_loose("적합성 20 § 문제 정의의 명확성 및 대회 취지와의 부합성", page)
    assert not verify_quote_loose("적합성 30 연구비 집행의 투명성", page)


def test_rubric_accepts_both_json_shapes():
    from rfp_to_fit.application.review import _flatten_items
    a = {"items": [{"criterion_id": "C1", "question": "q1"}]}
    b = {"items": [{"criterion_id": "C1", "questions": ["q1", "q2"]}]}
    assert _flatten_items(a) == [("C1", "q1")]
    assert _flatten_items(b) == [("C1", "q1"), ("C1", "q2")]


def test_rows_of_accepts_bare_list_and_skips_junk():
    from rfp_to_fit.application.review import rows_of
    assert rows_of([{"item_id": "a"}, "x"], "remedies") == [{"item_id": "a"}]
    assert rows_of({"remedies": [{"item_id": "b"}]}, "remedies") == [{"item_id": "b"}]
    assert rows_of(None, "remedies") == []


def test_trimmed_mean_drops_max_and_min_from_five_or_more():
    from rfp_to_fit.domain.aggregate import trimmed_mean
    assert trimmed_mean([10, 20, 20, 20, 100]) == 20
    assert trimmed_mean([10, 20]) == 15
    assert trimmed_mean([]) == 0.0
