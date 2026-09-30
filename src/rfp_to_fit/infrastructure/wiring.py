"""조립 — 어떤 평가위원을 어떤 회사 모델로 돌릴지(모델 다양성 = 독립성).
Gemini 무료 등급은 모델당 하루 20회라(9/30 실측 quotaId GenerateRequestsPerDayPerProjectPerModel-FreeTier)
주 엔진(파싱·질문·보완)은 Upstage Solar, Gemini는 평가위원 3명에만 쓰고 한도가 떨어지면 자동으로 Solar로 넘긴다.
실제로 판정한 모델은 실행 기록에 남는다."""
from __future__ import annotations

import os
from dataclasses import replace

from dotenv import load_dotenv

from ..adapters.llm import FallbackLLM, GeminiLLM, SolarLLM
from ..application.personas import DEFAULT_PERSONAS

load_dotenv()

REVIEWER_POOL = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash",
                 "gemini-3-flash-preview", "gemini-2.5-flash"]


def _gemini(pool=None):
    pool = pool or REVIEWER_POOL
    return GeminiLLM(model=pool[0], temperature=0.0, pool=pool)


def make_llms():
    """(주 엔진, 평가위원용 Gemini) — 주 엔진은 RFP_PRIMARY=gemini 로 바꿀 수 있다."""
    solar_main = FallbackLLM(SolarLLM(temperature=0.0), _gemini())
    main = FallbackLLM(_gemini(), SolarLLM(temperature=0.0)) if os.environ.get("RFP_PRIMARY") == "gemini" else solar_main
    return main, None


def personas_with_models(main, _unused=None):
    """P1·P3·P5 = Google Gemini, P2·P4 = Upstage Solar(국산). 평가위원마다 따로 인스턴스(실제 모델 기록용)."""
    llms = {}
    for p in DEFAULT_PERSONAS:
        if p.id in ("P1", "P3", "P5") and os.environ.get("RFP_NO_GEMINI") != "1":
            llms[p.id] = FallbackLLM(_gemini(), SolarLLM(temperature=0.0))
        else:
            llms[p.id] = FallbackLLM(SolarLLM(temperature=0.0), _gemini())
    ps = [replace(p, model=llms[p.id].name) for p in DEFAULT_PERSONAS]
    return ps, (lambda p: llms[p.id])


def actual_models(personas, llm_for) -> dict[str, str]:
    return {p.id: (getattr(llm_for(p), "last_model", None) or p.model) for p in personas}


def prior_search():
    from ..adapters.mcp_client import McpPriorArt
    return McpPriorArt()
