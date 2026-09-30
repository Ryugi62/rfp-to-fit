"""정확도 측정 — 정답표 대비 요건 재현율·지표 일치(결정론, LLM 미사용)."""
from __future__ import annotations

from .quotes import normalize


def bigrams(s: str) -> set[str]:
    n = normalize(s)
    return {n[i:i + 2] for i in range(len(n) - 1)}


def coverage(gold_text: str, cand_text: str) -> float:
    g = bigrams(gold_text)
    return len(g & bigrams(cand_text)) / len(g) if g else 0.0


def match_score(gold_text: str, cand_text: str, cand_quote: str = "", min_len: int = 12) -> float:
    """정답 요건을 후보가 덮는 정도. 후보가 정답을 짧게 요약한 경우(역방향)도 인정하되, 후보가 12자 미만이면 역방향 불인정."""
    fwd = coverage(gold_text, f"{cand_text} {cand_quote}")
    rev = coverage(cand_text, gold_text) if len(normalize(cand_text)) >= min_len else 0.0
    return max(fwd, rev)


def match_requirements(gold: list[dict], extracted: list[dict], threshold: float = 0.5, page_slack: int = 1):
    """gold 요건마다 같은 쪽(±1) 추출 요건 중 가장 많이 덮는 것을 찾는다. 반환: [(gold, best_cand|None, score)]"""
    out = []
    for g in gold:
        best, best_s = None, 0.0
        for c in extracted:
            gp, cp = g.get("page"), c.get("page")
            if gp and cp and abs(int(gp) - int(cp)) > page_slack:
                continue
            s = match_score(g["text"], c.get("text", ""), c.get("quote", ""))
            if s > best_s:
                best, best_s = c, s
        out.append((g, best if best_s >= threshold else None, best_s))
    return out


def recall(matches) -> float:
    return sum(1 for _, c, _ in matches if c is not None) / len(matches) if matches else 0.0


def criteria_agreement(gold: list[dict], extracted: list[dict]) -> float:
    """정답 지표(이름·배점·단계)가 추출 결과에 있는 비율."""
    def key(d):
        return (normalize(d["name"]), float(d["points"]))
    ex = {key(e) for e in extracted}
    return sum(1 for g in gold if key(g) in ex) / len(gold) if gold else 0.0
