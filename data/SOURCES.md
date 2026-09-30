# RFP 데이터 출처 및 정답표(gold) 작성 방법

| id | 제목 | 기관 | 원문 URL | 받은 날짜 | 쪽수 | 요건 수 | 지표 수 | 정답표 작성 방법 |
|---|---|---|---|---|---|---|---|---|
| nais-hackathon-2026 | 2026 국가과학기술연구회 국가과학AI연구센터(NAIS) AI 해커톤 대회 모집 공고 | 국가과학기술연구회 국가과학AI연구센터(NAIS) | https://www.nst.re.kr/www/selectBbsNttView.do?key=54&bbsNo=1&nttNo=51734 (PDF는 공고 신청 폼의 원문 첨부) | 2026-09-04 (팀 보관본 복사 2026-09-30) | 5 | 26 | 10 (예선 5 + 본선 5) | Claude(Anthropic) 원문 페이지별 수작업 판독, 파이프라인(Gemini/Solar)과 독립 |
| kasa-space-manufacturing-platform-2026 | 2026년도 우주소형무인제조플랫폼실증사업(R&D) 신규과제 공고 (우주항공청 공고 제2026-0024호) | 우주항공청 (접수 KISTEP IRIS) | https://research.kau.ac.kr/upfile/2026/03/20260318101946-9198.pdf (원 게시처: kasa.go.kr → 알림 → 사업공고) | 2026-09-30 | 19 | 39 | 4 (단일) | Claude(Anthropic) 원문 페이지별 수작업 판독, 파이프라인(Gemini/Solar)과 독립 |
| motir-industrial-cluster-rnd-2026 | 2026년도 『산업집적지경쟁력강화사업 (R&D)』 신규과제 지원 공고 (산업통상부 공고 제2026-64호) | 산업통상부 / 한국산업단지공단 | https://www.motir.go.kr/kor/article/ATCL2826a2625/70794/view (PDF 사본: grant-documents.thevc.kr, gold JSON source_url 참조) | 2026-09-30 | 37 | 58 | 11 (세부사업 3개 × 3~4) | Claude(Anthropic) 원문 페이지별 수작업 판독, 파이프라인(Gemini/Solar)과 독립 |

## 규약
- `page`는 PDF 물리 쪽번호(1부터). motir는 인쇄 쪽번호 = 물리 - 1.
- requirements = 지키지 않으면 탈락·감점·불이익이 생기는 조항만, 한 요건 = 한 행. `권고` 문구·사후관리(협약 후 보고 등)·법조문 인용 박스는 제외.
- criteria = 평가표 대항목 행 단위. 표별 배점 합 100 검산 완료. 세부사업이 여러 개인 공고는 `track` 필드로 구분.
- NAIS 본선 배점은 공고 PDF 3쪽 심사기준 표에 명시되어 있어 page 3으로 기록(2026-09-30 본선 오프닝 심사 안내 슬라이드의 적합성 10·활용성 20·확장성 20·실현가능성 25·혁신성 25와 일치).
- kasa·motir PDF는 정부 서버 직링크가 아닌 공개 사본(한국항공대 연구처, thevc.kr)에서 받음. motir는 2026-04-08 변경공고(제2026-276호) 미반영 원공고 기준.

## 결함 주입 실험 (drafts/nais-hackathon-2026)
- `original.md` = 팀 루미아 예선 제출 기획서 v2(2026-09-05) 본문, HTML 주석 제거.
- `drop-*.md` 5개 = 본선 지표 5개(적합성·활용성·혁신성·실현가능성·확장성)에 하나씩 대응하는 블록을 삭제한 변형. 정답은 `planted.json`.
