# SPEC · RFP-to-Fit

기준 시점: 2026-10-01 제출본 코드(`src/rfp_to_fit/`). 여기 적힌 이름은 모두 코드에 실제로 있고, 수치는 모두 `data/eval/`·`data/runs/` 파일이나 테스트에서 나온다.

## 목적
**제출 전에, 빈칸부터.** 공고(RFP)가 요구하는데 연구자 초안에 근거가 없는 곳을 공고 원문(쪽·인용)과 초안 원문(인용)으로 짚는다. 심사 결과를 예측하지 않는다. 초안에 넣을 문장을 대신 쓰지 않는다. LLM은 증인이다. 공고와 초안에서 인용을 가져오고 의견을 낼 뿐이고, 인용이 원문에 있는지, 판정이 유효한지, 합의인지 논쟁인지는 코드가 정한다.

## 유비쿼터스 언어
말과 코드 이름은 1:1이다. 위치는 `src/rfp_to_fit/` 기준.

| 말 | 코드 | 위치 | 뜻 |
|---|---|---|---|
| 공고 문서 | `Document` | application/ports.py | 쪽 단위 텍스트 목록(`pages`). 쪽이 없는 HWPX·텍스트는 약 3천 자 구간을 쪽으로 쓴다 |
| 출처 | `Evidence` | domain/model.py | 문서 id · 쪽 · 원문 인용 |
| 요건 | `Requirement` | domain/model.py | 신청자가 지켜야 하는 조건. `category`(자격·제출서류·기간·형식·제한·기타), `consequence`(어기면 탈락·감점·불이익·해당없음) |
| 평가지표 | `Criterion` | domain/model.py | 이름·배점·설명·출처. `stage`는 심사 단계나 평가표(예선·본선·과제 유형·`표1`) |
| 파싱 결과 | `Extraction` | application/extract.py | 요건 목록 · 평가지표 목록 · 인용 검사에서 버린 항목(`dropped`) |
| 표 나누기 | `split_tables` | application/extract.py | 한 단계의 배점 합이 100을 넘으면 문서 순서대로 합 100마다 끊어 `·표1`, `·표2`로 나눈다 |
| 점검 항목 | `CheckItem` | domain/model.py | 평가지표 하나를 심사위원이 확인할 질문으로 나눈 것(지표당 최대 3개) |
| 가상 평가위원(관점) | `ReviewerPersona`, `DEFAULT_PERSONAS` | domain/model.py, application/personas.py | 역할 유형 6개: 기술 타당성 검증형 · 기술 큰그림형 · 세부 전문형 · 사업성·시장형 · 행정·관리형 · 사업 취지형 |
| 판정 | `Verdict`, `VerdictLabel` | domain/model.py | 평가위원 1명이 점검 항목 1개에 내린 충족·부족·누락과 초안 인용. 점수 환산 `VALUE`: 1 · 0.5 · 0 |
| 전체 인상 | `ReviewerStance` | domain/model.py | 항목 점수와 별개로 평가위원이 적은 선정·보류·탈락과 당락을 가를 한 가지(`key_point`) |
| 인용 실재 검사 | `verify_quote` | domain/quotes.py | 공백·기호를 뺀 뒤 연속 문자열로 원문에 있는지. 초안 인용은 이것만 쓴다 |
| 느슨한 인용 검사 | `verify_quote_loose` | domain/quotes.py | 표 셀 순서가 섞이는 공고용. 인용의 낱말 85% 이상이 그 쪽에 있으면 통과. 공고 파싱에만 쓴다 |
| 원문 위치 | `locate`, `context` | domain/quotes.py | 인용의 원문 [시작, 끝) 위치와 앞뒤 문맥. 화면의 원문 강조에 쓴다 |
| 유효 라벨 | `effective_label` | domain/aggregate.py | 인용 검사 뒤의 라벨. 가짜·빈 인용의 충족은 무효(None), 가짜 인용의 부족은 누락 |
| 결과 | `Finding`, `FindingKind` | domain/model.py | 점검 항목별 집계: 합의 결핍 · 논쟁 지점 · 충족 · 확인 불가 |
| 합의·논쟁 기준 | `CONSENSUS` = 0.8, `CONTEST` = 0.2 | domain/aggregate.py | 결핍 비율 경계값 |
| 절사 평균 | `trimmed_mean` | domain/aggregate.py | 5명 이상이면 최고점·최저점을 하나씩 빼고 평균 |
| 심사기준 대조표 | `FitTable`, `FitRow` | domain/model.py | 지표 × 평가위원 점수, 지표별 절사 평균(`expected_points`), 편차(`spread`) |
| 보완 지정 | `RemedyItem` | domain/model.py | 근거 종류(`evidence_type`) · 넣을 절(`location`) · 이유(`why`). 문장 필드는 없다 |
| 재질의 | `recheck` | application/review.py | 인용 검사에 걸린 판정만 그 평가위원에게 한 번 더 묻는다 |
| 교차 신문 | `cross_examine` | application/review.py | 유효한 「충족」 인용을 다른 회사 모델이 반대 심문. 사유 코드(무관·부정·빈말)가 있을 때만 코드가 「부족」으로 내린다 |
| 선행 탐색 | `find_prior_art`, `PriorArtSearch`, `as_context` | application/prior_art.py | 초안에서 영문 검색어 2개를 뽑아 검색 포트로 선행연구를 찾고 평가위원 참고 자료로 준다 |
| 선행 탐색 구현 | `McpPriorArt`, `search_works` | adapters/mcp_client.py, adapters/openalex.py | MCP 도구 `search_prior_art` 경유. OpenAlex 우선, 실패하거나 빈 결과면 Crossref |
| 개인정보 가림 | `mask_pii` | domain/privacy.py | 주민번호·전화·이메일·생년월일을 `[종류 가림]`으로 바꾸고 종류별 건수를 돌려준다 |
| 실행 기록 | `ReviewRun`, `run_to_dict`, `run_from_dict` | application/pipeline.py, application/serialize.py | 한 번의 채점 결과. 저장 시 초안 인용은 60자까지만 |
| LLM 포트 | `LLM` | application/ports.py | `complete_json(system, prompt)` 하나. 구현은 adapters/llm.py |
| 첨부 | `Attachment`, `Fetched` | adapters/fetch.py | 공지 페이지에서 찾은 첨부와 점수, 내려받은 공고문 조각(`parts`) |
| 결함 주입 판정 | `new_gaps`, `score_variant`, `RISE` = 0.4 | domain/planted.py | 원본 대비 점검 항목 결핍 비율이 0.4 이상 오른 곳 = 새 결핍 |
| 정확도 지표 | `match_requirements`, `recall`, `criteria_agreement` | domain/metrics.py | 정답표 대비 요건 재현율(같은 쪽 ±1)과 지표 이름·배점 일치율 |

