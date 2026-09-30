"""OpenAlex 공개 학술 검색(무료·키 없음) — https://api.openalex.org"""
from __future__ import annotations

import httpx


def search_works(query: str, n: int = 5, since: int = 2019) -> list[dict]:
    r = httpx.get("https://api.openalex.org/works", timeout=30, params={
        "search": query, "filter": f"from_publication_date:{since}-01-01", "per_page": n,
        "select": "display_name,publication_year,doi,cited_by_count"})
    r.raise_for_status()
    return [{"title": w.get("display_name", ""), "year": w.get("publication_year"), "doi": w.get("doi") or "",
             "cited_by": w.get("cited_by_count", 0)} for w in r.json().get("results", [])]
