import json

from rfp_to_fit.application.extract import Extraction
from rfp_to_fit.application.pipeline import ReviewRun
from rfp_to_fit.application.serialize import extraction_from_dict, extraction_to_dict, run_from_dict, run_to_dict
from rfp_to_fit.domain.aggregate import build_fit_table
from rfp_to_fit.domain.model import (
    CheckItem, Criterion, Evidence, RemedyItem, Requirement, ReviewerPersona, ReviewerStance, Verdict, VerdictLabel,
)

DRAFT = ("## 3) 구현방안\n정확도 목표: 요건 추출 재현율 90% 이상.\n"
         "비밀 문단: 이 문장은 초안에만 있고 저장 파일에는 남으면 안 되는 긴 원문이다. " * 3)


def _json(d):
    return json.loads(json.dumps(d, ensure_ascii=False))


def _extraction():
    reqs = [Requirement("R1", "자격", "국내 대학 소속", Evidence("rfp", 1, "국내 대학 소속 연구자"), "탈락"),
            Requirement("R2", "기타", "안내", Evidence("rfp", 2, "문의처 안내"))]
    crits = [Criterion("C1", "혁신성", 25.0, "창의성", Evidence("rfp", 3, "혁신성 25"), "본선"),
             Criterion("C2", "실현가능성", 25.0, "완성도", Evidence("rfp", 3, "실현가능성 25"))]
    return Extraction(reqs, crits, [{"kind": "requirement", "text": "환각", "page": 9, "quote": "없음"}])


def _run():
    ex = _extraction()
    items = [CheckItem("C1-1", "C1", "비교 대상이 있는가"), CheckItem("C2-1", "C2", "정확도 목표가 있는가")]
    ps = [ReviewerPersona("P1", "기술 타당성 검증형", "lens1", "OpenAI x"), ReviewerPersona("P2", "사업 취지형", "lens2", "Upstage y")]
    vs = [Verdict("P1", "C1-1", VerdictLabel.MISSING, "", "없음"),
          Verdict("P2", "C1-1", VerdictLabel.WEAK, "요건 추출 재현율 90% 이상", "약함"),
          Verdict("P1", "C2-1", VerdictLabel.MET, "요건 추출 재현율 90% 이상", "있음"),
          Verdict("P2", "C2-1", VerdictLabel.MET, "요건 추출 재현율 90% 이상", "있음")]
    table = build_fit_table(ex.criteria, items, ps, vs, DRAFT)
    return ReviewRun(ex.requirements, ex.criteria, items, ps, vs, table,
                     [RemedyItem("C1-1", "선행연구", "3) 구현방안", "혁신성 원문")],
                     [{"step": "집계", "t": 1.0}], [{"title": "A", "doi": "https://doi.org/10.1/a"}],
                     [ReviewerStance("P1", "보류", "비교 대상 없음")], ["P9"])


def test_extraction_roundtrip_through_json_is_equal():
    ex = _extraction()
    assert extraction_from_dict(_json(extraction_to_dict(ex))) == ex


def test_extraction_from_dict_defaults_for_old_records():
    d = _json(extraction_to_dict(_extraction()))
    for r in d["requirements"]:
        r.pop("consequence")
    for c in d["criteria"]:
        c.pop("stage")
    d.pop("dropped")
    back = extraction_from_dict(d)
    assert back.requirements[0].consequence == "" and back.criteria[0].stage == "단일" and back.dropped == []


def test_run_roundtrip_through_json_is_equal():
    run = _run()
    back = run_from_dict(_json(run_to_dict(run)))
    assert back == run
    assert back.table.expected_total == run.table.expected_total


def test_saved_run_does_not_contain_draft_text_and_caps_quotes():
    long_quote = "이 문장은 초안에만 있고 저장 파일에는 남으면 안 되는 긴 원문이다. " * 2
    assert len(long_quote) > 60
    run = _run()
    run.verdicts.append(Verdict("P1", "C1-1", VerdictLabel.WEAK, long_quote, "r"))
    dumped = json.dumps(run_to_dict(run), ensure_ascii=False)
    assert all(len(v["quote"]) <= 60 for v in run_to_dict(run)["verdicts"])
    assert long_quote not in dumped
    assert DRAFT not in dumped and "비밀 문단" not in dumped