## 유스케이스 (Given / When / Then)
실행 순서(LangGraph, `adapters/graph.py`): 점검 항목 → 선행 탐색 → 독립 채점 → (무효 인용이 있으면) 재질의 1회 → (엄격 모드면) 교차 신문 → 집계 → 보완 지정.

- **UC-1 링크 수집** (`fetch_url`, `find_attachments`, `score_name`, `load_fetched`)
  Given 게시판 공지 페이지 주소 · When 링크를 넣으면 · Then 첨부마다 이름 점수를 매긴다(「공고문」 +5, 「공고」 +3, 서식·양식·신청서·포스터 감점, 같은 점수면 PDF > HWPX > HWP). 최고점에서 0.25 안의 첨부를 받되 같은 이름의 PDF·HWPX가 겹치면 PDF만, 공고문이 (1)(2)로 나뉘면 최대 4개까지 모두 받는다. 받은 내용이 PDF·ZIP·OLE 매직바이트가 아니면(오류 페이지 등) 버린다. 여러 조각은 쪽을 이어 한 문서로 합치고 조각별 쪽 범위를 남긴다. `onclick="fn(번호, 순번)"` 스크립트 다운로드는 POST 요청으로 바꾼다. 파일 직링크면 그대로, 첨부가 없으면 공지 본문을 공고로 쓴다.
