"""에이전트 흐름을 LangGraph 상태 그래프로 조립한다.
점검 질문 → 독립 채점(5명 병렬) → 인용 실재 검사 → (무효 판정이 있으면) 재질의 1회 → 집계 → 보완 지정."""
from __future__ import annotations

import time
from typing import Any, Callable, TypedDict

from langgraph.graph import END, StateGraph

from ..application.extract import Extraction
from ..application.pipeline import ReviewRun
from ..application.prior_art import as_context, find_prior_art
from ..application.review import build_rubric, recheck, remedy, review_all
from ..domain.aggregate import build_fit_table, effective_label


class S(TypedDict, total=False):
    items: list
    prior: list
    verdicts: list
    stances: list
    failed: list
    rechecked: int
    table: Any
    remedies: list


def build_graph(ex: Extraction, draft: str, personas, llm, llm_for, on_step: Callable | None = None, items=None,
                prior_search=None):
    t0 = time.time()
    trace: list[dict] = []

    def step(name, **info):
        rec = {"step": name, "t": round(time.time() - t0, 1), **info}
        trace.append(rec)
        if on_step:
            on_step(name, rec)

    invalid = lambda v: effective_label(v, draft) is None  # noqa: E731

    def n_rubric(s: S):
        its = items
        if its is None:
            guide = "\n".join(f"- {r.text}" for r in ex.requirements if r.category in ("형식", "제출서류"))[:3000]
            its = build_rubric(ex.criteria, llm, guide)
        step("점검 항목", n=len(its))
        return {"items": its}

    def n_prior(s: S):
        if prior_search is None:
            return {"prior": []}
        try:
            qs, works = find_prior_art(draft, llm, prior_search)
        except Exception:
            qs, works = [], []
        step("선행 탐색", queries=qs, n=len(works), via=getattr(prior_search, "name", ""))
        return {"prior": works}

    def n_review(s: S):
        vs, stances, failed = review_all(personas, ex.criteria, s["items"], draft, llm_for,
                                         as_context(s.get("prior", [])), with_stance=True)
        bad = sum(1 for v in vs if invalid(v))
        step("독립 채점", n=len(vs), reviewers=len({v.reviewer_id for v in vs}), of=len(personas), invalid=bad, failed=failed)
        return {"verdicts": vs, "stances": stances, "failed": failed, "rechecked": 0}

    def route(s: S):
        return "recheck" if s.get("rechecked", 0) == 0 and any(invalid(v) for v in s["verdicts"]) else "aggregate"

    def n_recheck(s: S):
        before = sum(1 for v in s["verdicts"] if invalid(v))
        vs = recheck(personas, ex.criteria, s["items"], s["verdicts"], draft, llm_for, invalid)
        after = sum(1 for v in vs if invalid(v))
        step("재질의", asked=before, fixed=before - after)
        return {"verdicts": vs, "rechecked": 1}

    def n_aggregate(s: S):
        t = build_fit_table(ex.criteria, s["items"], personas, s["verdicts"], draft)
        step("집계", expected=round(t.expected_total, 1), total=t.total_points)
        return {"table": t}

    def n_remedy(s: S):
        rem = remedy([f for r in s["table"].rows for f in r.findings], s["items"], ex.criteria, draft, llm)
        step("보완 지정", n=len(rem))
        return {"remedies": rem}

    g = StateGraph(S)
    for name, fn in [("rubric", n_rubric), ("prior", n_prior), ("review", n_review), ("recheck", n_recheck),
                     ("aggregate", n_aggregate), ("remedy", n_remedy)]:
        g.add_node(name, fn)
    g.set_entry_point("rubric")
    g.add_edge("rubric", "prior")
    g.add_edge("prior", "review")
    g.add_conditional_edges("review", route, {"recheck": "recheck", "aggregate": "aggregate"})
    g.add_edge("recheck", "aggregate")
    g.add_edge("aggregate", "remedy")
    g.add_edge("remedy", END)
    return g.compile(), trace


def run_graph(ex: Extraction, draft: str, personas, llm, llm_for, on_step=None, items=None, prior_search=None) -> ReviewRun:
    app, trace = build_graph(ex, draft, personas, llm, llm_for, on_step, items, prior_search)
    s = app.invoke({})
    return ReviewRun(ex.requirements, ex.criteria, s["items"], personas, s["verdicts"], s["table"], s["remedies"], trace,
                     s.get("prior", []), s.get("stances", []), s.get("failed", []))
