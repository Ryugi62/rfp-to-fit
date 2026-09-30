"""예시 공고 3건의 파싱·점검 질문 캐시를 주 엔진으로 새로 만든다(화면 예시·전후 비교가 같은 질문을 쓰게)."""
import json
from pathlib import Path
from rfp_to_fit.infrastructure.wiring import make_llms
from rfp_to_fit.adapters.documents import load_path
from rfp_to_fit.application.extract import extract_rfp
from rfp_to_fit.application.review import build_rubric
from rfp_to_fit.application.serialize import extraction_to_dict

main, _ = make_llms()
for rid in ["nais-hackathon-2026", "kasa-space-manufacturing-platform-2026", "motir-industrial-cluster-rnd-2026"]:
    ex = extract_rfp(load_path(f"data/rfp/{rid}.pdf", rid), main)
    Path(f"data/cache/{rid}.extract.json").write_text(json.dumps(extraction_to_dict(ex), ensure_ascii=False, indent=1))
    guide = "\n".join(f"- {r.text}" for r in ex.requirements if r.category in ("형식", "제출서류"))[:3000]
    stages = sorted({c.stage for c in ex.criteria})
    for st in stages:
        cs = [c for c in ex.criteria if c.stage == st]
        items = build_rubric(cs, main, guide)
        key = st if len(stages) > 1 else "all"
        Path(f"data/cache/{rid}.{key}.rubric.json").write_text(json.dumps([i.__dict__ for i in items], ensure_ascii=False, indent=1))
    print(rid, len(ex.requirements), [(c.name, c.points, c.stage) for c in ex.criteria])