- **UC-2 파일 파싱** (`load_bytes`, `sniff`)
  Given 공고 파일 · When 올리면 · Then 확장자가 아니라 내용 앞 바이트로 형식을 정한다. PDF는 쪽 단위 텍스트에 표를 행 단위로 한 번 더 붙이고(`[표]`), HWPX는 section XML의 문단을, HWP 5.0은 OLE `BodyText` 레코드의 문단 텍스트를 읽어 약 3천 자 구간으로 나눈다. HTML·텍스트도 받는다.
- **UC-3 요건·평가지표 추출** (`extract_rfp`)
  Given 공고 문서 · When 파싱하면 · Then 3쪽씩 묶어 병렬로 LLM에 묻고 합친다. 항목마다 LLM이 댄 쪽에서 인용을 찾고, 없으면 ±1쪽, 그래도 없으면 전체 쪽에서 찾아 쪽 번호를 고친다. 어디에도 없으면 `dropped`로 버린다. 요건 문장이 같으면 한 번만 남긴다. 프롬프트에는 ※·* 주석 안의 조건(「~시에만 인정」 등)도 한 요건으로 뽑으라는 규칙이 있다. 평가표가 섞여 배점 합이 100을 넘으면 `split_tables`로 나눈다. 실패한 묶음은 2회 시도 뒤 `FAILURES`에 남긴다.
- **UC-4 점검 질문 생성** (`build_rubric`)
  Given 평가지표 · When 채점을 시작하면 · Then 지표 설명 원문을 요소별로 쪼갠 질문을 지표당 최대 3개 만든다. 공고의 형식·제출서류 요건을 참고로 준다. 질문이 0개면 최대 3회 다시 묻고, 끝내 0개면 예외로 멈춘다.
- **UC-5 선행 탐색** (`find_prior_art`, MCP `search_prior_art`)
  Given 초안 · When 보안 모드가 아니면 · Then 영문 검색어 2개로 MCP 서버를 통해 OpenAlex(2019년 이후)를 찾고, 실패하면 Crossref로 넘긴다. DOI·제목으로 중복을 빼고 제목으로 관련 논문만 남겨 최대 6편을 평가위원에게 「인용 금지 참고 자료」로 준다. 판정 근거로는 쓰지 않는다.
- **UC-6 독립 채점과 전체 인상** (`review_all`, `review_one`)
  Given 점검 항목과 평가위원 6명 · When 채점하면 · Then 평가위원마다 따로 호출한다. 입력은 모두 같고 렌즈(시스템 프롬프트)만 다르며, 다른 평가위원의 답은 입력에 없다. 모르는 라벨은 누락, 없는 항목 id는 버린다. 평가위원마다 전체 인상(선정·보류·탈락 + 한 가지)을 받고, 그 밖의 값은 버린다. 실패한 평가위원은 순차로 한 번 더 부르고, 그래도 실패하면 `failed`에 남겨 화면에 알린다.
- **UC-7 인용 실재 검사와 재질의** (`effective_label`, `recheck`)
  Given 판정 · When 집계 전에 · Then 코드가 초안 인용을 연속 문자열로 대조한다. 인용이 없거나 가짜인 충족은 무효, 가짜 인용의 부족은 누락이 된다. 무효 판정이 있으면 그 평가위원에게 그 항목만 한 번 다시 묻고(다른 평가위원 답은 주지 않음) 새 판정으로 바꾼다. 두 번째 재질의는 없다.
- **UC-8 교차 신문(엄격 모드, 선택)** (`cross_examine`)
  Given 엄격 모드를 켬 · When 재질의 뒤 · Then 평가위원별 유효 「충족」 인용을 다른 회사 모델에게 한 번에 반대 심문한다. 응답이 `supports=false`이고 사유가 무관·부정·빈말 중 하나일 때만 코드가 「부족」으로 내린다. 기본은 끔(AC-17).
