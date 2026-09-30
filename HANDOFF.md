# HANDOFF — 2026-09-30 17:0x Jarvis(Claude) → Codex·사람 공용
<!-- 템플릿: # HANDOFF — <YYYY-MM-DD HH:MM> <쓴 쪽: 태걸|세훈|Codex|Claude> / 세션 / 브랜치 / 마지막 커밋 / 목표 1개 / 체크리스트 / 다음 1개 / 막힌 것 / 금지 -->
세션 ID: -   브랜치: main(뼈대) → 작업은 day/laptop · night/imac   마지막 커밋: 뼈대 + AGENTS.md·docs/brief
목표 1개(오늘 끝낼 것): 10/1 09:00까지 RFP 1건이 Streamlit 화면에서 요건 매트릭스→대조표→결핍→보완까지 끝까지 돌고, 정답표 대비 정확도 숫자가 화면에 뜬다
체크리스트:
[ ] 0. 17:40 주제 확정(기획서 v2 그대로면 이 줄에 「v2 그대로」)
[ ] 1. 데이터: 공개 RFP 3건 data/rfp/ + 정답표 data/gold/ + README 출처 표
[ ] 2. SPEC.md(성공 조건 재현율≥90%·정밀도≥80%, G/W/T)
[ ] 3. 파서·요건 매트릭스 + scripts/eval.py (3건 중 2건 ≥90%)
[ ] 4. 가상 평가위원 N명 채점 + 결핍 판정(합의/논쟁/확인 불가)
[ ] 5. 보완 지정
[ ] 6. Streamlit 화면 한 장(모델명·정확도 표시) — 실제 실행 확인
[ ] 7. 선행 탐색(MCP 검색기) — 부족하면 링크 목록
[ ] 8. README 실행 3줄 + 출처 표 최종
[ ] 9. 발표자료(권고 3칸) deliver/deck/
[ ] 10. 데모 영상 ≤2분(edge-tts) deliver/demo/
다음 1개: 17:40 이후 → 체크리스트 1(IRIS·NTIS에서 공개 공고 PDF/HWPX 3건 내려받기, 서로 다른 부처)
막힌 것: 없음 · GEMINI_API_KEY 실호출 200 확인(9/30 16:5x, gemini-2.5-flash, 무료 등급 키 — 429 나면 flash-lite로 내리고 README 기재)
금지: 17:00 전 코딩 · 출처 표 누락(실격) · main 직접 커밋 · .env 커밋 · macOS say 음성
