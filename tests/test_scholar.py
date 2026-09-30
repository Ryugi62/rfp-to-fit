import httpx

from rfp_to_fit.adapters import openalex


def test_falls_back_to_crossref_when_openalex_fails(monkeypatch):
    def boom(*a, **k):
        raise httpx.HTTPStatusError("503", request=httpx.Request("GET", "https://api.openalex.org"), response=httpx.Response(503))
    monkeypatch.setattr(openalex, "_openalex", boom)
    monkeypatch.setattr(openalex, "_crossref", lambda q, n, s: [{"title": "T", "source": "Crossref"}])
    assert openalex.search_works("q")[0]["source"] == "Crossref"
