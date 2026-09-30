"""실측: 예시 공고+예시 초안, 보안 모드 → 원문 보기·✓맞음 → 현장 검증 집계가 뜨는지."""
import sys, time
from playwright.sync_api import sync_playwright
url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1400, "height": 1100})
    pg.goto(url); pg.wait_for_selector("text=평가위원 6명에게 보내기", timeout=60000)
    pg.get_by_text("예시 공고", exact=True).click(); time.sleep(1.5)
    pg.get_by_text("예시: 우리 팀 예선 기획서").click(); time.sleep(1.5)
    pg.get_by_text("🔒 보안 모드", exact=False).first.click(); time.sleep(1)
    t0 = time.time(); pg.get_by_role("button", name="평가위원 6명에게 보내기").click()
    pg.wait_for_selector("text=/완료 · [0-9]+초/", timeout=500000); print("run", round(time.time() - t0), "s")
    time.sleep(2)
    pg.get_by_text("원문 보기 — 공고 근거").first.click(); time.sleep(1)
    pg.get_by_role("button", name="✓ 맞음").first.click(); time.sleep(2.5)
    print(pg.locator("text=/현장 검증/").first.inner_text()[:200])
    pg.screenshot(path="deliver/shots/07-verify.png", full_page=True)
    b.close()