- **UC-9 집계** (`aggregate_item`, `build_fit_table`)
  Given 점검 항목 하나의 판정들 · When 집계하면 · Then 유효 판정이 전체의 절반 미만이면 확인 불가. 아니면 유효 판정 중 부족·누락 비율이 0.8 이상이면 합의 결핍, 0.2 초과 0.8 미만이면 논쟁 지점, 0.2 이하면 충족. 대조표는 평가위원별 지표 점수(`VALUE` 평균 × 배점)를 내고, 5명 이상이면 최고·최저를 하나씩 뺀 평균을 지표 점수로 쓴다.
- **UC-10 보완 지정** (`remedy`, `sections_of`)
  Given 합의 결핍·논쟁 지점 · When 집계 뒤 · Then 항목마다 근거 종류와 초안의 절(마크다운 제목·`1)` 번호 제목 목록 중 하나, 없으면 「새 절」)과 이유만 받는다. 대상이 아닌 항목 id는 버리고, 대상이 없으면 LLM을 부르지 않는다. 초안 문장은 만들지 않는다.
- **UC-11 개인정보 가림** (`mask_pii`)
  Given 초안 · When LLM에 보내기 전 · Then 주민번호·전화·이메일·생년월일을 가리고 건수를 화면에 알린다.
- **UC-12 보안 모드** (`make_llms(secure=True)`, `personas_with_models(secure=True)`, `examiners(secure=True)`)
  Given 보안 모드를 켬 · When 채점하면 · Then 초안이 닿는 호출(점검 질문·판정·재질의·교차 신문·보완)은 모두 국산 Upstage Solar로 가고, 해외 학술 DB 선행 탐색은 끈다. 공개 문서인 공고 파싱은 기본 엔진 그대로다.
- **UC-13 현장 검증** (infrastructure/app.py)
  Given 공고 파싱 직후(요건) 또는 결과 화면(지적 카드) · When 사람이 원문 강조를 보고 ✓ 맞음 / ✗ 틀림을 고르면 · Then 지적과 요건 각각 「사람 확인 정밀도」(맞음 / 확인한 수)를 화면에 쌓는다.
- **UC-14 초안 비저장**
  Given 초안 · When 처리하면 · Then 초안 원문은 세션 메모리에서만 쓰고 파일로 쓰지 않는다. 저장되는 실행 기록(`run_to_dict`)에는 초안 인용이 60자까지만 들어간다.

## 수용기준
판정: ○ 충족 · × 미달 · △ 부분 · ? 미검증. 테스트는 `uv run pytest -q`(네트워크·LLM 없음), 실측은 `data/eval/*.json`.

