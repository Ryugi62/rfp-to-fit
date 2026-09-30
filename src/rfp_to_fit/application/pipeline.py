"""전체 흐름: 파싱 → 점검 항목 → 독립 채점 → 집계 → 보완. 각 단계가 끝날 때 trace 콜백을 부른다."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from ..domain.aggregate import build_fit_table
from ..domain.model import CheckItem, Criterion, FitTable, RemedyItem, Requirement, ReviewerPersona, Verdict
from .extract import Extraction
from .ports import LLM
from .review import build_rubric, remedy, review_all


@dataclass
class ReviewRun:
    requirements: list[Requirement]
    criteria: list[Criterion]
    items: list[CheckItem]
    personas: list[ReviewerPersona]
    verdicts: list[Verdict]
    table: FitTable
    remedies: list[RemedyItem]
    trace: list[dict] = field(default_factory=list)


def run_review(extraction: Extraction, draft: str, personas: list[ReviewerPersona], llm: LLM,
               llm_for: Callable[[ReviewerPersona], LLM], on_step: Callable[[str, dict], None] | None = None,
               items: list[CheckItem] | None = None) -> ReviewRun:
    trace: list[dict] = []

    def step(name: str, **info):
        rec = {"step": name, "t": round(time.time() - t0, 1), **info}
        trace.append(rec)
        if on_step:
            on_step(name, rec)

    t0 = time.time()
    criteria = extraction.criteria
    if items is None:
        guide = "\n".join(f"- {r.text}" for r in extraction.requirements if r.category in ("형식", "제출서류"))[:3000]
        items = build_rubric(criteria, llm, guide)
    step("점검 항목", n=len(items), model=llm.name)
    verdicts = review_all(personas, criteria, items, draft, llm_for)
    step("독립 채점", n=len(verdicts), reviewers=len({v.reviewer_id for v in verdicts}))
    table = build_fit_table(criteria, items, personas, verdicts, draft)
    step("집계", expected=round(table.expected_total, 1), total=table.total_points)
    rem = remedy([f for r in table.rows for f in r.findings], items, criteria, draft, llm)
    step("보완 지정", n=len(rem))
    return ReviewRun(extraction.requirements, criteria, items, personas, verdicts, table, rem, trace)
