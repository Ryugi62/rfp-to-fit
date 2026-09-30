"""실측(390×844 모바일): 예시 공고 → 요건 목록 펼치기 → 요건 하나 원문 강조 → ✓ 맞음 → 집계, 가로 넘침 0인지.
uv run --with playwright python scripts/e2e_mobile.py [URL]"""
import sys
import time

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg.goto(url)
    pg.wait_for_selector("text=평가위원 6명에게 보내기", timeout=60000)
    pg.get_by_text("예시 공고", exact=True).click()
    pg.wait_for_selector("text=공고에서 찾은 것", timeout=120000)
    time.sleep(1.5)
    pg.get_by_text("보기 — 어기면 탈락인 것부터").click()
    time.sleep(1.5)
    cb = pg.get_by_role("combobox").last
    cb.scroll_into_view_if_needed()
    cb.click()
    time.sleep(1.5)
    pg.keyboard.press("ArrowDown")
    pg.keyboard.press("Enter")
    time.sleep(1.5)
    assert pg.locator("mark").count() >= 1, "원문 강조 없음"
    pg.get_by_role("radio", name="✓ 맞음").first.click()
    pg.wait_for_selector("text=요건 1개 확인", timeout=15000)
    time.sleep(1)
    m = pg.evaluate("() => ({vw: document.documentElement.clientWidth, sw: document.documentElement.scrollWidth,"
                    " df: [...document.querySelectorAll('[data-testid=stDataFrame]')].map(e => Math.round(e.getBoundingClientRect().right))})")
    full = pg.evaluate("() => Math.max(...[...document.querySelectorAll('[data-testid=stMain]')].map(e => e.scrollHeight), 844)")
    pg.set_viewport_size({"width": 390, "height": min(full, 8000)})
    time.sleep(1)
    pg.screenshot(path="deliver/shots/responsive/06-mobile-verify-390.png")
    print("OK", m, "tally:", pg.locator("text=현장 검증 —").first.inner_text())
    b.close()
