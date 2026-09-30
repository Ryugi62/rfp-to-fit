"""데모 영상 녹화: 실제 앱을 브라우저로 조작하며 화면을 녹화하고, 장면 시각을 기록한다.
python scripts/record_demo.py [url] → deliver/demo/raw.webm + deliver/demo/events.json
대기(LLM 호출) 구간은 make_demo.py가 배속 처리하고 화면에 「실제 N초 · 4배속」을 표기한다(숨기지 않음)."""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
out = Path("deliver/demo")
out.mkdir(parents=True, exist_ok=True)
ev = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(out / "tmp"),
                        record_video_size={"width": 1440, "height": 900}, device_scale_factor=1)
    pg = ctx.new_page()
    t0 = time.time()
    mark = lambda k: ev.__setitem__(k, round(time.time() - t0, 2))  # noqa: E731
    pg.goto(url)
    pg.wait_for_selector("text=평가위원 5명에게 보내기", timeout=60000)
    time.sleep(1.0); mark("landing")
    time.sleep(6.0)
    pg.mouse.wheel(0, 250); time.sleep(0.5); mark("inputs")
    time.sleep(7.0)
    pg.get_by_role("button", name="평가위원 5명에게 보내기").click(); mark("click")
    pg.wait_for_selector("text=심사기준 대조표", timeout=300000); mark("done")
    time.sleep(1.0)
    pg.evaluate("window.scrollTo({top: document.querySelector('.big')?.getBoundingClientRect().top + window.scrollY - 120, behavior: 'smooth'})")
    time.sleep(8.0); mark("result")
    pg.mouse.wheel(0, 520); time.sleep(1.0); mark("cards")
    time.sleep(6.0)
    try:
        pg.get_by_text("평가위원 메모·인용 보기").first.click(); time.sleep(0.8); mark("memo")
    except Exception:
        mark("memo")
    time.sleep(7.0)
    pg.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})"); time.sleep(1.0)
    pg.get_by_role("tab", name="② 우리 기획서 전·후").click(); time.sleep(1.0); mark("before_after")
    time.sleep(9.0)
    pg.get_by_role("tab", name="③ 신뢰 장치·정확도").click(); time.sleep(1.0); mark("trust")
    time.sleep(9.0); mark("end")
    video = pg.video.path()
    ctx.close(); b.close()
Path(video).rename(out / "raw.webm")
(out / "events.json").write_text(json.dumps(ev, indent=1))
print(ev)
