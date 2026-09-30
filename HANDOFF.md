# HANDOFF — 2026-09-30 21:00 Claude(Jarvis, iMac) → Codex·사람 공용
<!-- 템플릿: # HANDOFF — <YYYY-MM-DD HH:MM> <쓴 쪽> / 세션 / 브랜치 / 마지막 커밋 / 목표 1개 / 체크리스트 / 다음 1개 / 막힌 것 / 금지 -->
브랜치: **main에 직접**(현장 심사위원이 main 커밋 과정을 본다 — 9/30 19:14 공지. day/laptop·night/imac은 쓰지 않음)
목표 1개: 10/1 09:00~09:20 제출 = 발표자료(PDF/PPTX) + 프로토타입(라이브 주소·저장소) + 데모 영상, 09:30 발표 5분+질의 3분.

## 상태 (21:00)
- 라이브: https://invisible-sail-shame-preliminary.trycloudflare.com (iMac `streamlit` :8501 + `cloudflared` 퀵 터널, `caffeinate`로 잠자기 막음). 터널이 죽으면 주소가 바뀐다 → 아래 「복구」.
- 발표자료: `deliver/deck/RFP-to-Fit_루미아.pdf`·`.pptx`(11장, 숫자는 data/ JSON에서 빌드, 발표 노트 포함). 재빌드 `bash deliver/deck/build.sh`(주소 바뀌면 `LIVE_URL=https://새주소 bash deliver/deck/build.sh`).
- 데모 영상: `deliver/demo/RFP-to-Fit_demo.mp4`(114초, 실제 앱 녹화 + edge-tts 내레이션).
- 대본·예상 질문 10: `deliver/발표-대본.md`(덱 노트가 최신 — 대본 숫자는 덱 기준으로 읽을 것).
- 측정(정본): 공고 파싱 `data/eval/extract-openai.json`(재현율 90/97/85%, 지표 100%) · 결함 주입 `data/eval/planted.json`(v2 절제, 탐지 4/5·정밀도 100%) · 1·2차 이력 `planted-v1*.json`.
- 엔진: 주 엔진 OpenAI gpt-4.1(장애 시 Solar) · 평가위원 6유형(현장 멘토링 반영) × 3사 모델(OpenAI gpt-5.4-mini 2 · Gemini 2(무료 20회/일, 소진 시 gpt-4.1-mini) · Upstage Solar 2). 키는 `.env`(커밋 금지).
- 테스트 29개 초록(`uv run pytest`).

## 체크리스트
[x] 데이터·정답표 3건 [x] SPEC [x] 파싱+측정 [x] 6인 독립 채점·인용 검사·재질의 [x] 보완 지정 [x] 화면 [x] MCP 선행 탐색(OpenAlex) [x] README 출처 표 [x] 덱 [x] 데모 영상
[ ] 온라인 멘토링 메일(23:00 마감, 초안은 사용자 승인 대기 — Jarvis 채팅)
[ ] 블라인드 심사(독립 3인) — Claude 주간 한도 소진(10/5 재설정)으로 서브에이전트 불가
[ ] 아침 07:30 라이브 점검: 주소 200 + 예시 1회 실행 + 덱 QR 주소 일치
[ ] 제출 방식 확인(현장) → 09:00~09:20 제출

## 다음 1개
아침 점검: `curl -s -o /dev/null -w "%{http_code}" <라이브 주소>` → 200이 아니면 「복구」.

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
