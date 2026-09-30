# RFP-to-Fit — 팀 루미아

**2026 NAIS AI 해커톤 본선** (국가과학기술연구회·국가과학AI연구센터, 2026-09-30 17:00 ~ 10-01 12:00, 서울드래곤시티)

> 평가위원의 눈으로 빈칸을 먼저 찾는 R&D 기획 에이전트.
> 국가 R&D 공고를 넣으면 자격·요건과 평가지표를 구조화하고, 관점이 다른 가상 평가위원 여럿이 연구자 초안을 독립 채점해
> 「어느 지표에서, 왜, 근거가 비는가」를 대조표로 먼저 보여줍니다.

- 팀: 김태걸(대표) · 박세훈
- 규정 준수: 대회 원문 「실제 개발 수행 전 과정이 반드시 본선 대회 기간 내」에 따라, 이 저장소는 **9/30 17:00 전에는 이 README·인계 파일(HANDOFF·AGENTS·docs/brief 기획 문서)·.gitignore만** 있습니다. 모든 코드 커밋은 본선 기간 안에 생깁니다(커밋 시각으로 확인 가능).

## 실행
```
cp .env.example .env   # GEMINI_API_KEY, UPSTAGE_API_KEY 입력
uv sync && uv run pytest
uv run streamlit run src/rfp_to_fit/infrastructure/app.py
```

## 무엇을 하나 (에이전트 흐름 — LangGraph)
```
공고 PDF/HWPX ─▶ ① 3쪽 묶음 병렬 파싱(요건·평가지표, 쪽 번호+원문 인용 필수) ─▶ 공고 인용 검사(없는 인용은 버림)
초안 ─────────▶ ② 평가지표 → 점검 질문 ─▶ 선행 탐색(MCP 도구 서버 → OpenAlex, 관련성 선별) ─▶ ③ 가상 평가위원 5명 독립 채점(Gemini 3 · Solar 2, 서로의 답 모름)
               ─▶ 인용 실재 검사(초안 원문과 글자 대조) ─▶ ↺ 무효 판정만 그 평가위원에게 재질의(1회)
               ─▶ ④ 집계: 합의 결핍(≥80% 감점) / 논쟁 지점 / 충족 / 확인 불가 ─▶ ⑤ 보완 지정(근거 종류·위치만, 문장 미생성)
```
- 도메인 규칙(집계·인용 검사·정확도 측정)은 `src/rfp_to_fit/domain/` — LLM 없이 결정론으로 동작, 테스트 `tests/`.
- 사람이 판단하는 지점: 논쟁 지점의 채택 여부, 보완 문장 작성, 최종 제출.

## 측정 (정답표 = 공고 원문 쪽별 수작업 판독, `data/gold/`, 출처 `data/SOURCES.md`)
- 요건 추출 재현율: `uv run python scripts/eval_extract.py` → `data/eval/extract-gemini.json`

## 사용 모델·라이브러리·데이터 출처

| 구분 | 이름 | 버전·출처 | 용도 |
|---|---|---|---|
| 생성형 AI | Google Gemini API (gemini-3.5-flash 기본, 한도 소진 시 gemini-3-flash-preview·gemini-2.5-flash·gemini-3.8-flash·gemini-3.7-flash·gemini-3.1-flash-lite·gemini-3.5-flash-lite 순) | google-genai 2.25.0 · ai.google.dev | 공고 파싱, 점검 질문, 평가위원 P1·P3·P5, 보완 지정 |
| 생성형 AI | Upstage Solar (solar-pro3) | OpenAI 호환 REST · console.upstage.ai | 평가위원 P2·P4(국산 모델, 모델 다양성), Gemini 장애 시 대체 |
| 에이전트 | LangGraph | 1.2.12 · MIT | 채점→인용 검사→재질의→집계→보완 상태 그래프 |
| 문서 파싱 | pdfplumber | 0.11.10 · MIT | PDF 쪽별 텍스트·표 |
| 문서 파싱 | HWPX 직접 파싱 | Python 표준 zipfile·re | HWPX 본문 |
| 화면 | Streamlit | 1.64.0 · Apache-2.0 | 웹 화면 |
| MCP | Model Context Protocol Python SDK (mcp 2.2.0, MIT) | | 선행 탐색 도구 서버(search_prior_art·check_quote) + 에이전트 쪽 stdio 클라이언트 |
| 데이터 | OpenAlex 공개 학술 API (api.openalex.org, CC0 메타데이터) | | 선행연구 검색 |
| 기타 | httpx 0.28.1(BSD) · pandas 3.0.6(BSD) · python-dotenv 1.2.3(BSD) · pytest(MIT) · Playwright(Apache-2.0, 화면 실측 캡처) | | |
| 배포 | Cloudflare Tunnel (cloudflared 2026.9.3, Apache-2.0) | | 시연용 공개 주소 |
| 데이터 | 2026 NAIS AI 해커톤 모집 공고(NST·NAIS) | nst.re.kr | 예시 공고·정답표 |
| 데이터 | 우주항공청 공고 제2026-0024호 우주제조 플랫폼 기술개발 | 공개 사본(한국항공대 연구처 게시) | 예시 공고·정답표 |
| 데이터 | 산업통상부 공고 제2026-64호 산업집적지경쟁력강화사업(R&D) | 공개 사본(thevc.kr 게시, 원 공고 motir.go.kr) | 예시 공고·정답표 |
| 데이터 | 팀 루미아 예선 기획서(자체 저작물) | `data/drafts/` | 예시 초안·결함 주입 실험 |
| 코딩 AI | Claude (Anthropic, Claude Code) · Codex(OpenAI) | | 코드 작성 보조 |

정답표는 Claude(Anthropic)가 공고 원문을 쪽별로 읽어 작성했고, 파이프라인 모델(Gemini·Solar)과 독립입니다. 연구자 초안은 저장하지 않습니다(세션 메모리만).
