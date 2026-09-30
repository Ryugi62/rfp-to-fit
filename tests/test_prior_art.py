from rfp_to_fit.application.prior_art import as_context, find_prior_art


class KwLLM:
    name = "fake"

    def complete_json(self, s, p):
        if "번호만 골라라" in p:
            return {"keep": [0, 1]}
        return {"queries": ["llm proposal review", "grant evaluation agent"]}


class FakeSearch:
    name = "fake-search"

    def __init__(self):
        self.qs = []

    def search(self, q, n=5):
        self.qs.append(q)
        return [{"title": "A", "year": 2024, "doi": "https://doi.org/10.1/a", "cited_by": 3},
                {"title": "B", "year": 2023, "doi": "https://doi.org/10.1/b", "cited_by": 1}]


def test_prior_art_dedupes_across_queries_and_builds_context():
    s = FakeSearch()
    qs, works = find_prior_art("초안", KwLLM(), s)
    assert s.qs == qs == ["llm proposal review", "grant evaluation agent"]
    assert [w["title"] for w in works] == ["A", "B"]
    ctx = as_context(works)
    assert "10.1/a" in ctx and "OpenAlex" in ctx


def test_empty_context_when_nothing_found():
    assert as_context([]) == ""


def test_filter_drops_irrelevant_titles():
    class Picky(KwLLM):
        def complete_json(self, s, p):
            return {"keep": [1]} if "번호만 골라라" in p else super().complete_json(s, p)
    _, works = find_prior_art("초안", Picky(), FakeSearch())
    assert [w["title"] for w in works] == ["B"]
