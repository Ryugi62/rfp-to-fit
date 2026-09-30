"""덱용 화면 캡처 — 라이브 앱을 실제 브라우저로 1회 실행(LLM 호출 1회)하고 요소 단위로 잘라 저장한다.

uv run --no-project --with playwright python deliver/deck/capture.py [URL]
출력: deliver/deck/shots/input.png · result.png · cards.png (prepare.py가 있으면 이걸 우선 쓴다)
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUT = Path(__file__).resolve().parent / "shots"
OUT.mkdir(exist_ok=True)


def box(pg, text):
    return pg.get_by_text(text, exact=False).first.bounding_box()


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 3200}, device_scale_factor=2)
    pg.goto(URL)
    pg.wait_for_selector("text=평가위원 5명에게 보내기", timeout=60000)
    time.sleep(2)
    btn = pg.get_by_role("button", name="평가위원 5명에게 보내기").bounding_box()
    top = box(pg, "1. 공고(RFP)")
    pg.screenshot(path=str(OUT / "input.png"),
                  clip={"x": btn["x"] - 10, "y": top["y"] - 16, "width": btn["width"] + 20,
                        "height": btn["y"] + btn["height"] - top["y"] + 32})
    t = time.time()
    pg.get_by_role("button", name="평가위원 5명에게 보내기").click()
    pg.wait_for_selector("text=심사기준 대조표", timeout=300000)
    time.sleep(4)
    print("run seconds", round(time.time() - t))
    head = box(pg, "모두가 깎는 곳")
    table = box(pg, "심사기준 대조표")
    pg.screenshot(path=str(OUT / "result.png"),
                  clip={"x": btn["x"] - 10, "y": head["y"] - 16, "width": btn["width"] + 20, "height": 330})
    g = box(pg, "고칠 곳 — 합의 결핍")
    pr = pg.get_by_text("선행연구", exact=False).last.bounding_box() or {"y": g["y"] + 700}
    pg.screenshot(path=str(OUT / "cards.png"),
                  clip={"x": btn["x"] - 10, "y": g["y"] - 16, "width": btn["width"] + 20,
                        "height": min(900, pr["y"] - g["y"] + 4)})
    pg.screenshot(path=str(OUT / "_full.png"), full_page=True)
    b.close()
