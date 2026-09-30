"""조립 — 어떤 평가위원을 어떤 회사 모델로 돌릴지(모델 다양성 = 독립성)."""
from __future__ import annotations

from dataclasses import replace

from dotenv import load_dotenv

from ..adapters.llm import FallbackLLM, GeminiLLM, SolarLLM
from ..application.personas import DEFAULT_PERSONAS

load_dotenv()


def make_llms():
    gemini = FallbackLLM(GeminiLLM(temperature=0.0), SolarLLM(temperature=0.0))
    solar = FallbackLLM(SolarLLM(temperature=0.0), GeminiLLM(temperature=0.0))
    return gemini, solar


def personas_with_models(gemini, solar):
    """P1·P3·P5 = Google Gemini, P2·P4 = Upstage Solar(국산). 한 회사 모델의 치우침이 합의로 굳지 않게."""
    assign = {"P1": gemini, "P2": solar, "P3": gemini, "P4": solar, "P5": gemini}
    ps = [replace(p, model=assign[p.id].name) for p in DEFAULT_PERSONAS]
    return ps, (lambda p: assign[p.id])
