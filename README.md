# RFP-to-Fit — 팀 루미아

**2026 NAIS AI 해커톤 본선** (국가과학기술연구회·국가과학AI연구센터, 2026-09-30 17:00 ~ 10-01 12:00, 서울드래곤시티)

> **제출 전에, 빈칸부터.** 공고 링크 하나와 초안 하나를 넣으면, 공고가 요구하는데 초안에 **근거가 없는 곳**을 원문으로 짚는 R&D 에이전트.
> 심사 결과를 예측하지 않고, 문장을 대신 쓰지 않습니다.

- 팀: 김태걸(대표) · 박세훈 · 라이브: https://ryugi62.github.io/rfp-to-fit/ (고정 주소 → 시연용 터널로 이동)
- 규정 준수: 대회 원문 「실제 개발 수행 전 과정이 반드시 본선 대회 기간 내」에 따라, 이 저장소는 **9/30 17:00 전에는 README·인계 파일(HANDOFF·AGENTS·docs/brief 기획 문서)·.gitignore만** 있습니다. 첫 코드 커밋은 9/30 19:19이며 모든 코드는 본선 기간 안에 커밋됐습니다.

## 신뢰도를 이렇게 정의했습니다 (정답이 없는 영역이라 기준을 먼저 세움)
| 주장하지 않는 것 | 정의한 신뢰 기준 |
|---|---|
| 심사 결과·점수를 맞힌다 | **① 추적 가능** — 모든 지적은 공고 원문(쪽·인용)과 초안 원문(인용) 두 끝에 묶인다 |
| 가상 관점 = 실제 심사위원 | **② 날조 없음** — 원문에 없는 인용은 코드가 걸러 판정에서 뺀다(재질의 1회 후에도 없으면 무효) |
| 제안서를 대신 써 준다 | **③ 모르면 넘김** — 관점이 갈리면(20~80%) 「논쟁 지점」으로 사람에게, 근거 있는 판정이 절반 미만이면 「확인 불가」 |
| | **④ 잴 수 있는 것만 숫자로** — 요건 추출(정답표 대비)·지운 근거 탐지(오탐)만 수치로 말한다 |

## 실행
```
cp .env.example .env   # OPENAI_API_KEY, GEMINI_API_KEY, UPSTAGE_API_KEY
uv sync && uv run pytest            # 테스트 34개
uv run streamlit run src/rfp_to_fit/infrastructure/app.py
```
사용: ① 공고 링크 붙여넣기(부처·기관 공지 주소 또는 PDF 주소 — 첨부 중 공고문 자동 선택, HWP·HWPX·PDF) ② 내 초안 올리기 ③ 고칠 곳(모든 관점이 근거 못 찾음)·판단할 곳(갈림)·관점별로 걸리는 점·보완 위치.

## 구조 — LLM은 증인, 판정은 코드 (LangGraph 상태 그래프)
```
[링크] fetch: 공지 HTML → 첨부 점수화(공고문↑ 서식·신청서↓) → 내려받기(스크립트 POST 포함) → 형식 판별(매직 바이트: PDF/HWPX/HWP5)
[파싱] gpt-4.1: 3쪽(구간) 묶음 병렬 → 요건·심사표(쪽·원문 인용) → 규칙: 인용 낱말 85%가 그 쪽에 있어야 채택 · 배점 합 100 초과면 표 분리
[그래프] rubric(gpt-4.1: 지표→점검 질문) → prior(MCP search_prior_art) → review(관점 6개 병렬: OpenAI gpt-5.4-mini 2 · Gemini 2 · Solar 2)
        → check(규칙: 공백·기호 제거 후 연속 문자열 대조) →(무효 있으면) recheck(그 관점에만 1회) → aggregate(규칙) → remedy(gpt-4.1: 근거 종류·위치만)
```
- 규칙(결정론, `src/rfp_to_fit/domain/`): 인용 실재 검사 · 합의(부족·누락 ≥80%)/논쟁(20~80%)/확인 불가(유효 < 절반) · 근거 충족도(충족1·부족0.5·누락0, 최고·최저 제외 평균) · 개인정보 가림(주민번호·전화·이메일·생년월일) · 정답표 대비 측정.
- 관점 6개(현장 멘토링의 실제 심사 경험): 기술 타당성·기술 큰그림·세부 전문·사업성·행정(예산·인력·빈칸)·사업 취지. 특정 심사위원 개인은 흉내 내지 않음.
- 실패 처리: 관점 호출 실패는 순차 재시도 후 「응답 k/6」 표시 · 모델마다 대체 사슬(한도·장애 시 자동 전환, 실제 판정 모델 기록).

