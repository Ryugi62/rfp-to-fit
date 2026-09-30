"""화면 실측: 앱을 실제 브라우저로 열어 예시 공고+초안으로 끝까지 실행하고 캡처한다."""
import sys, time
from playwright.sync_api import sync_playwright
url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
out = sys.argv[2] if len(sys.argv) > 2 else "deliver/shots"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 1000})
    pg.goto(url); pg.wait_for_selector("text=평가위원 6명에게 보내기", timeout=60000); time.sleep(2)
    pg.screenshot(path=f"{out}/01-input.png", full_page=True)
    t = time.time()
    pg.get_by_role("button", name="평가위원 6명에게 보내기").click()
    pg.wait_for_selector("text=심사기준 대조표", timeout=300000); time.sleep(3)
    print("run seconds", round(time.time() - t))
    pg.screenshot(path=f"{out}/02-result.png", full_page=True)
    for name, fn in [("② 우리 기획서 먼저 채점", "03-before-after"), ("③ 신뢰 장치·정확도", "04-trust")]:
        pg.get_by_role("tab", name=name).click(); time.sleep(2)
        pg.screenshot(path=f"{out}/{fn}.png", full_page=True)
    b.close()
