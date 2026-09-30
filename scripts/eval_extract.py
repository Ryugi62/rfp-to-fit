"""정답표 대비 공고 파싱 정확도: python scripts/eval_extract.py [gemini|solar] → data/eval/extract-<llm>.json"""
import json, os, sys, time
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
from rfp_to_fit.adapters.llm import OpenAILLM
llm = {"gemini": lambda: FallbackLLM(GeminiLLM(), SolarLLM()),
       "solar": lambda: FallbackLLM(SolarLLM(temperature=0.0), GeminiLLM()),
       "openai": lambda: FallbackLLM(OpenAILLM(os.environ.get("RFP_OPENAI_MODEL", "gpt-4.1")), SolarLLM(temperature=0.0))}[which]()
out, root = [], Path("data")
for gold_path in sorted((root / "gold").glob("*.json")):
    gold = json.loads(gold_path.read_text())
    if only and gold["id"] not in only:
        continue
    doc = load_path(root / "rfp" / f"{gold['id']}.pdf", gold["id"])
    t = time.time()
    ex = extract_rfp(doc, llm)
    sec = time.time() - t
    exr = [{"text": r.text, "quote": r.evidence.quote, "page": r.evidence.page, "consequence": r.consequence} for r in ex.requirements]
    exc = [{"name": c.name, "points": c.points, "stage": c.stage} for c in ex.criteria]
    m = match_requirements(gold["requirements"], exr)
    rec = recall(m); ca = criteria_agreement(gold["criteria"], exc)
    from rfp_to_fit.domain.metrics import match_score
    hard = [c for c in exr if c["consequence"] in ("탈락", "감점", "불이익")]
    def hits(rows):
        return sum(any(match_score(g["text"], c["text"], c["quote"]) >= 0.5 and (not c["page"] or abs(c["page"] - g["page"]) <= 1)
                       for g in gold["requirements"]) for c in rows)
    prec_all = hits(exr) / len(exr) if exr else 0.0
    prec_hard = hits(hard) / len(hard) if hard else 0.0
    rec_hard = recall(match_requirements(gold["requirements"], hard))
    missed = [g["id"] + " " + g["text"][:50] for g, c, s in m if c is None]
    Path(f"data/eval/extract-{gold['id']}.rows.json").parent.mkdir(parents=True, exist_ok=True)
    Path(f"data/eval/extract-{gold['id']}.rows.json").write_text(json.dumps(exr, ensure_ascii=False, indent=0))
    print(f"   정밀도(전체) {prec_all:.0%} · 탈락·감점 태그 {len(hard)}개 정밀도 {prec_hard:.0%} 재현율 {rec_hard:.0%}")
    print(f"{gold['id']}: 요건 재현율 {rec:.0%} ({sum(1 for _,c,_ in m if c)}/{len(m)}) · 지표 일치 {ca:.0%} · 추출 {len(exr)} · 인용탈락 {len(ex.dropped)} · {sec:.0f}s")
    for x in missed: print("   miss", x)
    out.append({"id": gold["id"], "model": getattr(llm, "last_model", None) or llm.name, "recall": rec, "criteria_agreement": ca,
                "n_gold": len(m), "n_extracted": len(exr), "precision": prec_all, "n_hard": len(hard),
                "precision_hard": prec_hard, "recall_hard": rec_hard, "dropped": len(ex.dropped), "seconds": round(sec, 1), "missed": missed})
Path("data/eval").mkdir(parents=True, exist_ok=True)
dst = Path(f"data/eval/extract-{which}.json")   # 일부만 다시 재면 기존 행과 합친다
prev = {r["id"]: r for r in json.loads(dst.read_text())} if dst.exists() else {}
prev.update({r["id"]: r for r in out})
dst.write_text(json.dumps(list(prev.values()), ensure_ascii=False, indent=1))