## MCP 도구 서버 — 다른 AI 비서도 같은 검사를
- `search_prior_art(query, n)`: OpenAlex 우선, 장애 시 Crossref(9/30 22시 실측: OpenAlex 503 → Crossref 자동 전환)
- `check_quote(quote, text)`: 인용 실재 검사(결정론)
- 연결 예(Codex CLI): `mcp_servers.rfp_to_fit.command="python"`, `args=["-m","rfp_to_fit.infrastructure.mcp_server"]` — 실제 호출 기록 `deliver/mcp-codex-transcript.txt`

## 측정 (정답표 = 파이프라인과 다른 모델이 원문을 읽어 작성, `data/gold/`·`data/holdout/gold/`)
| 무엇 | 결과 | 파일 |
|---|---|---|
| 공고 파싱 — 개발 공고 3건(3회 평균) | 요건 재현율 85%·93%·87%, 심사표 배점 100%, 추출 정밀도 45~84% | `data/eval/extract-openai-3runs.json` |
| 공고 파싱 — **처음 보는 공고 2건**(링크로 수집, 정답표 측정 전 커밋 430ea7d) | 94%·77%(블라인드), 심사표 100% → ※주석 조건 규칙 추가 후 89~95%(따로 표기) | `data/eval/holdout-summary.json` |
| 링크 입력 | 실제 공지 13건 중 13건 공고문 선택·판독(IRIS 상세 미실측) | `data/eval/link-fetch.json` |
| 일부러 지운 근거 탐지(5개) | 6관점 탐지 4/5·오탐 0 | `data/eval/planted.json` |
| 제거 실험 | 관점 1개 오탐 3 → 관점 6개 오탐 0 (3사 섞기 효과는 미확인) | `data/eval/planted-ablation-*.json` |
| 캐시 없는 업로드 E2E | 19쪽 공고 파싱 20초 + 채점 25초(브라우저 실측) | `scripts/e2e_upload.py` |

## 예선 약속 → 본선 구현 (그대로 대조)
| 예선 기획서·포스터 약속 | 본선 | 비고 |
|---|---|---|
| 공고 URL/PDF/HWPX 입력 | ✅ + HWP | 링크 13/13 |
| 요건·평가지표 구조화(출처 쪽) | ✅ | 모든 항목 쪽·원문 인용 |
| 가상 평가위원 독립 채점 → 합의/논쟁/확인 불가 | ✅ | 관점 6개(멘토링 반영) |
| 보완 지정(문장 미생성) | ✅ | |
| 선행 탐색(논문·NTIS 과제·KIPRIS 특허, MCP) | △ 논문만 | 축소 규칙 적용 — NTIS·KIPRIS는 API 키 미확보 |
| RAG(bge-m3+FAISS) | ✗ → 원문 전체 + 인용 대조 | 조각 검색보다 판정 근거 추적이 직접적이라 교체 |
| 요건 재현율 ≥90% | △ 개발 85~93 · 검증 77~94 | 약한 곳 공개 |
| 결핍 탐지 정밀도 ≥80% | ✅ 100%(오탐 0) · 탐지 4/5 | 표본 5 |
| 초안 비저장 | ✅ + 개인정보 가림 | |
| 오픈소스(MIT) | ✅ `LICENSE` | |

## 사용 모델·라이브러리·데이터 출처

| 구분 | 이름 | 버전·출처 | 용도 |
|---|---|---|---|
| 생성형 AI | OpenAI API (gpt-4.1 주 엔진, gpt-5.4-mini 관점 2, gpt-4.1-mini 대체) | REST · platform.openai.com | 공고 파싱·점검 질문·보완·관점 P1·P4 |
| 생성형 AI | Google Gemini API (gemini-3.5-flash 기본, 한도 소진 시 gemini-3-flash-preview·gemini-2.5-flash·gemini-3.8-flash·gemini-3.7-flash·gemini-3.1-flash-lite·gemini-3.5-flash-lite 순) | google-genai 2.25.0 · ai.google.dev | 공고 파싱, 점검 질문, 평가위원 P1·P3·P5, 보완 지정 |
| 생성형 AI | Upstage Solar (solar-pro3) | OpenAI 호환 REST · console.upstage.ai | 평가위원 P2·P4(국산 모델, 모델 다양성), Gemini 장애 시 대체 |
| 에이전트 | LangGraph | 1.2.12 · MIT | 채점→인용 검사→재질의→집계→보완 상태 그래프 |
| 문서 파싱 | pdfplumber | 0.11.10 · MIT | PDF 쪽별 텍스트·표 |
| 문서 파싱 | HWPX 직접 파싱 | Python 표준 zipfile·re | HWPX 본문 |
| 문서 파싱 | olefile | 0.47 · BSD | 구형 한글(HWP 5.0) 본문 |
| 데이터 | Crossref REST API (api.crossref.org, 메타데이터 공개) | | 선행연구 검색 대체 |
| 데이터 | 과기정통부 사업공고 2건(제2026-0940호·0945호, msit.go.kr) | 공개 | 처음 보는 공고 검증·정답표 |
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
