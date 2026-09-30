"""조립 — 어떤 평가위원을 어떤 회사 모델로 돌릴지(모델 다양성 = 독립성).
주 엔진(공고 파싱·점검 질문·보완 지정·검색어) = OpenAI gpt-4.1, 장애 시 Upstage Solar.
평가위원 6명 = 3개 회사 모델 × 2명: OpenAI gpt-5.4-mini(P1·P4) · Google Gemini(P2·P6) · Upstage Solar(P3·P5).
Gemini 무료 등급은 모델당 하루 20회(9/30 실측)라 한도가 떨어지면 OpenAI gpt-4.1-mini로 넘어가고, 실제 판정 모델은 실행 기록에 남는다."""
from __future__ import annotations

import os
from dataclasses import replace

from dotenv import load_dotenv

from ..adapters.llm import FallbackLLM, GeminiLLM, OpenAILLM, SolarLLM
from ..application.personas import DEFAULT_PERSONAS

load_dotenv()

GEMINI_POOL = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash",
               "gemini-3-flash-preview", "gemini-2.5-flash"]
VENDOR = {"P1": "openai", "P2": "gemini", "P3": "solar", "P4": "openai", "P5": "solar", "P6": "gemini"}


def _llm(vendor: str):
    if vendor == "openai":
        return FallbackLLM(OpenAILLM("gpt-5.4-mini"), SolarLLM(temperature=0.0))
    if vendor == "gemini":
        return FallbackLLM(GeminiLLM(model=GEMINI_POOL[0], temperature=0.0, pool=GEMINI_POOL), OpenAILLM("gpt-4.1-mini"))
    return FallbackLLM(SolarLLM(temperature=0.0), OpenAILLM("gpt-4.1-mini"))


def make_llms(secure: bool = False):
    """secure=True(보안 모드): 초안이 닿는 모든 호출을 국산 Upstage Solar로만 — 해외 API로 초안을 보내지 않는다."""
    if secure:
        return SolarLLM(temperature=0.0), None
    return FallbackLLM(OpenAILLM(os.environ.get("RFP_OPENAI_MODEL", "gpt-4.1")), SolarLLM(temperature=0.0)), None


def personas_with_models(main=None, _unused=None, secure: bool = False):
    llms = {p.id: (SolarLLM(temperature=0.0) if secure else _llm(VENDOR[p.id])) for p in DEFAULT_PERSONAS}
    ps = [replace(p, model=llms[p.id].name) for p in DEFAULT_PERSONAS]
    return ps, (lambda p: llms[p.id])


def actual_models(personas, llm_for) -> dict[str, str]:
    return {p.id: (getattr(llm_for(p), "last_model", None) or p.model) for p in personas}


def prior_search():
    from ..adapters.mcp_client import McpPriorArt
    return McpPriorArt()
