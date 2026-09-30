from rfp_to_fit.domain.planted import new_gaps, score_variant


def test_new_gap_needs_two_of_five_reviewers():
    base = {"a": 0.0, "b": 0.2}
    assert new_gaps(base, {"a": 0.4, "b": 0.4}) == {"a"}


def test_score_variant_counts_hits_in_expected_criterion():
    base = {"i1": 0.0, "i2": 0.0, "i3": 0.2}
    var = {"i1": 1.0, "i2": 0.6, "i3": 0.2}
    crit = {"i1": "활용성", "i2": "혁신성", "i3": "활용성"}
    assert score_variant(base, var, crit, {"활용성"}) == (True, 2, 1)
