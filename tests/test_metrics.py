from rfp_to_fit.domain.metrics import coverage, criteria_agreement, match_requirements, recall


def test_coverage_is_spacing_insensitive():
    assert coverage("참가신청서 제출", "참가 신청서를 제출해야 한다") > 0.8


def test_match_requires_nearby_page():
    gold = [{"text": "자필 서명 스캔 후 첨부", "page": 4}]
    far = [{"text": "자필 서명 스캔 후 첨부", "page": 9}]
    near = [{"text": "신청자 자필 서명을 스캔 후 첨부", "page": 5}]
    assert recall(match_requirements(gold, far)) == 0
    assert recall(match_requirements(gold, near)) == 1


def test_criteria_agreement_uses_name_and_points():
    gold = [{"name": "혁신성", "points": 25}, {"name": "적합성", "points": 10}]
    ex = [{"name": "혁신성", "points": 25.0}, {"name": "적합성", "points": 20}]
    assert criteria_agreement(gold, ex) == 0.5


def test_short_summary_candidate_counts_but_tiny_fragment_does_not():
    from rfp_to_fit.domain.metrics import match_score
    gold = "국가연구개발사업 참여제한 중인 자는 신청할 수 없음(연구개발계획서 제출마감일 전일에 참여제한이 종료되는 경우 신청 가능)"
    assert match_score(gold, "국가연구개발사업 참여제한 중인 자는 신청할 수 없음") >= 0.5
    assert match_score(gold, "신청 가능") < 0.5
