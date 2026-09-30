from rfp_to_fit.adapters.documents import hwpx_text, paginate


def test_hwpx_text_strips_nested_tags_and_linebreaks():
    xml = ('<hp:p id="1"><hp:run><hp:t>2026 NAIS<hp:lineBreak/>AI 해커톤</hp:t></hp:run></hp:p>'
           '<hp:p><hp:run><hp:t charPrIDRef="3">A &amp; B<hp:tab width="1"/>C</hp:t></hp:run></hp:p>')
    assert hwpx_text(xml) == ["2026 NAIS\nAI 해커톤", "A & B C"]


def test_paginate_splits_on_paragraph_boundaries():
    pages = paginate(["a" * 2000, "b" * 2000, "c" * 10], size=3000)
    assert len(pages) == 2 and pages[0] == "a" * 2000