| AC | 기준 | 목표 | 실측 | 판정 | 검사 위치 |
|---|---|---|---|---|---|
| AC-1 | 요건 추출 재현율(정답표 대비, 공고별 3회 평균) | 공고별 ≥90%, 개발 3건 중 2건 이상 | 개발 3건: 우주항공청 85% · 산업통상부 93% · NAIS 87%. 검증 2건(블라인드): 국가과학자 94% · 라이징스타 77% | × (개발 1/3 · 검증 1/2) | `extract-openai-3runs.json`, `extract-openai-holdout-3runs.json`, `holdout-summary.json` · 채점 로직 `tests/test_metrics.py` |
| AC-1b | 주석 규칙 추가 뒤 검증 2건 재현율(블라인드 아님, 2회) | 참고 | 국가과학자 97 · 92% · 라이징스타 89 · 95% | 참고 | `holdout-summary.json` `after_footnote_rule` · 규칙 존재 `tests/test_extract.py::test_footnote_rule_is_in_extraction_prompt` |
| AC-2 | 평가지표 이름·배점 일치 | 100% | 5건 모두 100%(3회 최솟값도 100%) | ○ | 같은 파일 `criteria_agreement` · `tests/test_metrics.py` |
| AC-3 | 공고 인용 검증: 추출 항목은 그 쪽(±1, 또는 교정된 쪽) 원문 대조를 통과, 아니면 버림 | 100% | 테스트 통과. 처음 본 공고 51개 원문 대조: 원문에 없음·왜곡 0 · 신청 단계 요건 44(86%) · 안내·사후 의무 7 · 중복 5 (감사자는 다른 회사 모델, 사람 검수 아님) | ○ | `tests/test_extract.py` · `audit-national-scientist.json` |
| AC-4 | 요건 추출 정밀도 | 목표 없음 | 개발 45 · 54 · 84% · 검증 71 · 73% | 참고 | 위 3runs 파일 `precision` |
| AC-5 | 초안 인용 실재: 인용 검사에 걸린 「충족」은 유효 판정에서 빠짐 | 100% | 테스트 통과. 기준 실행 90판정 중 무효 9 → 재질의 뒤 2, 보완본 22 → 4 | ○ | `tests/test_aggregate.py::test_effective_label_rules`, `tests/test_domain.py::test_hallucinated_met_quote_is_demoted`, `tests/test_recheck.py` · `data/runs/*.json` trace |
| AC-6 | 집계 경계값: 0.8 → 합의 결핍, 0.2 → 충족, 사이 → 논쟁, 유효 = 절반 → 판정, 절반 미만 → 확인 불가 | 전부 | 테스트 통과 | ○ | `tests/test_aggregate.py` |
| AC-7 | 절사 평균: n < 5 절사 없음, n ≥ 5 최고·최저 1개씩(동점 포함) | 전부 | 테스트 통과 | ○ | `tests/test_aggregate.py::test_trimmed_mean_*`, `test_fit_table_trims_outlier_reviewers_with_six_personas` |
| AC-8 | 결함 주입: 지표별 근거 블록을 지운 초안 5개에서 지운 지표를 새 결핍으로 잡음 | 탐지 ≥80% · 정밀도 ≥80% | 탐지 4/5(80%) · 정밀도 7/7(100%). 놓친 1건: 적합성 블록 삭제. n=5, 1회, 예선 심사표 | ○ | `planted.json` · 판정 로직 `tests/test_planted.py` |
| AC-8b | 제거 실험(같은 5개) | 참고 | 평가위원 1명 5/5 · 73% · 6역할 한 회사 모델 5/5 · 100% · 6역할 3사(현재) 4/5 · 100%. n=5 1회라 구성 간 우열 근거로는 약하다 | 참고 | `planted-ablation-single.json`, `planted-ablation-roles-one-model.json`, `planted.json` |
| AC-9 | 링크 수집: 실제 공고 링크에서 공고문을 골라 문서로 읽음 | 전부 | 13/13(공지 페이지 12 · 직링크 1 · 공고문 2개 합치기 1 · `.hwp` 이름의 HWPX 1), 최대 7.5초 | ○ | `link-fetch.json` · `tests/test_fetch.py`, `tests/test_fetch_flow.py` |
| AC-10 | 파일 파싱: PDF 쪽·표, HWPX 구간, 내용 기반 형식 판별 | 전부 | 테스트 통과(실제 공고 PDF 5쪽 · HWPX 2건) | ○ | `tests/test_documents.py`, `tests/test_fetch.py::test_sniff_uses_magic_bytes_not_extension` |
| AC-10b | HWP 5.0 본문 파싱 | 동작 | 샘플 파일 없음, 자동 테스트 없음(형식 판별만 테스트) | ? | `adapters/documents.py::hwp5_paragraphs` |
| AC-11 | 처리 시간(평가위원 6명, 공고 1건 + 초안 1건) | ≤120초 | 채점~보완 23.7초 · 22.0초(선행 탐색·재질의 포함, 점검 질문은 캐시) + 공고 파싱 3회 평균 10.9~23.8초 | ○ | `data/runs/*.json` trace `t` · 3runs 파일 `seconds` |
| AC-12 | 평가위원 6명은 서로 다른 유형, 기본 구성은 3개 회사 × 2명, 교차 신문은 다른 회사 모델 | 전부 | 테스트 통과 | ○ | `tests/test_personas.py`, `tests/test_wiring.py` |
| AC-13 | 독립 채점: 평가위원별 1회 호출, 입력 동일(렌즈만 다름), 실패는 1회 재시도 후 `failed` | 전부 | 테스트 통과 | ○ | `tests/test_review.py` |
| AC-14 | 개인정보 4종을 각각 가리고, 일반 수치·본문 날짜는 그대로 | 오탐 0 | 4종 각각 가림 통과. 10/1 01시 일정 날짜를 생년월일로 가리던 오탐을 테스트로 잡고 고침(생년월일은 「생년월일·출생·생일」 표지 뒤나 「…생」일 때만) | ○ | `tests/test_privacy.py::test_schedule_date_at_line_end_is_not_birthdate`, `test_deadline_date_is_not_birthdate` |
| AC-15 | 보안 모드: 초안이 닿는 LLM 100% Upstage Solar | 100% | 조립 테스트 통과. 선행 탐색 끔은 화면 코드에서 `prior_search=None` | ○ | `tests/test_wiring.py::test_secure_mode_routes_every_draft_call_to_solar` |
| AC-16 | 초안 비저장: 저장 JSON에 초안 원문 없음, 인용 ≤60자, 저장 후 복원이 같음 | 전부 | 테스트 통과 | ○ | `tests/test_serialize.py` |
| AC-17 | 교차 신문 기본 끔의 근거 | 참고 | 켜면 탐지 4/5 동일 · 오탐 0 → 2 · 정밀도 78% | 참고 | `planted-cross.json` |
| AC-18 | 레이어 import 방향 위반 | 0 | 0 | ○ | `tests/test_architecture.py` · 아래 grep |

