"""정답표 대비 공고 파싱 정확도: python scripts/eval_extract.py [gemini|solar] → data/eval/extract-<llm>.json"""
import json, sys, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from rfp_to_fit.adapters.documents import load_path
from rfp_to_fit.adapters.llm import GeminiLLM, SolarLLM
from rfp_to_fit.application.extract import extract_rfp
from rfp_to_fit.domain.metrics import criteria_agreement, match_requirements, recall

which = sys.argv[1] if len(sys.argv) > 1 else "gemini"
only = sys.argv[2:] 
from rfp_to_fit.adapters.llm import FallbackLLM
llm = FallbackLLM(GeminiLLM(), SolarLLM()) if which == "gemini" else SolarLLM()
out, root = [], Path("data")
for gold_path in sorted((root / "gold").glob("*.json")):
    gold = json.loads(gold_path.read_text())
    if only and gold["id"] not in only:
        continue
    doc = load_path(root / "rfp" / f"{gold['id']}.pdf", gold["id"])
    t = time.time()
    ex = extract_rfp(doc, llm)
    sec = time.time() - t
    exr = [{"text": r.text, "quote": r.evidence.quote, "page": r.evidence.page} for r in ex.requirements]
    exc = [{"name": c.name, "points": c.points, "stage": c.stage} for c in ex.criteria]
    m = match_requirements(gold["requirements"], exr)
    rec = recall(m); ca = criteria_agreement(gold["criteria"], exc)
    missed = [g["id"] + " " + g["text"][:50] for g, c, s in m if c is None]
    Path(f"data/eval/extract-{gold['id']}.rows.json").parent.mkdir(parents=True, exist_ok=True)
    Path(f"data/eval/extract-{gold['id']}.rows.json").write_text(json.dumps(exr, ensure_ascii=False, indent=0))
    print(f"{gold['id']}: 요건 재현율 {rec:.0%} ({sum(1 for _,c,_ in m if c)}/{len(m)}) · 지표 일치 {ca:.0%} · 추출 {len(exr)} · 인용탈락 {len(ex.dropped)} · {sec:.0f}s")
    for x in missed: print("   miss", x)
    out.append({"id": gold["id"], "model": getattr(llm, "last_model", None) or llm.name, "recall": rec, "criteria_agreement": ca,
                "n_gold": len(m), "n_extracted": len(exr), "dropped": len(ex.dropped), "seconds": round(sec, 1), "missed": missed})
Path("data/eval").mkdir(parents=True, exist_ok=True)
Path(f"data/eval/extract-{which}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
