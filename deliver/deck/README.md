# 발표 덱 — RFP-to-Fit (팀 루미아, 본선 10/1 09:30)

## 재빌드 (숫자가 바뀌면 이 한 줄)
```bash
bash deliver/deck/build.sh
# 라이브 주소가 바뀌었으면: LIVE_URL=https://새주소 bash deliver/deck/build.sh
```
- 산출물: `RFP-to-Fit_루미아.pptx` · `RFP-to-Fit_루미아.pdf`(16:9) · `png/slide-01..11.png`
- 끝에 `All validations PASSED!` 와 `자리표시: 없음` 이 나와야 한다. 「측정 중」이 남으면 `data/eval/planted.json`의 `stage`가 `예선`이 아닌 것.
- `STOP:` 이 나오면 data/runs 실행이 비어 있음(점검 질문 0개·응답 0명) — 덱 파일은 덮어쓰지 않는다. 급하면 `RUNS_REF=HEAD bash deliver/deck/build.sh`(커밋된 실행으로 임시 빌드).
- `WARN: ... 응답 k/n` 은 7·9장 각주에 자동 표기된다.

## 숫자는 어디서 오나 (손으로 적은 숫자 0개)
`prepare.py`가 빌드 시점에 읽어 `build/numbers.json`을 만들고, `deck.js`가 그것만 쓴다.

| 장 | 숫자 | 파일 |
|---|---|---|
| 2 | 37쪽 · 요건 58개 · 평가표 3종 | `data/rfp/motir-*.pdf` 쪽수 · `data/gold/motir-*.json` |
| 3·6 | 평가위원 6유형·회사별 모델 수 | `data/runs/nais-hackathon-2026--original.json` `personas` |
| 4 | 요건·심사표·점검 질문 수, 실행 초 | `--original.json` `requirements`·`criteria`·`items`·`trace` |
| 7 | 인용 불일치·재질의 결과 | `--original.json` `trace`(독립 채점 `invalid`, 재질의 `cited`·`downgraded`·`still`) |
| 8 | 요건 재현율·심사표 일치 3건 · 결함 주입 탐지/정밀도 | `data/eval/extract-openai.json`(없으면 extract-gemini.json) · `data/eval/planted.json`(stage=예선일 때만) · `planted-v1*.json`(1차 이력) |
| 9 | 평가위원별 마음속 등수(선정·보류·탈락)·결정 포인트 원문, 실측치 요약 | `--original.json` `stances` · extract-openai · planted |
| 6 | 테스트 수 | `tests/test_*.py`의 `def test_` |
| 11 | 커밋 수·첫 코드 커밋 시각 | `git log`(메시지에 「코드 없음」이 없는 첫 커밋) |

## 화면 캡처 (4장)
- 기본: `deliver/shots/01-input.png`·`02-result.png`를 잘라 쓴다.
- 최신 화면으로 바꾸려면(라이브 앱 실행 1회 = LLM 호출 1회):
  `uv run --no-project --with playwright python deliver/deck/capture.py` → `deliver/deck/shots/`에 저장 → `build.sh` 가 그걸 우선 사용.
- **권장(LLM 호출 0)**: `uv run --no-project --with playwright python deliver/deck/capture_saved.py` — 입력 화면(`shots/input.png`)과 앱 「② 전·후」 탭의 점검 항목 표(`shots/result.png`, 포화된 점수 줄은 제외). data/runs가 바뀌면 이것부터 다시.
- `capture.py`는 라이브 1회 실행 화면(input.png·result.png — 결과는 대조표만). result.png를 덮어쓰니 둘 중 하나만.

## 파일
- `prepare.py` 숫자·이미지·QR 준비 / `deck.js` pptxgenjs 덱(발표 대본은 각 장 노트) / `build.sh` 빌드→PDF→PNG→validate→자리표시 검사 / `capture.py` 화면 캡처
- 스타일: 흰 배경 · 좌상단 파랑 아이브로우 · 2줄 굵은 제목(한 단어만 파랑) · 큰 숫자 ≤3 · 연한 테두리 카드 · Arial. 흐름도(5장)·구성도(6장)는 도형(사람=검정, AI=파랑, 규칙(코드)=점선).
