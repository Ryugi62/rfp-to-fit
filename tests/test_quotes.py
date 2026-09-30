from rfp_to_fit.domain.quotes import context, locate, normalize, verify_quote


def test_locate_returns_span_in_original_text_with_symbols_between():
    src = "목표: 「재현율」 90 % 이상."
    a, b = locate("재현율 90%", src)
    assert src[a:b] == "재현율」 90 %"


def test_locate_none_for_too_short_or_missing_or_empty_source():
    assert locate("가", "가나다") is None          # 정규화 후 2자 미만
    assert locate("다라", "가나다") is None
    assert locate("가나", "") is None
    assert locate("가나", None) is None


def test_locate_finds_first_occurrence():
    assert locate("ab", "xab-ab") == (1, 3)


def test_context_clamps_radius_at_both_ends():
    src = "0123456789ABCDEFGHIJ"
    pre, hit, post = context("ABC", src, radius=3)
    assert (pre, hit, post) == ("789", "ABC", "DEF")
    pre, hit, post = context("0123", src, radius=50)
    assert pre == "" and hit == "0123" and post == src[4:]


def test_context_none_when_quote_absent():
    assert context("없는 인용", "원문 텍스트") is None


def test_context_hit_equals_verify_quote_result():
    src = "## 3) 구현\n- 요건 추출 **재현율** 90% 이상"
    q = "요건 추출 재현율 90%"
    assert verify_quote(q, src)
    _, hit, _ = context(q, src)
    assert normalize(hit) == normalize(q)
