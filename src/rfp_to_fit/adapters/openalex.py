"""공개 학술 검색 — OpenAlex(무료·키 없음·CC0 메타데이터) 우선, 장애 시 Crossref(무료·키 없음)로 넘긴다.
2026-09-30 22:0x 실측: OpenAlex 503 연속 · Semantic Scholar 키 없이 429 · Crossref 200 → 한 곳에 의존하지 않는다."""
from __future__ import annotations

import httpx


def _openalex(query: str, n: int, since: int) -> list[dict]:
    r = httpx.get("https://api.openalex.org/works", timeout=20, params={
        "search": query, "filter": f"from_publication_date:{since}-01-01", "per_page": n,
        "select": "display_name,publication_year,doi,cited_by_count"})
    r.raise_for_status()
    return [{"title": w.get("display_name", ""), "year": w.get("publication_year"), "doi": w.get("doi") or "",
             "cited_by": w.get("cited_by_count", 0), "source": "OpenAlex"} for w in r.json().get("results", [])]


def _crossref(query: str, n: int, since: int) -> list[dict]:
    r = httpx.get("https://api.crossref.org/works", timeout=20, params={
        "query": query, "rows": n, "filter": f"from-pub-date:{since}-01-01",
        "select": "title,DOI,issued,is-referenced-by-count"})
    r.raise_for_status()
    out = []
    for w in r.json().get("message", {}).get("items", []):
        year = (w.get("issued", {}).get("date-parts") or [[None]])[0][0]
        out.append({"title": (w.get("title") or [""])[0], "year": year,
                    "doi": f"https://doi.org/{w['DOI']}" if w.get("DOI") else "",
                    "cited_by": w.get("is-referenced-by-count", 0), "source": "Crossref"})
    return out


def search_works(query: str, n: int = 5, since: int = 2019) -> list[dict]:
    last = None
    for fn in (_openalex, _crossref):
        try:
            res = fn(query, n, since)
            if res:
                return res
        except httpx.HTTPError as e:
            last = e
    if last:
        raise last
    return []
