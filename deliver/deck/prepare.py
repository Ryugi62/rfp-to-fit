"""덱 숫자·이미지 준비 — 숫자는 전부 data/ JSON에서 빌드 시점에 읽는다(손으로 적은 숫자 0개).

출력: deliver/deck/build/numbers.json, build/img/*.png(화면 캡처 잘라낸 것), build/img/qr-*.png
실행: deliver/deck/build.sh 가 부른다(prepare.py). LIVE_URL 환경변수로 라이브 주소를 바꿀 수 있다.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pypdfium2
import qrcode
from PIL import Image

DECK = Path(__file__).resolve().parent
ROOT = DECK.parents[1]
OUT = DECK / "build"
IMG = OUT / "img"
PENDING = "측정 중"

LIVE_URL = os.environ.get("LIVE_URL", "https://invisible-sail-shame-preliminary.trycloudflare.com")
REPO_URL = "https://github.com/Ryugi62/rfp-to-fit"
RID = "nais-hackathon-2026"


def load(p: str):
    return json.loads((ROOT / p).read_text())


def pct(x: float) -> int:
    return round(x * 100)


def run_numbers(run: dict) -> dict:
    trace = {t["step"]: t for t in run["trace"]}
    kinds: dict[str, list[str]] = {}
    for row in run["table"]:
        for f in row["findings"]:
            kinds.setdefault(f["kind"], []).append(f["item_id"])
    q = {i["id"]: i["question"] for i in run["items"]}
    crit = {c["id"]: c for c in run["criteria"]}
    per = [{"name": crit[r["criterion_id"]]["name"], "points": crit[r["criterion_id"]]["points"],
            "got": round(r["expected_points"], 1)} for r in run["table"]]
    review = trace.get("독립 채점", {})
    recheck = trace.get("재질의", {})
    return {
        "total": round(sum(r["expected_points"] for r in run["table"]), 1),
        "per": per,
        "n_req": len(run["requirements"]),
        "n_crit": len(run["criteria"]),
        "n_items": len(run["items"]),
        "n_verdicts": review.get("n", len(run["verdicts"])),
        "invalid": review.get("invalid", 0),
        "asked": recheck.get("asked", 0),
        "fixed": recheck.get("fixed", 0),
        "seconds": round(max(t["t"] for t in run["trace"])),
        "gaps": [q[i] for i in kinds.get("합의 결핍", [])],
        "contested": [q[i] for i in kinds.get("논쟁 지점", [])],
        "n_gaps": len(kinds.get("합의 결핍", [])),
        "n_contested": len(kinds.get("논쟁 지점", [])),
        "mcp_via": trace.get("선행 탐색", {}).get("via", ""),
        "personas": [{"name": p["name"], "model": p["model"]} for p in run["personas"]],
        "answered": sorted({v["reviewer_id"] for v in run["verdicts"]}),
        "reviewers": review.get("reviewers", len({v["reviewer_id"] for v in run["verdicts"]})),
    }


def git_facts() -> dict:
    log = subprocess.run(["git", "-C", str(ROOT), "log", "--reverse", "--format=%ad\t%s", "--date=format:%m/%d %H:%M"],
                         capture_output=True, text=True).stdout.strip().splitlines()
    code = [l.split("\t")[0] for l in log if "코드 없음" not in l]
    return {"commits": len(log), "first_code": code[0] if code else PENDING}


def crop_shots() -> dict:
    """capture.py 결과(deliver/deck/shots/)가 있으면 그걸, 없으면 deliver/shots/ 전체 캡처를 잘라 쓴다."""
    IMG.mkdir(parents=True, exist_ok=True)
    mine = DECK / "shots"
    shots = ROOT / "deliver" / "shots"
    boxes = {  # (좌, 위, 우, 아래) — 1400×1000 전체 캡처 기준. Streamlit 상단 바·잘린 머리글 제외
        "result": ("02-result.png", (615, 722, 1220, 985)),  # 심사기준 대조표만
        "input": ("01-input.png", (180, 262, 1220, 600)),
    }
    out = {}
    for key, (name, box) in boxes.items():
        if (mine / f"{key}.png").exists():
            im = Image.open(mine / f"{key}.png").convert("RGB")
        elif (shots / name).exists():
            im = Image.open(shots / name).convert("RGB").crop(box)
        else:
            continue
        p = IMG / f"{key}.png"
        im.save(p)
        out[key] = {"path": str(p), "w": im.width, "h": im.height}
    return out


def qr(url: str, name: str) -> str:
    p = IMG / f"qr-{name}.png"
    img = qrcode.make(url, border=1, box_size=12)
    img.save(p)
    return str(p)


def main():
    OUT.mkdir(exist_ok=True)
    ext = {e["id"]: e for e in load("data/eval/extract-gemini.json")}
    gold = {k: load(f"data/gold/{k}.json") for k in ext}
    pages = {k: len(pypdfium2.PdfDocument(str(ROOT / f"data/rfp/{k}.pdf"))) for k in ext}
    extract = []
    for k, e in ext.items():
        extract.append({"id": k, "agency": gold[k]["agency"].split(" ")[0].split("/")[0],
                        "recall": pct(e["recall"]), "n_gold": e["n_gold"],
                        "hit": e["n_gold"] - len(e["missed"]), "pages": pages[k], "model": e["model"],
                        "seconds": e["seconds"], "n_extracted": e["n_extracted"],
                        "missed_form": sum("기획서 항목" in m for m in e["missed"]),
                        "crit_agree": pct(e.get("criteria_agreement", 0))})
    motir = gold["motir-industrial-cluster-rnd-2026"]
    tracks = {c.get("track") for c in motir["criteria"] if c.get("track")}

    planted_path = ROOT / "data/eval/planted.json"
    planted = {"ready": False, "detect": PENDING, "precision": PENDING, "n": 5, "detected": PENDING}
    if planted_path.exists():
        p = json.loads(planted_path.read_text())
        if p.get("stage") == "예선":
            det = sum(1 for r in p["rows"] if r["detected"])
            planted = {"ready": True, "n": p["n"], "detected": det, "stage": p["stage"],
                       "detect": f"{det}/{p['n']}",
                       "precision": PENDING if p.get("precision") is None else f"{pct(p['precision'])}%"}

    v1 = []
    for f in sorted((ROOT / "data/eval").glob("planted-v1*.json")):
        q = json.loads(f.read_text())
        v1.append(sum(1 for r in q["rows"] if r["detected"]))
    if planted["ready"]:
        p = json.loads(planted_path.read_text())
        totals = [r["total"] for r in p["rows"]]
        planted.update({"v1": v1, "base": p["base_total"], "drop_min": round(p["base_total"] - max(totals), 1),
                        "drop_max": round(p["base_total"] - min(totals), 1)})
    before = run_numbers(load(f"data/runs/{RID}--original.json"))
    after = run_numbers(load(f"data/runs/{RID}--after.json"))
    tests = sum(l.lstrip().startswith("def test_") for f in (ROOT / "tests").glob("test_*.py")
                for l in f.read_text().splitlines())
    img = crop_shots()
    nums = {
        "motir": {"pages": pages["motir-industrial-cluster-rnd-2026"], "n_req": len(motir["requirements"]),
                  "tables": len(tracks) or PENDING},
        "extract": extract,
        "planted": planted,
        "before": before,
        "after": after,
        "git": git_facts(),
        "tests": tests,
        "live_url": LIVE_URL,
        "repo_url": REPO_URL,
        "img": img,
        "qr_live": qr(LIVE_URL, "live"),
        "qr_repo": qr(REPO_URL, "repo"),
    }
    for k, r in (("original", before), ("after", after)):
        if r["reviewers"] < len(r["personas"]):
            print(f"WARN: {k} 실행에서 평가위원 {len(r['personas'])}명 중 {r['reviewers']}명만 판정 — 덱의 「5명 독립 채점」과 어긋남. 재실행 필요", file=sys.stderr)
    if planted["ready"] is False:
        print("WARN: planted.json stage≠예선 → 8장 「측정 중」", file=sys.stderr)
    (OUT / "numbers.json").write_text(json.dumps(nums, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in nums.items() if k not in ("img",)}, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
