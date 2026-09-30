from rfp_to_fit.application.review import recheck
from rfp_to_fit.domain.aggregate import effective_label
from rfp_to_fit.domain.model import CheckItem, Criterion, Evidence, ReviewerPersona, Verdict, VerdictLabel

DRAFT = "정확도 목표: 요건 추출 재현율 90% 이상, 결핍 탐지 정밀도 80% 이상."


class FakeLLM:
    name = "fake"

    def __init__(self):
        self.prompts = []

    def complete_json(self, system, prompt):
        self.prompts.append(prompt)
        return {"verdicts": [{"item_id": "C1-1", "label": "충족", "quote": "요건 추출 재현율 90% 이상", "reason": "ok"}]}


def test_recheck_only_asks_invalid_and_replaces_them():
    crit = [Criterion("C1", "실현가능성", 25, "d", Evidence("rfp", 1, "q"))]
    items = [CheckItem("C1-1", "C1", "정확도 목표가 있는가")]
    ps = [ReviewerPersona("P1", "a", "l"), ReviewerPersona("P2", "b", "l")]
    vs = [Verdict("P1", "C1-1", VerdictLabel.MET, "재현율 95%를 달성", "x"),      # 가짜 인용
          Verdict("P2", "C1-1", VerdictLabel.MET, "결핍 탐지 정밀도 80%", "y")]   # 진짜 인용
    llm = FakeLLM()
    out = recheck(ps, crit, items, vs, DRAFT, lambda p: llm, lambda v: effective_label(v, DRAFT) is None)
    assert len(llm.prompts) == 1                       # P1만 다시 물음
    assert "결핍 탐지 정밀도" in llm.prompts[0]          # 초안은 주되
    assert "P2" not in llm.prompts[0]                  # 다른 평가위원 답은 안 보여줌
    assert out[0].quote == "요건 추출 재현율 90% 이상" and out[0].reason.startswith("[재질의]")
    assert out[1] is vs[1]
