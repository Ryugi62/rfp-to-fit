# HANDOFF — 2026-09-30 23:55 Claude(Jarvis, iMac) → Codex·사람 공용
<!-- 템플릿: # HANDOFF — <YYYY-MM-DD HH:MM> <쓴 쪽> / 세션 / 브랜치 / 마지막 커밋 / 목표 1개 / 체크리스트 / 다음 1개 / 막힌 것 / 금지 -->
브랜치: **main에 직접**(현장 심사위원이 main 커밋 과정을 본다 — 9/30 19:14 공지. day/laptop·night/imac은 쓰지 않음)
목표 1개: 10/1 09:00~09:20 제출 = 발표자료(PDF/PPTX) + 프로토타입(라이브 주소·저장소) + 데모 영상, 09:30 발표 5분+질의 3분.

## 상태 (10/1 01:4x)
- 라이브: 고정 주소 https://ryugi62.github.io/rfp-to-fit/ → 터널 https://invisible-sail-shame-preliminary.trycloudflare.com (iMac `streamlit` :8501 + `cloudflared`). 터널이 죽으면 주소가 바뀐다 → 아래 「복구」.
- 발표자료: `deliver/deck/RFP-to-Fit_루미아.pdf`·`.pptx`(발표 11장 + 부록 3장: 12 MCP·13 우리 기획서부터·14 출처, 부록은 질문 때만). 숫자는 data/ JSON과 pytest 수집 결과에서 빌드. 재빌드 `bash deliver/deck/build.sh`.
- 데모 영상: `deliver/demo/RFP-to-Fit_demo.mp4`(95초, 링크 입력 → 채점(실제 71초, 5배속 표기) → 원문 보기 → ✓ 맞음 → 집계).
- 대본·질의응답 14: `deliver/발표-대본-노트.md`(덱 노트에서 추출 + 4장 라이브 동선).
- 스펙·테스트: `SPEC.md`(UC 14·AC 18·UI 수용기준 10) · `uv run pytest` 99개 초록.
- 화면: 공고 파싱 직후 요건 목록·원문 강조·맞음/틀림 · 390/1280 넘침 0(`scripts/responsive.py`, `data/eval/ui-responsive.json`).
- 엔진: 주 엔진 OpenAI gpt-4.1(장애 시 Solar) · 관점 6개 = OpenAI gpt-5.4-mini P1·P4 · Gemini P2·P6(소진 시 gpt-4.1-mini) · Upstage Solar P3·P5. 키는 `.env`(커밋 금지).

## 체크리스트(23:55)
[x] 링크 입력(13/13)·HWP·검증 공고 2건·제거 실험·MCP 외부 연동 실측 [x] 포지셔닝 전환(심사위원 3인 온라인 멘토링) [x] 신뢰도 정의 [x] 현장 검증(원문 보기·✓/✗·사람 확인 정밀도) [x] 보안 모드 [x] README·LICENSE [x] 덱 v4.1(13장·290초) [x] 대본·질의응답 12 [x] 고정 주소 https://ryugi62.github.io/rfp-to-fit/
[x] (OpenAI 크레딧 충전 뒤) 주 엔진 복구 확인 — `source .env; curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"` 200
[x] 4장 화면 캡처를 링크 입력·현장 검증 화면으로 교체 → `bash deliver/deck/build.sh`
[x] 데모 영상 재녹화(95초, 10/1 01:38 현재 화면)(링크 입력 → 보안 모드 없이 실행 → 원문 보기 → ✓) — `scripts/make_demo.py tts` → `scripts/record_demo.py` → `scripts/make_demo.py`(내레이션 LINES 갱신 필요)
[x] 10/1 01시 반응형·SPEC·테스트 98·README 모델 표 정정·대본 재생성
[ ] 07:30 라이브 점검(고정 주소 → 터널 200, 예시 1회) · 08:00 김태걸 리허설 2회(대본 deliver/발표-대본-노트.md)
[ ] 09:00~09:20 제출: deliver/deck/RFP-to-Fit_루미아.pdf(+pptx) · deliver/demo/RFP-to-Fit_demo.mp4 · 저장소 링크 — 방식은 현장 공지

## 다음 1개
07:30 라이브 점검(고정 주소) → 08:00 김태걸 리허설(대본 4장 라이브 전환 포함) → 09:00 제출.

## 복구 (iMac)
```
cd ~/dev/rfp-to-fit
pgrep -fl "streamlit run" || (nohup uv run streamlit run src/rfp_to_fit/infrastructure/app.py --server.port 8501 --server.headless true > /tmp/streamlit.log 2>&1 &)
pgrep -fl cloudflared || (nohup ~/.local/bin/cloudflared tunnel --url http://localhost:8501 --no-autoupdate > /tmp/cf.log 2>&1 &); sleep 8; grep -o "https://[a-z0-9-]*\.trycloudflare\.com" /tmp/cf.log | head -1
# 덱 QR은 고정 주소 https://ryugi62.github.io/rfp-to-fit/ — 터널이 바뀌면 docs/index.html의 주소 2곳만 새 주소로 바꿔 commit·push(덱 재빌드 불필요)
```
노트북 단독 실행(인터넷만 되면): `git clone https://github.com/Ryugi62/rfp-to-fit && cd rfp-to-fit && cp <키 파일> .env && uv sync && uv run streamlit run src/rfp_to_fit/infrastructure/app.py`

## 막힌 것
- Gemini 무료 등급 모델당 20회/일(quotaId GenerateRequestsPerDayPerProjectPerModel-FreeTier) → 평가위원 P2·P6은 대부분 gpt-4.1-mini로 대체 판정됨. 화면 「에이전트 실행 기록·사용 모델」에 실제 모델이 찍힌다(숨기지 않음).
- 근거가 촘촘한 초안은 근거 충족도가 100에 수렴(점수 예측이 아님 — 화면·덱에 명시). 판단 신호는 「심사위원의 마음(선정/보류·결정 포인트)」.

## 금지
main 강제 push · .env 커밋 · macOS say 음성 · 측정 안 한 숫자를 덱/발표에 쓰기 · 경쟁팀 이름 언급 · 심사위원 개인 모델링
