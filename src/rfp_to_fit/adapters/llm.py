"""LLM 어댑터 — Gemini(google-genai) · Upstage Solar(OpenAI 호환 HTTP). 둘 다 complete_json 포트를 구현."""
from __future__ import annotations

import json
import os
import re
import time

import httpx

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)


def parse_json(text: str):
    t = _FENCE.sub("", (text or "").strip())
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            return json.loads(m.group(0))
        raise


POOL = ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-3.8-flash",
        "gemini-3.7-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"]


class GeminiLLM:
    """무료 등급은 모델마다 한도가 따로다 → 429·503이면 풀의 다음 모델로 넘긴다. 실제 쓴 모델은 last_model에 남는다."""

    def __init__(self, model: str | None = None, temperature: float = 0.2, pool: list[str] | None = None):
        from google import genai
        self.model = model or os.environ.get("RFP_GEMINI_MODEL", POOL[0])
        self.pool = [self.model] + [m for m in (pool or POOL) if m != self.model]
        self.name = f"Google {self.model}"
        self.temperature = temperature
        self.last_model = None
        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def complete_json(self, system: str, prompt: str):
        from google.genai import types
        cfg = types.GenerateContentConfig(system_instruction=system, temperature=self.temperature,
                                          response_mime_type="application/json")
        last = None
        for model in self.pool:
            for attempt in range(2):
                try:
                    r = self._client.models.generate_content(model=model, contents=prompt, config=cfg)
                    self.last_model = model
                    return parse_json(r.text)
                except Exception as e:
                    last = e
                    msg = str(e)
                    if "429" in msg or "404" in msg or "RESOURCE_EXHAUSTED" in msg:
                        break           # 이 모델 한도 소진 → 다음 모델
                    time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Gemini 호출 실패: {last}")


class FallbackLLM:
    """1차 LLM이 전부 실패하면 2차(다른 회사 모델)로 넘긴다 — 시연 중 한도 소진 대비."""

    def __init__(self, primary, secondary):
        self.primary, self.secondary = primary, secondary
        self.name = primary.name
        self.last_model = None

    def complete_json(self, system: str, prompt: str):
        try:
            out = self.primary.complete_json(system, prompt)
            lm = getattr(self.primary, "last_model", None)
            self.last_model = f"Google {lm}" if lm else self.primary.name
            return out
        except Exception:
            out = self.secondary.complete_json(system, prompt)
            self.last_model = self.secondary.name
            return out


class SolarLLM:
    URL = "https://api.upstage.ai/v1/chat/completions"

    def __init__(self, model: str | None = None, temperature: float = 0.2):
        self.model = model or os.environ.get("RFP_SOLAR_MODEL", "solar-pro3")
        self.name = f"Upstage {self.model}"
        self.temperature = temperature
        self._key = os.environ["UPSTAGE_API_KEY"]

    def complete_json(self, system: str, prompt: str):
        body = {"model": self.model, "temperature": self.temperature,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
        last = None
        for attempt in range(4):
            try:
                r = httpx.post(self.URL, json=body, headers={"Authorization": f"Bearer {self._key}"}, timeout=180)
                r.raise_for_status()
                return parse_json(r.json()["choices"][0]["message"]["content"])
            except Exception as e:
                last = e
                time.sleep(2 * (attempt + 1))
        raise RuntimeError(f"Solar 호출 실패: {last}")
