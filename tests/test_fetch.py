from rfp_to_fit.adapters.documents import sniff
from rfp_to_fit.adapters.fetch import find_attachments, score_name

PAGE = """<a href="./down.do?no=1">[붙임1] 참가자 가이드라인.hwp</a>
<a href="./down.do?no=2">[붙임2] 참가자 제출서류.hwp</a>
<a href="./down.do?no=3">2026 ○○ 신규과제 지원 공고.hwp</a>
<a href="/attach/down/abc">붙임1. 2026년도 사업 공고문 (1).pdf [594.6 KB]</a>
<a href="./poster.png">포스터.png</a>"""


def test_picks_announcement_over_forms():
    atts = find_attachments(PAGE, "https://ex.go.kr/bbs/view.do")
    assert atts[0].name == "붙임1. 2026년도 사업 공고문 (1).pdf"
    assert atts[0].url == "https://ex.go.kr/attach/down/abc"
    assert [a.name for a in atts][1] == "2026 ○○ 신규과제 지원 공고.hwp"
    assert all("포스터" not in a.name for a in atts)
    assert score_name("[붙임2] 참가자 제출서류.hwp") < 0


def test_sniff_uses_magic_bytes_not_extension():
    assert sniff(b"PK\x03\x04rest", "공고.hwp") == "hwpx"
    assert sniff(b"%PDF-1.7", "x.hwp") == "pdf"
    assert sniff(bytes.fromhex("D0CF11E0A1B11AE1") + b"x", "a.hwp") == "hwp5"


def test_script_download_links_become_post_urls():
    page = """<a href="javascript:void(0);" onclick="getExtension_path('55025', '7');">[공고문] 2026 지정 신청 공고.hwpx</a>"""
    atts = find_attachments(page, "https://www.msit.go.kr/bbs/view.do?x=1")
    assert atts[0].url == "POST https://www.msit.go.kr/ssm/file/fileDown.do?atchFileNo=55025&fileOrd=7&fileBtn=A"
