"""가상 평가위원 — 역할 유형(렌즈)만 정의한다. 실존 심사위원 개인을 모델링하지 않는다(SPEC 비목표)."""
from __future__ import annotations

from ..domain.model import ReviewerPersona

DEFAULT_PERSONAS = [
    ReviewerPersona("P1", "출연연 연구기획 책임자", "문제 정의가 명확한가, 국가 R&D·주최 취지와 맞는가, 기획 논리가 이어지는가를 먼저 본다."),
    ReviewerPersona("P2", "산업체 CTO", "현장에서 실제로 쓰일지, 비용·도입 장벽·사업화 경로가 있는지, 숫자로 된 효과가 있는지를 먼저 본다."),
    ReviewerPersona("P3", "AI 기술 전문가", "기술 구성이 구체적인지, 정확도 목표와 검증 방법이 있는지, 재현 가능하고 기존 기술과 무엇이 다른지를 먼저 본다."),
    ReviewerPersona("P4", "전문기관 과제관리 PM", "요건·일정·역할 분담·성과지표·위험 대응이 관리 가능하게 적혀 있는지를 먼저 본다."),
    ReviewerPersona("P5", "연구윤리·신뢰성 심사자", "개인정보·보안, 환각·오류 대응, 책임 주체(사람의 최종 판단), 출처 표기를 먼저 본다."),
]
