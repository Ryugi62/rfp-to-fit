"""보안 모드 조립 — 초안이 닿는 호출이 국산 Upstage Solar로만 가는지(네트워크·실제 키 없음).
wiring은 import 시 .env를 읽으므로 load_dotenv를 막고 가짜 키로 조립만 한다."""
import importlib
import sys

import pytest


@pytest.fixture
def wiring(monkeypatch):
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    for k in ("OPENAI_API_KEY", "UPSTAGE_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.setenv(k, "test-key")
    sys.modules.pop("rfp_to_fit.infrastructure.wiring", None)
    mod = importlib.import_module("rfp_to_fit.infrastructure.wiring")
    yield mod
    sys.modules.pop("rfp_to_fit.infrastructure.wiring", None)


def test_secure_mode_routes_every_draft_call_to_solar(wiring):
    from rfp_to_fit.adapters.llm import SolarLLM
    main, _ = wiring.make_llms(secure=True)
    assert isinstance(main, SolarLLM)
    ps, llm_for = wiring.personas_with_models(secure=True)
    assert len(ps) == 6
    assert all(isinstance(llm_for(p), SolarLLM) and p.model.startswith("Upstage") for p in ps)
    ex = wiring.examiners(secure=True)
    assert all(isinstance(ex(p), SolarLLM) for p in ps)


def test_default_mode_spreads_six_reviewers_over_three_vendors_two_each(wiring):
    from collections import Counter
    assert Counter(wiring.VENDOR.values()) == {"openai": 2, "gemini": 2, "solar": 2}
    ps, llm_for = wiring.personas_with_models()
    assert len({llm_for(p).primary.name.split()[0] for p in ps}) == 3


def test_cross_examiner_is_a_different_vendor_from_the_reviewer(wiring):
    ps, llm_for = wiring.personas_with_models()
    ex = wiring.examiners()
    for p in ps:
        assert ex(p).primary.name.split()[0] != llm_for(p).primary.name.split()[0]
