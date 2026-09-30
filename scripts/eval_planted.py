"""결함 주입 실험: python scripts/eval_planted.py → data/eval/planted.json"""
import json, statistics
from pathlib import Path
from rfp_to_fit.infrastructure.wiring import make_llms, personas_with_models
from rfp_to_fit.application.extract import Extraction
from rfp_to_fit.application.serialize import extraction_from_dict
from rfp_to_fit.adapters.graph import run_graph
from rfp_to_fit.domain.model import CheckItem
from rfp_to_fit.domain.planted import score_variant

import sys
STAGE = sys.argv[1] if len(sys.argv) > 1 else "예선"
PLANTED = sys.argv[2] if len(sys.argv) > 2 else "planted.json"
OUT = sys.argv[3] if len(sys.argv) > 3 else "data/eval/planted.json"
rid = "nais-hackathon-2026"; D = Path("data/drafts") / rid
ex = extraction_from_dict(json.loads(Path(f"data/cache/{rid}.extract.json").read_text()))
ex = Extraction(ex.requirements, [c for c in ex.criteria if c.stage == STAGE], ex.dropped)
items = [CheckItem(**i) for i in json.loads(Path(f"data/cache/{rid}.{STAGE}.rubric.json").read_text())]
cname = {c.id: c.name for c in ex.criteria}
item_crit = {i.id: cname[i.criterion_id] for i in items}
gemini, solar = make_llms(); personas, llm_for = personas_with_models(gemini, solar)

def ratios(text):
    run = run_graph(ex, text, personas, gemini, llm_for, items=items)
    return {f.item_id: f.gap_ratio for r in run.table.rows for f in r.findings}, run.table.expected_total, \
           {r.criterion.name: r.expected_points for r in run.table.rows}

orig = (D / "original.md").read_text()
bases = [ratios(orig) for _ in range(2)]
base = {k: statistics.mean(b[0].get(k, 0) for b in bases) for k in bases[0][0]}
base_total = statistics.mean(b[1] for b in bases)
print("base total", round(base_total, 1))
planted = json.loads((D / PLANTED).read_text())
rows = []
for name, spec in planted.items():
    r, total, per = ratios((D / f"{name}.md").read_text())
    det, n_new, n_hit = score_variant(base, r, item_crit, set(spec["expected_criteria"]))
    rows.append({"variant": name, "expected": spec["expected_criteria"], "detected": det, "new_gaps": n_new, "hits": n_hit,
                 "total": round(total, 1), "per": {k: round(v, 1) for k, v in per.items()}})
    print(rows[-1])
n = len(rows)
new_total = sum(x["new_gaps"] for x in rows); hit_total = sum(x["hits"] for x in rows)
out = {"n": n, "detect_rate": sum(x["detected"] for x in rows) / n,
       "precision": hit_total / new_total if new_total else None,
       "base_total": round(base_total, 1), "stage": STAGE, "planted": PLANTED, "rows": rows, "rule": "원본 2회 평균 대비 점검 항목 감점 비율 +0.4 이상(5명 중 2명 이상) = 새 결핍"}
Path(OUT).write_text(json.dumps(out, ensure_ascii=False, indent=1))
print("detect", out["detect_rate"], "precision", out["precision"])
