"""① 공고 파싱 — 가짜 LLM으로 쪽·인용 검증, 쪽 교정, 환각 버림, 묶음 간 중복 제거를 확인한다."""
from rfp_to_fit.application import extract as extract_mod
from rfp_to_fit.application.extract import PROMPT, extract_rfp
from rfp_to_fit.application.ports import Document

PAGES = [
    "신청 자격: 공고일 기준 국내 대학 소속 연구자\n※ 증빙서류는 PDF로만 접수",
    "□ 심사기준\n혁신성 30 아이디어의 창의성\n실현가능성 70 구현 계획의 구체성",
    "접수 마감: 2026. 10. 12. 18:00까지 IRIS로 제출",
    "기타 문의처 안내",
]


class FakeExtractor:
    name = "fake"

    def complete_json(self, system, prompt):
        if "[p.1]" in prompt:   # 1~3쪽 묶음
            return {"requirements": [
                {"category": "자격", "consequence": " 탈락 ", "text": "국내 대학 소속 연구자", "page": 1, "quote": "국내 대학 소속 연구자"},
                {"category": "형식", "consequence": "불이익", "text": "증빙은 PDF로만", "page": 1, "quote": "증빙서류는 PDF로만 접수"},
                {"category": "기간", "consequence": "탈락", "text": "마감 10/12 18시", "page": 1, "quote": "2026. 10. 12. 18:00까지"},
                {"category": "제한", "consequence": "탈락", "text": "예산 5억 이하", "page": 2, "quote": "총 예산 5억 원 이하로 제한"},
            ], "criteria": [
                {"name": "혁신성", "points": 30, "description": "창의성", "stage": "단일", "page": 3, "quote": "혁신성 30 아이디어의 창의성"},
                {"name": "실현가능성", "points": "70", "description": "구체성", "stage": "", "page": 2, "quote": "실현가능성 70"},
            ]}
        return {"requirements": [   # 4쪽 묶음: 앞 묶음과 같은 요건을 다시 냄
            {"category": "자격", "consequence": "탈락", "text": "국내 대학 소속 연구자", "page": 4, "quote": "기타 문의처 안내"}],
            "criteria": []}


def test_extract_verifies_quotes_corrects_pages_and_drops_hallucinations():
    ex = extract_rfp(Document("rfp", PAGES), FakeExtractor())
    by_text = {r.text: r for r in ex.requirements}
    assert set(by_text) == {"국내 대학 소속 연구자", "증빙은 PDF로만", "마감 10/12 18시"}
    assert by_text["국내 대학 소속 연구자"].evidence.page == 1
    assert by_text["국내 대학 소속 연구자"].consequence == "탈락"
    assert by_text["마감 10/12 18시"].evidence.page == 3          # 쪽 번호가 틀려도 원문이 있는 쪽으로 교정
    assert [d["text"] for d in ex.dropped] == ["예산 5억 이하"]      # 원문에 없는 인용 = 버림
    assert [r.id for r in ex.requirements] == ["R1", "R2", "R3"]


def test_extract_criteria_page_within_one_and_points_parsed():
    ex = extract_rfp(Document("rfp", PAGES), FakeExtractor())
    c = {x.name: x for x in ex.criteria}
    assert c["혁신성"].evidence.page == 2                        # 3쪽이라 했지만 ±1쪽(2쪽)에서 찾음
    assert c["실현가능성"].points == 70.0 and c["실현가능성"].stage == "단일"
    assert sum(x.points for x in ex.criteria) == 100


def test_extract_records_failed_chunks_instead_of_hiding_them():
    class Broken:
        name = "broken"

        def complete_json(self, s, p):
            raise RuntimeError("429")

    before = len(extract_mod.FAILURES)
    ex = extract_rfp(Document("rfp", PAGES), Broken())
    assert ex.requirements == [] and ex.criteria == []
    assert len(extract_mod.FAILURES) - before == 4               # 2묶음 × 2회 시도


def test_extract_chunks_three_pages_per_call():
    seen = []

    class Spy(FakeExtractor):
        def complete_json(self, system, prompt):
            seen.append(sorted(int(x) for x in __import__("re").findall(r"\[p\.(\d+)\]", prompt.split("공고문:")[-1])))
            return {}

    extract_rfp(Document("rfp", PAGES), Spy())
    assert sorted(seen) == [[1, 2, 3], [4]]


def test_footnote_rule_is_in_extraction_prompt():
    assert "※·* 주석 안의 조건" in PROMPT
    assert "consequence" in PROMPT and "해당없음" in PROMPT


def test_empty_document_yields_empty_extraction():
    ex = extract_rfp(Document("empty", []), None)
    assert ex.requirements == [] and ex.criteria == []
