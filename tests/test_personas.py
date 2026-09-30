from rfp_to_fit.application.personas import DEFAULT_PERSONAS
from rfp_to_fit.domain.model import ReviewerPersona


def test_six_distinct_reviewer_types():
    assert len(DEFAULT_PERSONAS) == 6
    assert all(isinstance(p, ReviewerPersona) for p in DEFAULT_PERSONAS)
    assert len({p.id for p in DEFAULT_PERSONAS}) == 6
    assert len({p.name for p in DEFAULT_PERSONAS}) == 6
    assert len({p.lens for p in DEFAULT_PERSONAS}) == 6


def test_persona_types_match_mentoring_list():
    names = [p.name for p in DEFAULT_PERSONAS]
    assert names == ["기술 타당성 검증형", "기술 큰그림형", "세부 전문형", "사업성·시장형", "행정·관리형", "사업 취지형"]
