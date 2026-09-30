from rfp_to_fit.application.review import cross_examine
from rfp_to_fit.domain.model import CheckItem, ReviewerPersona, Verdict, VerdictLabel


class Examiner:
    name = "x"

    def __init__(self):
        self.prompts = []

    def complete_json(self, s, p):
        self.prompts.append(p)
        return {"results": [{"item_id": "C1-1", "supports": False, "why": "부정", "reason": "없다고 함"},
                            {"item_id": "C1-2", "supports": False, "why": "", "reason": "사유 코드 없음 → 기각 안 함"}]}


def test_cross_examination_downgrades_rejected_met_only():
    items = [CheckItem("C1-1", "C1", "데이터 확보 계획이 있는가"), CheckItem("C1-2", "C1", "일정이 있는가")]
    ps = [ReviewerPersona("P1", "a", "l")]
    vs = [Verdict("P1", "C1-1", VerdictLabel.MET, "데이터 확보 계획은 아직 없다", "x"),
          Verdict("P1", "C1-2", VerdictLabel.MET, "1일차 17:00~24:00 파서 구현", "y"),
          Verdict("P1", "C1-2", VerdictLabel.MISSING, "", "z")]
    ex = Examiner()
    out, stat = cross_examine(ps, items, vs, lambda p: ex, lambda v: v.label == VerdictLabel.MET)
    assert len(ex.prompts) == 1 and "데이터 확보 계획은 아직 없다" in ex.prompts[0]
    assert out[0].label == VerdictLabel.WEAK and out[0].reason.startswith("[교차 신문")
    assert out[1].label == VerdictLabel.MET and out[2] is vs[2]
    assert stat == {"examined": 2, "rejected": 1}
