"""실측: 캐시 없는 경로 — 공고 PDF 업로드 + 초안 붙여넣기 → 끝까지. 소요 시간과 결과를 찍는다."""
import sys, time
from playwright.sync_api import sync_playwright
url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
pdf, draft = sys.argv[2], open(sys.argv[3]).read()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1400, "height": 1000})
    pg.goto(url); pg.wait_for_selector("text=평가위원 6명에게 보내기", timeout=60000)
    pg.get_by_text("직접 올리기(PDF·HWPX)").click(); time.sleep(1)
    t0 = time.time()
    pg.locator("input[type=file]").first.set_input_files(pdf)
    pg.wait_for_selector("text=공고에서 찾은 것", timeout=300000); t1 = time.time()
    print("parse", round(t1 - t0), "s ·", pg.locator("text=공고에서 찾은 것").first.inner_text()[:160])
    pg.get_by_text("붙여넣기").click(); time.sleep(1)
    pg.locator("textarea").first.fill(draft); pg.keyboard.press("Tab"); time.sleep(2)
    pg.get_by_role("button", name="평가위원 6명에게 보내기").click()
    pg.wait_for_selector("text=/완료 · [0-9]+초/", timeout=400000)
    print("review", round(time.time() - t1), "s")
    time.sleep(2); pg.screenshot(path="deliver/shots/05-upload-e2e.png", full_page=True)
    print(pg.locator(".big").first.inner_text(), "|", pg.locator("text=/근거 충족도/").first.inner_text()[:120])
    b.close()
