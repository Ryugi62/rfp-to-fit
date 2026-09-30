"""LLM 호출 없이 저장된 실행 기록 화면(앱 「② 우리 기획서 전·후」 탭)을 캡처 → deliver/deck/shots/result.png
9장 숫자(data/runs/*.json)와 같은 실행이라 덱 안에서 숫자가 어긋나지 않는다.
uv run --no-project --with playwright python deliver/deck/capture_saved.py [URL]"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUT = Path(__file__).resolve().parent / "shots"; OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1400, "height": 1600}, device_scale_factor=2)
    pg.goto(URL); pg.get_by_role("tab").nth(1).wait_for(timeout=90000); time.sleep(3)
    pg.get_by_role("tab").nth(1).click(); time.sleep(4)
    h = pg.get_by_text("이 대회의 공고와 본선 심사표로", exact=False).first.bounding_box()
    end = pg.get_by_text("보완 = 기획서에", exact=False).first.bounding_box()
    btab = pg.get_by_role("tab").nth(0).bounding_box()
    x = btab["x"] - 10; w = 1400 - 2 * x
    pg.screenshot(path=str(OUT / "result.png"), clip={"x": x, "y": h["y"] - 12, "width": w, "height": end["y"] + end["height"] - h["y"] + 24})
    b.close()
print("saved", OUT / "result.png")
