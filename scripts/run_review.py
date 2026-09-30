"""공고 1건 + 초안 1건 끝까지: python scripts/run_review.py <rfp_id> <draft.md> [stage] [out.json]"""
import json, sys, time
from pathlib import Path
from rfp_to_fit.infrastructure.wiring import examiners, make_llms, personas_with_models, prior_search
from rfp_to_fit.adapters.documents import load_path
from rfp_to_fit.application.extract import extract_rfp, Extraction
from rfp_to_fit.adapters.graph import run_graph as run_review
from rfp_to_fit.application.serialize import extraction_to_dict, extraction_from_dict, run_to_dict

rid, draft_path = sys.argv[1], sys.argv[2]
stage = sys.argv[3] if len(sys.argv) > 3 else None
out = sys.argv[4] if len(sys.argv) > 4 else f"data/runs/{rid}--{Path(draft_path).stem}.json"
gemini, solar = make_llms()
cache = Path(f"data/cache/{rid}.extract.json")
if cache.exists():
    ex = extraction_from_dict(json.loads(cache.read_text()))
else:
    ex = extract_rfp(load_path(f"data/rfp/{rid}.pdf", rid), gemini)
    cache.parent.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(extraction_to_dict(ex), ensure_ascii=False, indent=1))
if stage:
    ex = Extraction(ex.requirements, [c for c in ex.criteria if c.stage == stage], ex.dropped)
print("criteria:", [(c.name, c.points, c.stage) for c in ex.criteria])
personas, llm_for = personas_with_models(gemini, solar)
from rfp_to_fit.domain.model import CheckItem
from rfp_to_fit.application.review import build_rubric
rcache = Path(f"data/cache/{rid}.{stage or 'all'}.rubric.json")   # 같은 공고는 같은 점검 항목으로(전후 비교 공정성)
if rcache.exists():
    items = [CheckItem(**i) for i in json.loads(rcache.read_text())]
else:
    guide = "\n".join(f"- {r.text}" for r in ex.requirements if r.category in ("형식", "제출서류"))[:3000]
    items = build_rubric(ex.criteria, gemini, guide)
    rcache.write_text(json.dumps([i.__dict__ for i in items], ensure_ascii=False, indent=1))
t = time.time()
from rfp_to_fit.domain.privacy import mask_pii
run = run_review(ex, mask_pii(Path(draft_path).read_text())[0], personas, gemini, llm_for, on_step=lambda n, r: print(" ", n, r), items=items, prior_search=prior_search(), examiner_for=examiners())
print(f"{time.time()-t:.0f}s expected {run.table.expected_total:.1f}/{run.table.total_points:g}")
for r in run.table.rows:
    print(f" {r.criterion.name} {r.expected_points:.1f}/{r.criterion.points:g}", {k: round(v, 1) for k, v in r.per_reviewer.items()})
    for f in r.findings:
        item = next(i for i in run.items if i.id == f.item_id)
        print(f"    [{f.kind.value}] {item.question[:50]} gap={f.gap_ratio:.1f} demoted={f.demoted}")
for x in run.remedies: print("  보완", x)
Path(out).parent.mkdir(parents=True, exist_ok=True); Path(out).write_text(json.dumps(run_to_dict(run), ensure_ascii=False, indent=1))