## UI 수용기준
기준: 토스 디자인 원칙 체크리스트 10(`~/jarvis/notes/원칙-디자인.md`)을 이 화면에 맞게 구체화했다. 실측 도구는 `scripts/responsive.py`(예시 공고+초안을 끝까지 실행한 뒤 같은 화면을 1280·390 폭으로 바꿔 가며 측정, 결과 `data/eval/ui-responsive.json`, 캡처 `deliver/shots/responsive/`), `scripts/e2e_mobile.py`(390×844), `scripts/e2e_verify.py`(1400 폭). 측정 10/1 01시, 로컬과 공개 주소 둘 다.

| # | 항목 | 이 화면의 기준 | 실측 | 판정 |
|---|---|---|---|---|
| U1 | 모바일 퍼스트 | 입력·파싱·결과·전후·신뢰 5화면 × 390·1280에서 가로 넘침 0, 창 밖 요소 0(표는 자기 안에서만 가로 스크롤) | 10/10 화면 넘침 0 · 창 밖 0. 390 폭에서 요건 표 오른쪽 끝 357px | ○ |
| U2 | 한 화면 한 질문 | 입력은 「공고」「초안」 두 묶음, 심사표가 여럿일 때만 셋째 질문 | 묶음 2 + 조건부 1 | ○ |
| U3 | 타이포 위계 | 제목 ≥22px 굵게 · 본문 15~16px · 보조 13px | 제목 26px(모바일)·본문 16px·보조 13px. 13px 미만은 표 도구막대의 글자 없는 아이콘 버튼뿐 | ○ |
| U4 | 여백·라운드 | 카드 라운드 ≥16px, 그림자 없음 | 카드 16px · 모바일 여백 16px | ○ |
| U5 | 하단 고정 CTA | 주 행동 1개(「평가위원 6명에게 보내기」), 전폭, 높이 ≥52px, 아래에 붙음 | 390 폭: 358×52px, 화면 아래 12px 안(sticky, 흰 띠). 결과로 내려가면 따라오지 않음 | ○ |
| U6 | 숫자 먼저 | 결과 첫 요소 = 「모두가 깎는 곳 N곳」 큰 숫자(모바일 40px), 판정 줄은 그 아래 | 캡처 확인 | ○ |
| U7 | 근거는 접힘 | 원문 보기·요건 목록·대조표·실행 기록은 기본 닫힘, 결과 첫 화면에 표 없음 | 4종 모두 expander(닫힘). 대조표도 접음(10/1) | ○ |
| U8 | 마이크로카피 | 존댓말·짧게, 전문용어엔 한 줄 풀이(「근거 충족도(점수 예측이 아니라…)」 등) | 문안 검토 | ○ |
| U9 | 색·대비 | 흰 배경 + 블루 1색(#3182F6) + 상태 3색, 본문 대비 ≥4.5:1, 다크 모드에서 글자가 사라지지 않음 | 보조 글자 #6B7684 = 4.6:1(10/1 #8B95A1 3.0:1에서 교체) · 테마를 light로 고정 | ○ |
| U10 | 성능·의존 | 외부 폰트·CDN 0, 로딩은 진행 단계 표시 | 시스템 폰트 · 진행 로그(①~⑤ 단계를 그대로 보여 줌. 스켈레톤 대신 에이전트가 하는 일을 보이는 쪽을 택함) | ○ |

흐름 실측(10/1): 공개 주소에서 과기정통부 공고 링크 → 파싱 25초(첨부 2개 중 공고문 1개, 요건 62·지표 3) → 채점 21초. 모바일에서 예시 공고 → 요건 목록 → 원문 강조 → ✓ 맞음 → 「요건 1개 확인 → 맞음 1」 집계. 데스크톱 보안 모드 → 지적 카드 원문 보기 → ✓ 맞음 → 「사람 확인 정밀도 100%」.

## 비목표
- 심사 결과·당락·점수 예측. 대조표 점수는 「근거 충족도」이고 예측이 아니다.
- 제안서 문장 생성·자동 작성.
- 실존 심사위원 개인을 흉내 내는 페르소나. 관점은 역할 유형만 쓴다.
- 모델 학습·미세조정.
- 로그인·다중 사용자·초안 보관.

## 구조
```
src/rfp_to_fit/
  domain/          모델·인용 검사·집계·개인정보 가림·정확도 지표. 표준 라이브러리만 쓴다
  application/     유스케이스(파싱·점검 질문·채점·재질의·교차 신문·보완·선행 탐색·직렬화)와 포트(LLM, Document, PriorArtSearch)
  adapters/        LLM 3사 구현, PDF·HWPX·HWP 로더, 링크 수집, OpenAlex·Crossref, MCP 클라이언트, LangGraph 조립
  infrastructure/  Streamlit 화면(app.py), 모델 배치(wiring.py), MCP 서버(mcp_server.py)
```
규칙: `domain` ← `application` ← `adapters` ← `infrastructure`. 안쪽은 바깥을 import하지 않는다.
- domain: 표준 라이브러리와 `rfp_to_fit.domain`만.
- application: 표준 라이브러리, `rfp_to_fit.domain`, `rfp_to_fit.application`만. LLM·검색기는 포트로만 받는다.
- adapters: `rfp_to_fit.infrastructure`를 import하지 않는다. (`McpPriorArt`는 MCP 서버를 별도 프로세스로 띄울 때 모듈 이름 문자열을 쓴다. import가 아니다.)

검사 방법:
1. `uv run pytest -q tests/test_architecture.py`: 각 레이어의 모든 모듈을 `ast`로 읽어(함수 안 지연 import 포함, 상대 import는 절대 이름으로 풀어서) 위 규칙을 검사한다.
2. `grep -rnE "^\s*(from|import) " src/rfp_to_fit/domain src/rfp_to_fit/application | grep -E "adapters|infrastructure|streamlit|google|httpx|langgraph|pdfplumber|mcp|dotenv"`: 결과 0줄.
