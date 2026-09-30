"""링크 수집 흐름 — httpx 전송층을 가짜로 바꿔 네트워크 없이 공지 페이지 → 첨부 선택 → 내려받기 → 매직바이트 검사를 확인한다."""
from pathlib import Path

import httpx
import pytest

from rfp_to_fit.adapters import fetch
from rfp_to_fit.adapters.fetch import Fetched, fetch_url, load_fetched

ROOT = Path(__file__).resolve().parents[1]
NAIS_PDF = ROOT / "data" / "rfp" / "nais-hackathon-2026.pdf"

NOTICE = """<html><head><title>2026 공모 안내</title></head><body>
<a href="/f/1.pdf">붙임1. 2026 지원 공고문 (1).pdf</a>
<a href="/f/1.hwpx">붙임1. 2026 지원 공고문 (1).hwpx</a>
<a href="/f/2.pdf">붙임1. 2026 지원 공고문 (2).pdf</a>
<a href="/f/3.pdf">붙임1. 2026 지원 공고문 (3).pdf</a>
<a href="/f/form.hwp">붙임2. 신청서 양식.hwp</a>
</body></html>"""


@pytest.fixture
def served(monkeypatch):
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(str(req.url))
        path = req.url.path
        if path == "/notice":
            return httpx.Response(200, text=NOTICE, headers={"content-type": "text/html; charset=utf-8"})
        if path == "/plain":
            return httpx.Response(200, text="<html><title>공지</title><p>첨부 없음</p></html>",
                                  headers={"content-type": "text/html; charset=utf-8"})
        if path == "/direct.pdf":
            return httpx.Response(200, content=b"%PDF-1.7 direct", headers={"content-type": "application/pdf"})
        if path in ("/f/1.pdf", "/f/2.pdf"):
            return httpx.Response(200, content=b"%PDF-1.7 " + path.encode(), headers={"content-type": "application/pdf"})
        if path == "/f/3.pdf":   # 서버가 파일 대신 오류 페이지를 줌 → 매직바이트 검사에서 버림
            return httpx.Response(200, text="<html>세션 만료</html>", headers={"content-type": "text/html"})
        return httpx.Response(404)

    real = httpx.Client
    monkeypatch.setattr(fetch.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    return calls


def test_notice_page_picks_announcement_parts_and_skips_duplicates_and_forms(served):
    f = fetch_url("https://ex.go.kr/notice")
    assert f.page_title == "2026 공모 안내"
    assert len(f.attachments) == 5
    assert f.chosen.name == "붙임1. 2026 지원 공고문 (1).pdf"
    assert [n for n, _ in f.parts] == ["붙임1. 2026 지원 공고문 (1).pdf", "붙임1. 2026 지원 공고문 (2).pdf"]
    assert not any(u.endswith(("/f/1.hwpx", "/f/form.hwp")) for u in served)   # 같은 공고문의 HWPX·서식은 받지 않음
    assert f.data.startswith(b"%PDF-")


def test_direct_file_link_is_returned_as_is(served):
    f = fetch_url("https://ex.go.kr/direct.pdf")
    assert f.filename == "direct.pdf" and f.data == b"%PDF-1.7 direct" and f.parts == []


def test_page_without_attachments_falls_back_to_page_text(served):
    f = fetch_url("https://ex.go.kr/plain")
    assert f.filename == "page.html" and f.chosen is None


def test_load_fetched_merges_parts_into_one_document_with_page_spans():
    pdf = NAIS_PDF.read_bytes()
    f = Fetched("u", "a.pdf", pdf, parts=[("a.pdf", pdf), ("b.pdf", pdf)])
    doc, spans = load_fetched(f, "url")
    assert len(doc.pages) == 10
    assert spans == [("a.pdf", 1, 5), ("b.pdf", 6, 10)]
    assert doc.pages[5] == doc.pages[0]


def test_load_fetched_single_file():
    doc, spans = load_fetched(Fetched("u", "notice.txt", "한 줄\n두 줄".encode()), "url")
    assert doc.pages == ["한 줄\n두 줄"] and spans == [("notice.txt", 1, 1)]
