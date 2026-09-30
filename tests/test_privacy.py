from rfp_to_fit.domain.privacy import mask_pii


def test_masks_phone_email_rrn_birthdate():
    t = "휴대전화\n010-9303-1412\n이메일\nabc.def@naver.com\n주민 010101-3123456\n생년월일\n01. 10. 20.\n"
    out, c = mask_pii(t)
    assert "9303" not in out and "naver.com" not in out and "3123456" not in out and "01. 10. 20." not in out
    assert c["전화"] == 1 and c["이메일"] == 1 and c["주민번호"] == 1 and c["생년월일"] == 1


def test_keeps_ordinary_numbers_and_dates_in_text():
    t = "2026년 예산안 기준 35조 원, 재현율 90% 이상, 9.30.(수)~10.01.(목) 본선"
    out, c = mask_pii(t)
    assert out == t and c == {}


import pytest  # noqa: E402


@pytest.mark.parametrize("kind, text, secret", [
    ("주민번호", "주민등록번호 900101-1234567 입니다", "1234567"),
    ("전화", "연락처 02-123-4567 로", "123-4567"),
    ("전화", "휴대폰 010 1234 5678 로", "1234 5678"),
    ("이메일", "메일 a.b+c@lab.kaist.ac.kr 로", "kaist"),
    ("생년월일", "생년월일: 1990. 01. 01.\n", "1990"),
    ("생년월일", "1990년 1월 1일생", "1990"),
])
def test_each_pii_kind_is_masked_alone(kind, text, secret):
    out, c = mask_pii(text)
    assert secret not in out
    assert c == {kind: 1}
    assert f"[{kind} 가림]" in out


def test_schedule_date_at_line_end_is_not_birthdate():
    t = "개발 일정\n1단계 완료: 2026. 10. 12.\n2단계 착수"
    out, c = mask_pii(t)
    assert out == t and c == {}


def test_deadline_date_is_not_birthdate():
    t = "접수 마감 2026-10-12\n"
    assert mask_pii(t) == (t, {})
