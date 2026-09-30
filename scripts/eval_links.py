"""링크 입력 실측(LLM 미사용): 실제 공고 주소에서 공고문을 골라 내려받아 읽을 수 있는지 → data/eval/link-fetch.json"""
import json, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
from rfp_to_fit.adapters.fetch import fetch_url, load_fetched

MSIT = "https://www.msit.go.kr/bbs/view.do?sCode=user&mId=311&mPid=121&bbsSeqNo=100&nttSeqNo="
URLS = [("NST 공지(HWP 첨부)", "https://www.nst.re.kr/www/selectBbsNttView.do?key=54&bbsNo=1&nttNo=51734"),
        ("산업통상부 공지(공고문 2개)", "https://www.motir.go.kr/kor/article/ATCL2826a2625/70794/view"),
        ("우주항공청 공고 PDF 직링크", "https://research.kau.ac.kr/upfile/2026/03/20260318101946-9198.pdf")] + \
       [(f"과기정통부 사업공고 {n}", MSIT + str(n)) for n in (3186886, 3186885, 3186884, 3186883, 3186882, 3186881, 3186880, 3186879, 3186878, 3186877)]
rows = []
for label, u in URLS:
    t = time.time()
    try:
        f = fetch_url(u); d, spans = load_fetched(f)
        rows.append({"label": label, "url": u, "ok": sum(map(len, d.pages)) > 500, "seconds": round(time.time() - t, 1),
                     "attachments": len(f.attachments), "chosen": [s[0] for s in spans], "pages": len(d.pages)})
    except Exception as e:
        rows.append({"label": label, "url": u, "ok": False, "error": str(e)[:200]})
    print(rows[-1]["ok"], rows[-1].get("seconds"), label, rows[-1].get("chosen"))
Path("data/eval/link-fetch.json").write_text(json.dumps({"n": len(rows), "ok": sum(r["ok"] for r in rows), "rows": rows}, ensure_ascii=False, indent=1))
