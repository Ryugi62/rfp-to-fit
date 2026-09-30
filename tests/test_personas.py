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


def test_lenses_are_domain_neutral():
    # 관점은 어느 분야 공고에도 쓰인다 — 특정 기술 분야(예: AI·LLM)를 박아 두면 우주·제조 공고에서도 AI 전문가처럼 묻는다
    for p in DEFAULT_PERSONAS:
        for word in ("AI", "LLM", "인공지능"):
            assert word not in p.lens, (p.name, word)
