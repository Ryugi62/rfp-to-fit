from rfp_to_fit.adapters.graph import run_graph
from rfp_to_fit.application.extract import Extraction
from rfp_to_fit.domain.model import CheckItem, Criterion, Evidence, FindingKind, ReviewerPersona

DRAFT = "## 3) 구현방안\n정확도 목표: 요건 추출 재현율 90% 이상."


class Fake:
    name = "fake"

    def __init__(self):
        self.calls = 0

    def complete_json(self, system, prompt):
        self.calls += 1
        if "다시 판정" in prompt:
            return {"verdicts": [{"item_id": "C1-1", "label": "충족", "quote": "요건 추출 재현율 90% 이상", "reason": "ok"}]}
        if "보완 지정" in prompt:
            return {"remedies": []}
        return {"verdicts": [{"item_id": "C1-1", "label": "충족", "quote": "재현율 99% 달성", "reason": "x"}]}   # 첫 판정은 가짜 인용


def test_graph_runs_recheck_loop_then_aggregates():
    ex = Extraction([], [Criterion("C1", "실현가능성", 25, "d", Evidence("rfp", 1, "q"))])
    ps = [ReviewerPersona(f"P{i}", f"n{i}", "l") for i in range(3)]
    llm = Fake()
    run = run_graph(ex, DRAFT, ps, llm, lambda p: llm, items=[CheckItem("C1-1", "C1", "정확도 목표가 있는가")])
    steps = [t["step"] for t in run.trace]
    assert steps == ["점검 항목", "독립 채점", "재질의", "집계", "보완 지정"]
    assert run.table.rows[0].findings[0].kind == FindingKind.MET
    assert run.trace[2]["fixed"] == 3
