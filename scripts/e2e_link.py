"""실측: 공고 링크 붙여넣기 → 초안 붙여넣기 → 끝까지."""
import sys, time
from playwright.sync_api import sync_playwright
url, link, draft = sys.argv[1], sys.argv[2], open(sys.argv[3]).read()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1400, "height": 1000})
    pg.goto(url); pg.wait_for_selector("text=평가위원 6명에게 보내기", timeout=60000)
    t0 = time.time()
    box = pg.get_by_placeholder("IRIS·과기정통부·기관 게시판 공지 주소 또는 공고 PDF 주소")
    box.fill(link); box.press("Enter")
    pg.wait_for_selector("text=/공고 파싱 완료/", timeout=300000); t1 = time.time()
    print("link→parse", round(t1 - t0), "s |", pg.locator("text=/공고 파싱 완료/").first.inner_text()[:200])
    print(pg.locator("text=공고에서 찾은 것").first.inner_text()[:200])
    pg.get_by_text("붙여넣기", exact=True).click(); time.sleep(1)
    pg.locator("textarea").first.fill(draft); pg.keyboard.press("Tab"); time.sleep(2)
    pg.get_by_role("button", name="평가위원 6명에게 보내기").click()
    pg.wait_for_selector("text=/완료 · [0-9]+초/", timeout=400000)
    print("review", round(time.time() - t1), "s |", pg.locator(".big").first.inner_text())
    time.sleep(2); pg.screenshot(path="deliver/shots/06-link-e2e.png", full_page=True)
    b.close()
