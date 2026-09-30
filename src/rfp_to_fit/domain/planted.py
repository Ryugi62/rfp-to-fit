"""결함 주입 실험 판정(결정론): 원본 대비 점검 항목별 감점 비율이 크게 오른 곳 = 새 결핍."""
from __future__ import annotations

RISE = 0.4   # 5명 중 2명 이상이 새로 깎으면 「새 결핍」


def new_gaps(base: dict[str, float], variant: dict[str, float], rise: float = RISE) -> set[str]:
    return {k for k, v in variant.items() if v - base.get(k, 0.0) >= rise - 1e-9}


def score_variant(base: dict[str, float], variant: dict[str, float], item_crit: dict[str, str], expected: set[str]):
    """반환 (탐지 여부, 새 결핍 수, 그중 기대 지표 수)."""
    ng = new_gaps(base, variant)
    hit = {k for k in ng if item_crit.get(k) in expected}
    return bool(hit), len(ng), len(hit)
