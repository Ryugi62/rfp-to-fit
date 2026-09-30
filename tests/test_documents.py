from rfp_to_fit.adapters.documents import hwpx_text, paginate


def test_hwpx_text_strips_nested_tags_and_linebreaks():
    xml = ('<hp:p id="1"><hp:run><hp:t>2026 NAIS<hp:lineBreak/>AI 해커톤</hp:t></hp:run></hp:p>'
           '<hp:p><hp:run><hp:t charPrIDRef="3">A &amp; B<hp:tab width="1"/>C</hp:t></hp:run></hp:p>')
    assert hwpx_text(xml) == ["2026 NAIS\nAI 해커톤", "A & B C"]


def test_paginate_splits_on_paragraph_boundaries():
    pages = paginate(["a" * 2000, "b" * 2000, "c" * 10], size=3000)
    assert len(pages) == 2 and pages[0] == "a" * 2000


from pathlib import Path  # noqa: E402

from rfp_to_fit.adapters.documents import load_bytes, load_path  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"


def test_pdf_keeps_pages_and_appends_table_rows():
    doc = load_path(DATA / "rfp" / "nais-hackathon-2026.pdf")
    assert len(doc.pages) == 5
    assert "심사기준" in doc.pages[2] and "[표]" in doc.pages[2]


def test_hwpx_is_parsed_into_3000_char_sections():
    doc = load_path(DATA / "holdout" / "rfp" / "msit-national-scientist-2026.hwpx")
    assert len(doc.pages) == 4
    assert doc.pages[0].startswith("과학기술정보통신부 공고")
    assert all(len(p) <= 3000 + 500 for p in doc.pages)


def test_hwpx_named_hwp_is_detected_by_content():
    data = (DATA / "holdout" / "rfp" / "msit-rising-star-2026.hwpx").read_bytes()
    assert load_bytes(data, "공고.hwp").pages == load_path(DATA / "holdout" / "rfp" / "msit-rising-star-2026.hwpx").pages
