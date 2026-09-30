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
