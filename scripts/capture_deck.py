"""덱 4장용 실제 화면 캡처: 공고 링크(NST 공지·HWP 첨부) 붙여넣기 → 예시 초안 → 실행 → 원문 보기 → ✓ → 현장 검증 집계.
→ deliver/deck/shots/input.png · result.png"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
URL = "http://localhost:8501"
LINK = "https://www.nst.re.kr/www/selectBbsNttView.do?key=54&bbsNo=1&nttNo=51734"
out = Path("deliver/deck/shots"); out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1400, "height": 1000}, device_scale_factor=2)
    pg.goto(URL); pg.wait_for_selector("text=평가위원 6명에게 보내기", timeout=60000)
    box = pg.get_by_placeholder("IRIS·과기정통부·기관 게시판 공지 주소 또는 공고 PDF 주소"); box.fill(LINK); box.press("Enter")
    pg.wait_for_selector("text=/공고 파싱 완료/", timeout=300000); time.sleep(1)
    pg.get_by_text("예시: 우리 팀 예선 기획서").click(); time.sleep(2)
    top = pg.get_by_text("1. 공고(RFP)").bounding_box(); bot = pg.get_by_role("button", name="평가위원 6명에게 보내기").bounding_box()
    pg.screenshot(path=str(out / "input.png"), clip={"x": 180, "y": top["y"] - 10, "width": 1040, "height": bot["y"] + bot["height"] - top["y"] + 20})
    t0 = time.time(); pg.get_by_role("button", name="평가위원 6명에게 보내기").click()
    pg.wait_for_selector("text=/완료 · [0-9]+초/", timeout=500000); print("run", round(time.time() - t0), "s")
    time.sleep(2)
    pg.get_by_text("원문 보기 — 공고 근거").first.click(); time.sleep(1)
    pg.get_by_role("button", name="✓ 맞음").first.click(); time.sleep(3)
    pg.get_by_text("원문 보기 — 공고 근거").first.click(); time.sleep(1.5)
    tally = pg.locator("text=/사람 확인 정밀도 [0-9]+%/").first
    tally.scroll_into_view_if_needed(); time.sleep(0.8)
    tb = tally.bounding_box()
    pg.screenshot(path=str(out / "result.png"), clip={"x": 180, "y": max(0, tb["y"] - 10), "width": 1040, "height": min(880, 1000 - max(0, tb["y"] - 10))})
    print(tally.inner_text()[:120])
    b.close()
