"""실행 결과 ↔ JSON. 초안 원문은 저장하지 않는다(SPEC S6) — 인용은 60자까지만."""
from __future__ import annotations

from dataclasses import asdict

from ..domain.model import (
    CheckItem, Criterion, Evidence, Finding, FindingKind, FitRow, FitTable, RemedyItem, Requirement,
    ReviewerPersona, ReviewerStance, Verdict, VerdictLabel,
)
from .extract import Extraction
from .pipeline import ReviewRun


def extraction_to_dict(ex: Extraction) -> dict:
    return {"requirements": [asdict(r) for r in ex.requirements], "criteria": [asdict(c) for c in ex.criteria],
            "dropped": ex.dropped}


def extraction_from_dict(d: dict) -> Extraction:
    reqs = [Requirement(r["id"], r["category"], r["text"], Evidence(**r["evidence"])) for r in d["requirements"]]
    crits = [Criterion(c["id"], c["name"], c["points"], c["description"], Evidence(**c["evidence"]), c.get("stage", "단일"))
             for c in d["criteria"]]
    return Extraction(reqs, crits, d.get("dropped", []))


def _v(v: Verdict) -> dict:
    return {"reviewer_id": v.reviewer_id, "item_id": v.item_id, "label": v.label.value, "quote": v.quote[:60], "reason": v.reason}


def run_to_dict(run: ReviewRun) -> dict:
    return {
        "requirements": [asdict(r) for r in run.requirements],
        "criteria": [asdict(c) for c in run.criteria],
        "items": [asdict(i) for i in run.items],
        "personas": [asdict(p) for p in run.personas],
        "verdicts": [_v(v) for v in run.verdicts],
        "table": [{"criterion_id": r.criterion.id, "expected_points": r.expected_points, "per_reviewer": r.per_reviewer,
                   "findings": [{"item_id": f.item_id, "kind": f.kind.value, "gap_ratio": f.gap_ratio, "valid": f.valid,
                                 "demoted": f.demoted} for f in r.findings]} for r in run.table.rows],
        "remedies": [asdict(x) for x in run.remedies],
        "trace": run.trace,
        "prior_art": run.prior_art,
        "stances": [asdict(x) for x in run.stances],
        "failed": run.failed,
    }


def run_from_dict(d: dict) -> ReviewRun:
    crits = [Criterion(c["id"], c["name"], c["points"], c["description"], Evidence(**c["evidence"]), c.get("stage", "단일"))
             for c in d["criteria"]]
    by_c = {c.id: c for c in crits}
    items = [CheckItem(**i) for i in d["items"]]
    personas = [ReviewerPersona(**p) for p in d["personas"]]
    verdicts = [Verdict(v["reviewer_id"], v["item_id"], VerdictLabel(v["label"]), v["quote"], v["reason"]) for v in d["verdicts"]]
    rows = []
    for r in d["table"]:
        fs = [Finding(f["item_id"], FindingKind(f["kind"]), f["gap_ratio"], f["valid"], f["demoted"],
                      [v for v in verdicts if v.item_id == f["item_id"]]) for f in r["findings"]]
        rows.append(FitRow(by_c[r["criterion_id"]], r["expected_points"], r["per_reviewer"], fs))
    reqs = [Requirement(r["id"], r["category"], r["text"], Evidence(**r["evidence"])) for r in d["requirements"]]
    return ReviewRun(reqs, crits, items, personas, verdicts, FitTable(rows), [RemedyItem(**x) for x in d["remedies"]], d.get("trace", []),
                     d.get("prior_art", []), [ReviewerStance(**x) for x in d.get("stances", [])], d.get("failed", []))
