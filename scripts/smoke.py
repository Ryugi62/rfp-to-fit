"""실측: 공고 1건 파싱 → 요건·지표 수, 인용 탈락 수, 소요 시간."""
import sys, time, json
from dotenv import load_dotenv
load_dotenv()
from rfp_to_fit.adapters.documents import load_path
from rfp_to_fit.adapters.llm import GeminiLLM, SolarLLM
from rfp_to_fit.application.extract import extract_rfp

path = sys.argv[1]; which = sys.argv[2] if len(sys.argv) > 2 else "gemini"
llm = GeminiLLM() if which == "gemini" else SolarLLM()
doc = load_path(path)
t = time.time()
ex = extract_rfp(doc, llm)
print(llm.name, f"{time.time()-t:.1f}s pages={len(doc.pages)} reqs={len(ex.requirements)} crits={len(ex.criteria)} dropped={len(ex.dropped)}")
for c in ex.criteria: print(" C", c.name, c.points, c.stage, "p", c.evidence.page)
for r in ex.requirements[:40]: print(" R", r.category, r.text[:60], "p", r.evidence.page)
for d in ex.dropped[:5]: print(" X", json.dumps(d, ensure_ascii=False)[:150])
