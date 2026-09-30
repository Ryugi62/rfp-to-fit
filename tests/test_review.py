"""③ 독립 채점 · 전체 인상(stance) · ⑤ 보완 지정 — 가짜 LLM, 네트워크 없음."""
import threading

from rfp_to_fit.application.review import remedy, review_all, sections_of
from rfp_to_fit.domain.model import (
    CheckItem, Criterion, Evidence, Finding, FindingKind, ReviewerPersona, ReviewerStance, VerdictLabel,
)

DRAFT = "## 1) 문제 정의\n공고 요건 누락이 잦다.\n## 3) 구현방안\n요건 추출 재현율 90% 이상."
CRIT = [Criterion("C1", "실현가능성", 25, "완성도", Evidence("rfp", 3, "q"))]
ITEMS = [CheckItem("C1-1", "C1", "정확도 목표가 있는가"), CheckItem("C1-2", "C1", "일정이 있는가")]
PS = [ReviewerPersona(f"P{i}", f"관점{i}", f"렌즈-{i}") for i in range(1, 4)]


class Reviewer:
    name = "fake"

    def __init__(self, decision="보류", fail_times=0):
        self.decision, self.fail_times = decision, fail_times
        self.calls = []
        self.lock = threading.Lock()

    def complete_json(self, system, prompt):
        with self.lock:
            self.calls.append((system, prompt))
            if self.fail_times:
                self.fail_times -= 1
                raise RuntimeError("429")
        return {"verdicts": [{"item_id": "C1-1", "label": "충족", "quote": "요건 추출 재현율 90% 이상", "reason": "a"},
                             {"item_id": "C1-2", "label": "이상한값", "quote": "", "reason": "b"},
                             {"item_id": "C9-9", "label": "충족", "quote": "x", "reason": "없는 항목"}],
                "stance": {"decision": self.decision, "key_point": "일정이 없다"}}


def test_each_reviewer_called_separately_with_same_input_except_lens():
    llms = {p.id: Reviewer() for p in PS}
    vs, stances, failed = review_all(PS, CRIT, ITEMS, DRAFT, lambda p: llms[p.id], with_stance=True)
    assert all(len(l.calls) == 1 for l in llms.values())
    prompts = {l.calls[0][1] for l in llms.values()}
    assert len(prompts) == 1                                   # 모두 같은 입력 = 서로의 답을 보지 않음
    for p in PS:
        assert p.lens in llms[p.id].calls[0][0]
    assert len(vs) == 6 and failed == []
    assert {v.item_id for v in vs} == {"C1-1", "C1-2"}          # 없는 항목 판정은 버림
    assert all(v.label == VerdictLabel.MISSING for v in vs if v.item_id == "C1-2")   # 모르는 라벨 = 누락


def test_stance_is_parsed_per_reviewer_and_invalid_decision_is_ignored():
    llms = {"P1": Reviewer("선정"), "P2": Reviewer("탈락"), "P3": Reviewer("모름")}
    _, stances, _ = review_all(PS, CRIT, ITEMS, DRAFT, lambda p: llms[p.id], with_stance=True)
    assert sorted(stances, key=lambda s: s.reviewer_id) == [ReviewerStance("P1", "선정", "일정이 없다"),
                                                             ReviewerStance("P2", "탈락", "일정이 없다")]


def test_failed_reviewer_is_retried_once_then_reported():
    llms = {"P1": Reviewer(fail_times=1), "P2": Reviewer(fail_times=5), "P3": Reviewer()}
    vs, _, failed = review_all(PS, CRIT, ITEMS, DRAFT, lambda p: llms[p.id], with_stance=True)
    assert failed == ["P2"]
    assert {v.reviewer_id for v in vs} == {"P1", "P3"}
    assert len(llms["P1"].calls) == 2 and len(llms["P2"].calls) == 2


def test_prior_art_context_is_passed_as_reference():
    llm = Reviewer()
    review_all(PS[:1], CRIT, ITEMS, DRAFT, lambda p: llm, context="- Paper A (2024)")
    assert "[참고 자료 — 인용 금지]" in llm.calls[0][1] and "Paper A" in llm.calls[0][1]


class RemedyLLM:
    name = "fake"

    def __init__(self):
        self.prompts = []

    def complete_json(self, s, p):
        self.prompts.append(p)
        return {"remedies": [{"item_id": "C1-2", "evidence_type": "일정", "location": "3) 구현방안", "why": "지표 원문"},
                             {"item_id": "C1-1", "evidence_type": "수치", "location": "x", "why": "충족 항목 — 버려야 함"}]}


def test_remedy_only_for_gaps_and_contested_and_has_no_sentence_field():
    fs = [Finding("C1-1", FindingKind.MET, 0.0, 3, 0), Finding("C1-2", FindingKind.CONSENSUS_GAP, 1.0, 3, 0)]
    llm = RemedyLLM()
    out = remedy(fs, ITEMS, CRIT, DRAFT, llm)
    assert [(r.item_id, r.evidence_type, r.location) for r in out] == [("C1-2", "일정", "3) 구현방안")]
    assert "- 1) 문제 정의" in llm.prompts[0] and "- 3) 구현방안" in llm.prompts[0]
    assert set(out[0].__dataclass_fields__) == {"item_id", "evidence_type", "location", "why"}


def test_remedy_skips_llm_when_nothing_to_fix():
    llm = RemedyLLM()
    assert remedy([Finding("C1-1", FindingKind.MET, 0.0, 3, 0)], ITEMS, CRIT, DRAFT, llm) == []
    assert llm.prompts == []


def test_sections_of_reads_markdown_and_numbered_headings():
    assert sections_of(DRAFT) == ["1) 문제 정의", "3) 구현방안"]
    assert sections_of("제목 없는 본문") == ["본문"]
