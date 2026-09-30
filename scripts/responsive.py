"""반응형 실측: 예시 공고+예시 초안으로 한 번 실행한 뒤, 같은 화면을 1280·390 폭으로 바꿔 가며
가로 넘침(문서 폭 > 창 폭)과 창 밖으로 삐져나간 요소를 세고 캡처한다. SPEC 「UI 수용기준」의 측정 도구.
uv run python scripts/responsive.py [URL] [출력 폴더]"""
import json
import sys
import time

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
out = sys.argv[2] if len(sys.argv) > 2 else "deliver/shots/responsive"
WIDTHS = [(1280, 900), (390, 844)]

PROBE = """() => {
  const vw = document.documentElement.clientWidth;
  const main = document.querySelector('section.main, [data-testid="stMain"]') || document.body;
  const over = [];
  for (const el of main.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (el.closest('details:not([open])') && !el.closest('summary')) continue;  // 접힌 섹션 안은 화면에 없다
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    // 가로 스크롤 컨테이너(표) 안의 요소는 넘쳐도 정상 — 스크롤 컨테이너 자체만 본다
    let p = el.parentElement, inScroller = false;
    while (p && p !== main) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') { inScroller = true; break; } p = p.parentElement; }
    if (!inScroller && (r.right > vw + 1 || r.left < -1)) over.push((el.className || el.tagName).toString().slice(0, 60) + ' ' + Math.round(r.left) + '~' + Math.round(r.right));
  }
  const fs = [...main.querySelectorAll('p, div.muted, div.sub, label, button')].map(e => parseFloat(getComputedStyle(e).fontSize)).filter(x => x > 0);
  return { vw, scrollW: document.documentElement.scrollWidth, overflowX: document.documentElement.scrollWidth > vw + 1,
           outside: over.slice(0, 15), n_outside: over.length, min_font: Math.min(...fs) };
}"""


def shoot(pg, tag):
    res = {}
    for w, h in WIDTHS:
        pg.set_viewport_size({"width": w, "height": h})
        time.sleep(1.5)
        res[w] = pg.evaluate(PROBE)
        # Streamlit은 문서가 아니라 안쪽 컨테이너가 스크롤한다 → 창을 내용 높이만큼 늘려 전체를 찍는다
        full = pg.evaluate("() => Math.max(...[...document.querySelectorAll('[data-testid=stMain], section.main, .main')].map(e => e.scrollHeight), 0)")
        pg.set_viewport_size({"width": w, "height": max(h, min(full, 12000))})
        time.sleep(1.5)
        pg.screenshot(path=f"{out}/{tag}-{w}.png")
        pg.set_viewport_size({"width": w, "height": h})
    return res


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.goto(url)
    pg.wait_for_selector("text=평가위원 6명에게 보내기", timeout=60000)
    time.sleep(2)
    report = {"input": shoot(pg, "01-input")}
    pg.set_viewport_size({"width": 1280, "height": 900})
    pg.get_by_text("예시 공고", exact=True).click()
    pg.get_by_text("예시: 우리 팀 예선 기획서", exact=True).click()
    pg.wait_for_selector("text=공고에서 찾은 것", timeout=120000)
    time.sleep(2)
    report["parsed"] = shoot(pg, "02-parsed")
    pg.set_viewport_size({"width": 1280, "height": 900})
    t = time.time()
    pg.get_by_role("button", name="평가위원 6명에게 보내기").click()
    pg.wait_for_selector("text=심사기준 대조표", timeout=300000)
    time.sleep(3)
    report["run_seconds"] = round(time.time() - t)
    report["result"] = shoot(pg, "03-result")
    for name, fn in [("② 우리 기획서 먼저 채점", "04-before-after"), ("③ 신뢰 장치·정확도", "05-trust")]:
        pg.set_viewport_size({"width": 1280, "height": 900})
        pg.get_by_role("tab", name=name).click()
        time.sleep(2)
        report[fn] = shoot(pg, fn)
    b.close()
print(json.dumps(report, ensure_ascii=False, indent=1))
