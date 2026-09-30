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


def test_graph_with_cross_examination_step():
    class Ex:
        name = "ex"

        def complete_json(self, s, p):
            return {"results": [{"item_id": "C1-1", "supports": False, "why": "무관", "reason": "다른 내용"}]}

    ex = Extraction([], [Criterion("C1", "실현가능성", 25, "d", Evidence("rfp", 1, "q"))])
    ps = [ReviewerPersona(f"P{i}", f"n{i}", "l") for i in range(3)]
    llm = Fake()
    run = run_graph(ex, DRAFT, ps, llm, lambda p: llm, items=[CheckItem("C1-1", "C1", "정확도 목표가 있는가")],
                    examiner_for=lambda p: Ex())
    steps = [t["step"] for t in run.trace]
    assert steps == ["점검 항목", "독립 채점", "재질의", "교차 신문", "집계", "보완 지정"]
    assert run.trace[3]["rejected"] == 3


def test_graph_prior_art_step_feeds_reviewers_and_is_recorded():
    class Search:
        name = "fake-mcp"

        def search(self, q, n=5):
            return [{"title": "LLM grant review", "year": 2025, "doi": "https://doi.org/10.1/x"}]

    class L(Fake):
        def __init__(self):
            super().__init__()
            self.review_prompts = []

        def complete_json(self, system, prompt):
            if "검색어" in prompt:
                return {"queries": ["llm grant review"]}
            if "번호만 골라라" in prompt:
                return {"keep": [0]}
            if "평가지표와 점검 질문" in prompt:
                self.review_prompts.append(prompt)
                return {"verdicts": [{"item_id": "C1-1", "label": "충족", "quote": "요건 추출 재현율 90% 이상", "reason": "ok"}]}
            return super().complete_json(system, prompt)

    ex = Extraction([], [Criterion("C1", "실현가능성", 25, "d", Evidence("rfp", 1, "q"))])
    ps = [ReviewerPersona(f"P{i}", f"n{i}", "l") for i in range(2)]
    llm = L()
    run = run_graph(ex, DRAFT, ps, llm, lambda p: llm, items=[CheckItem("C1-1", "C1", "정확도 목표가 있는가")],
                    prior_search=Search())
    assert [t["step"] for t in run.trace] == ["점검 항목", "선행 탐색", "독립 채점", "집계", "보완 지정"]
    assert run.prior_art[0]["title"] == "LLM grant review"
    assert all("LLM grant review" in p for p in llm.review_prompts)
