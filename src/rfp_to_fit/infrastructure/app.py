"""RFP-to-Fit 화면 — streamlit run src/rfp_to_fit/infrastructure/app.py
한 화면 한 메시지: 「평가위원 모두가 깎는 곳」을 먼저, 근거(쪽·인용)는 펼치면 보인다.
초안 원문은 세션 메모리에서만 처리하고 디스크·로그에 남기지 않는다(SPEC S6)."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st  # noqa: E402

from rfp_to_fit.adapters.documents import load_bytes  # noqa: E402
from rfp_to_fit.application.extract import Extraction, extract_rfp  # noqa: E402
from rfp_to_fit.adapters.graph import run_graph  # noqa: E402
from rfp_to_fit.application.serialize import extraction_from_dict, run_from_dict  # noqa: E402
from rfp_to_fit.domain.model import FindingKind  # noqa: E402
from rfp_to_fit.domain.privacy import mask_pii  # noqa: E402
from rfp_to_fit.infrastructure.wiring import actual_models, make_llms, personas_with_models, prior_search  # noqa: E402

DATA = ROOT / "data"
st.set_page_config(page_title="RFP-to-Fit · 평가위원의 눈으로 빈칸 찾기", page_icon="🔎", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Pretendard', -apple-system, 'Apple SD Gothic Neo', sans-serif; }
.block-container { padding-top: 3.4rem; max-width: 1180px; }
.big { font-size: 56px; font-weight: 800; letter-spacing: -1.5px; line-height: 1.05; color: #191F28; }
.sub { color: #6B7684; font-size: 15px; }
.pill { display:inline-block; padding: 3px 10px; border-radius: 999px; font-size: 13px; font-weight: 700; margin-right: 6px; }
.gap { background:#FFEBEE; color:#D32F2F; } .con { background:#FFF4E5; color:#E65100; }
.ok { background:#E8F5E9; color:#2E7D32; } .unk { background:#ECEFF1; color:#546E7A; }
.card { border: 1px solid #E5E8EB; border-radius: 16px; padding: 16px 18px; margin-bottom: 12px; background: #fff; }
.card h4 { margin: 4px 0 8px 0; font-size: 17px; color:#191F28; }
.muted { color:#8B95A1; font-size: 13px; }
.quote { background:#F2F4F6; border-radius: 8px; padding: 6px 10px; font-size: 13px; color:#333D4B; margin: 4px 0; }
</style>
""", unsafe_allow_html=True)

PILL = {FindingKind.CONSENSUS_GAP: "gap", FindingKind.CONTESTED: "con", FindingKind.MET: "ok", FindingKind.UNVERIFIABLE: "unk"}

EXAMPLES = {
    "nais-hackathon-2026": "2026 NAIS AI 해커톤 공고 (NST·NAIS, 5쪽)",
    "kasa-space-manufacturing-platform-2026": "우주항공청 우주제조 플랫폼 기술개발 공고 (19쪽)",
    "motir-industrial-cluster-rnd-2026": "산업통상부 산업집적지경쟁력강화사업(R&D) 공고 (37쪽)",
}


@st.cache_resource
def llms():
    return make_llms()


def gold_meta(rid: str) -> dict:
    p = DATA / "gold" / f"{rid}.json"
    return json.loads(p.read_text()) if p.exists() else {}


@st.cache_data(show_spinner=False)
def cached_extraction(rid: str) -> dict | None:
    p = DATA / "cache" / f"{rid}.extract.json"
    return json.loads(p.read_text()) if p.exists() else None


@st.cache_data(show_spinner=False, max_entries=20)
def extract_uploaded(digest: str, data: bytes, name: str):
    from rfp_to_fit.application.serialize import extraction_to_dict
    gemini, _ = llms()
    doc = load_bytes(data, name, "upload")
    return extraction_to_dict(extract_rfp(doc, gemini)), len(doc.pages)


def cached_rubric(key, sub):
    if not key:
        return None
    from rfp_to_fit.domain.model import CheckItem
    p = DATA / "cache" / f"{key}.rubric.json"
    return [CheckItem(**i) for i in json.loads(p.read_text())] if p.exists() else None


def accuracy_panel():
    p = DATA / "eval" / "extract-openai.json"
    if not p.exists():
        return
    rows = json.loads(p.read_text())
    st.markdown("**공고 파싱 정확도** — 사람이 쪽마다 읽어 만든 정답표 대비(모델과 독립)")
    cols = st.columns(len(rows))
    for c, r in zip(cols, rows):
        c.metric(EXAMPLES.get(r["id"], r["id"])[:18], f'{r["recall"] * 100:.0f}%', f'지표 일치 {r["criteria_agreement"] * 100:.0f}%')


# ---------------- 머리 ----------------
st.markdown('<div class="sub">팀 루미아 · 2026 NAIS AI 해커톤</div>', unsafe_allow_html=True)
st.markdown("## 평가위원의 눈으로, 제출 전에 빈칸을 먼저.")
st.markdown('<div class="sub">공고의 <b>실제 심사표</b>로 실제 심사위원 유형 6가지(기술 타당성·기술 큰그림·세부 전문·사업성·행정·사업 취지)의 가상 평가위원이 초안을 <b>따로</b> 채점합니다. '
            '모두가 깎는 곳(합의 결핍)과 의견이 갈리는 곳(논쟁 지점)을 나누고, 무엇을 어디에 보완할지 지정합니다. 문장은 대신 쓰지 않습니다.</div>',
            unsafe_allow_html=True)
st.write("")

tab_run, tab_ba, tab_trust = st.tabs(["① 실행", "② 우리 기획서 먼저 채점", "③ 신뢰 장치·정확도"])

# ---------------- ① 실행 ----------------
with tab_run:
    left, right = st.columns(2)
    with left:
        st.markdown("**1. 공고(RFP)**")
        src = st.radio("공고", ["예시 공고", "직접 올리기(PDF·HWPX)"], horizontal=True, label_visibility="collapsed")
        ex_dict, rfp_label, n_pages, rid = None, "", None, None
        if src == "예시 공고":
            rid = st.selectbox("예시", list(EXAMPLES), format_func=lambda k: EXAMPLES[k], label_visibility="collapsed")
            ex_dict = cached_extraction(rid)
            rfp_label = EXAMPLES[rid]
            if ex_dict is None:
                st.info("이 공고는 아직 파싱 캐시가 없습니다. 실행 시 새로 파싱합니다.")
                data = (DATA / "rfp" / f"{rid}.pdf").read_bytes()
                ex_dict, n_pages = extract_uploaded(hashlib.sha256(data).hexdigest(), data, f"{rid}.pdf")
        else:
            up = st.file_uploader("공고 파일", type=["pdf", "hwpx"], label_visibility="collapsed")
            if up:
                data = up.getvalue()
                with st.status("공고를 3쪽씩 나눠 병렬로 읽는 중… (쪽 수에 따라 20초~2분)", expanded=False) as s:
                    ex_dict, n_pages = extract_uploaded(hashlib.sha256(data).hexdigest(), data, up.name)
                    s.update(label=f"공고 파싱 완료 · {n_pages}쪽", state="complete")
                rfp_label = up.name
    with right:
        st.markdown("**2. 연구자 초안**")
        dsrc = st.radio("초안", ["예시: 우리 팀 예선 기획서", "직접 올리기", "붙여넣기"], horizontal=True, label_visibility="collapsed")
        draft = ""
        if dsrc.startswith("예시"):
            labels = {"original": "원본(예선 제출본)", "after": "보완본(본선 구현 결과 추가)",
                      "drop2-ethics": "결함 주입: 윤리·신뢰성 제거", "drop2-comparison": "결함 주입: 차별성 비교 제거",
                      "drop2-plan": "결함 주입: 구현 계획 제거", "drop2-impact": "결함 주입: 기대효과·확장 제거",
                      "drop2-problem": "결함 주입: 문제 정의 제거"}
            variant = st.selectbox("예시 초안", list(labels), format_func=labels.get, label_visibility="collapsed")
            draft = (DATA / "drafts" / "nais-hackathon-2026" / f"{variant}.md").read_text()
        elif dsrc == "직접 올리기":
            dup = st.file_uploader("초안 파일", type=["pdf", "hwpx", "md", "txt"], label_visibility="collapsed")
            if dup:
                draft = load_bytes(dup.getvalue(), dup.name, "draft").text
        else:
            draft = st.text_area("초안 붙여넣기", height=180, label_visibility="collapsed",
                                 placeholder="제안서·기획서 본문을 붙여넣으세요. 저장되지 않습니다.")
        pii = {}
        if draft.strip():
            draft, pii = mask_pii(draft)
        note = " · 개인정보 " + ", ".join(f"{k} {v}건" for k, v in pii.items()) + "을 가린 뒤 AI에 보냅니다." if pii else ""
        st.markdown(f'<div class="muted">🔒 초안은 서버에 저장하지 않고 이 세션 메모리에서만 처리합니다.{note}</div>', unsafe_allow_html=True)

    ex = extraction_from_dict(ex_dict) if ex_dict else None
    stage = None
    if ex:
        stages = sorted({c.stage for c in ex.criteria})
        if len(stages) > 1:
            default = stages.index("본선") if "본선" in stages else 0
            stage = st.radio("어느 심사표로 채점할까요?", stages, index=default, horizontal=True)
        crits = [c for c in ex.criteria if stage is None or c.stage == stage]
        st.markdown(f'<div class="muted">공고에서 찾은 것: 요건 {len(ex.requirements)}개 · 평가지표 {len(crits)}개 ('
                    + " · ".join(f"{c.name} {c.points:g}" for c in crits) + ")</div>", unsafe_allow_html=True)

    rubric_key = f"{rid}.{stage or 'all'}" if (src == "예시 공고" and rid) else None
    go = st.button("평가위원 6명에게 보내기", type="primary", disabled=not (ex and draft.strip()), use_container_width=True)
    if go:
        gemini, solar = llms()
        personas, llm_for = personas_with_models(gemini, solar)
        sub = Extraction(ex.requirements, [c for c in ex.criteria if stage is None or c.stage == stage], ex.dropped)
        t0 = time.time()
        with st.status("에이전트가 일하는 중…", expanded=True) as status:
            st.write("① 공고 심사표 → 점검 질문으로 쪼개기")

            def on_step(name, rec):
                fmt = {"점검 항목": lambda r: f"② 점검 질문 {r.get('n')}개 → 평가위원 6명에게 **따로** 보냄(서로의 답을 모름, 3개 회사 모델)",
                       "선행 탐색": lambda r: f"② 선행 탐색(MCP → OpenAlex) 검색어 {r.get('queries')} → 선행연구 {r.get('n')}편을 평가위원 참고 자료로",
                       "독립 채점": lambda r: f"③ 판정 {r.get('n')}개 수신 · 인용 실재 검사 탈락 {r.get('invalid')}건",
                       "재질의": lambda r: f"↺ 가짜 인용 {r.get('asked')}건을 그 평가위원에게 다시 물음 → 원문 인용으로 충족 {r.get('cited')}건 · 부족/누락으로 정정 {r.get('downgraded')}건 · 여전히 무효 {r.get('still')}건",
                       "집계": lambda r: f"④ 근거 충족도 {r.get('expected')} / {r.get('total')}(최고·최저 제외 평균) → 결핍마다 보완 위치 지정",
                       "보완 지정": lambda r: f"⑤ 보완 지정 {r.get('n')}개 완료"}
                msg = fmt[name](rec) if name in fmt else name
                st.write(msg)

            run = run_graph(sub, draft, personas, gemini, llm_for, on_step=on_step, items=cached_rubric(rubric_key, sub),
                            prior_search=prior_search())
            used = actual_models(personas, llm_for)
            run.trace.append({"step": "실제 판정 모델", **used})
            status.update(label=f"완료 · {time.time() - t0:.0f}초", state="complete", expanded=False)
        st.session_state["run"] = run
        st.session_state["rfp_label"] = rfp_label

    run = st.session_state.get("run")
    if run:
        t = run.table
        gaps, cons = t.findings(FindingKind.CONSENSUS_GAP), t.findings(FindingKind.CONTESTED)
        unk = t.findings(FindingKind.UNVERIFIABLE)
        demoted = sum(f.demoted for r in t.rows for f in r.findings)
        items = {i.id: i for i in run.items}
        crit = {c.id: c for c in run.criteria}
        pname = {p.id: p.name for p in run.personas}
        rem = {r.item_id: r for r in run.remedies}

        st.divider()
        a, b = st.columns([1, 1.4])
        with a:
            st.markdown('<div class="sub">모두가 깎는 곳</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="big">{len(gaps)}곳</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sub">논쟁 지점 {len(cons)} · 확인 불가 {len(unk)} · '
                        f'근거 충족도 <b>{t.expected_total:.1f}</b> / {t.total_points:g} <span class="muted">(점수 예측이 아니라 지표별 근거가 초안에 있는 정도)</span></div>', unsafe_allow_html=True)
            rc = next((x for x in run.trace if x.get("step") == "재질의"), None)
            ind = next((x for x in run.trace if x.get("step") == "독립 채점"), {})
            msg = (f"가짜 인용 {rc['asked']}건 → 그 평가위원에게 재질의" if rc else "가짜 인용 0건") + \
                  f" · 최종 강등 {demoted}건 · 응답 {ind.get('reviewers', len(run.personas))}/{len(run.personas)}명"
            st.markdown(f'<div class="muted">{msg}</div>', unsafe_allow_html=True)
            if run.failed:
                st.warning(f"응답하지 못한 평가위원: {', '.join(pname.get(x, x) for x in run.failed)} — 나머지로 집계했습니다.")
            if run.stances:
                cnt = {d: sum(1 for x in run.stances if x.decision == d) for d in ("선정", "보류", "탈락")}
                st.markdown(f'<div style="margin-top:14px" class="sub">심사위원의 마음(항목 점수와 별개인 전체 인상)</div>'
                            f'<div style="font-size:22px;font-weight:800">선정 {cnt["선정"]} · 보류 {cnt["보류"]} · 탈락 {cnt["탈락"]}</div>',
                            unsafe_allow_html=True)
                for x in run.stances:
                    st.markdown(f'<div class="muted">· <b>{pname.get(x.reviewer_id, x.reviewer_id)}</b> {x.decision} — {x.key_point}</div>',
                                unsafe_allow_html=True)
        with b:
            import pandas as pd
            df = pd.DataFrame({crit[r.criterion.id].name + f" ({r.criterion.points:g})":
                               {pname[k]: round(v, 1) for k, v in r.per_reviewer.items()} for r in t.rows}).T
            df["평균"] = [round(r.expected_points, 1) for r in t.rows]
            st.markdown("**심사기준 대조표** — 지표 × 평가위원(점수)")
            st.dataframe(df, use_container_width=True)

        def finding_card(f):
            it = items[f.item_id]
            c = crit[it.criterion_id]
            votes = " ".join(f"{pname[v.reviewer_id][:6]}:{v.label.value}" for v in f.verdicts)
            html = (f'<div class="card"><span class="pill {PILL[f.kind]}">{f.kind.value}</span>'
                    f'<span class="muted">{c.name} {c.points:g}점 · 공고 p.{c.evidence.page}</span>'
                    f'<h4>{it.question}</h4><div class="muted">{votes}</div>')
            r = rem.get(f.item_id)
            if r:
                html += (f'<div style="margin-top:8px"><b>보완 지정</b> — <b>{r.evidence_type}</b>을(를) '
                         f'<b>「{r.location}」</b>에 · <span class="muted">{r.why}</span></div>')
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
            with st.expander("평가위원 메모·인용 보기"):
                for v in f.verdicts:
                    st.markdown(f"- **{pname[v.reviewer_id]}** ({v.label.value}) {v.reason}")
                    if v.quote:
                        st.markdown(f'<div class="quote">“{v.quote}”</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 고칠 곳 — 합의 결핍")
            for f in gaps or []:
                finding_card(f)
            if not gaps:
                st.success("모두가 깎는 곳은 없습니다.")
        with c2:
            st.markdown("### 판단할 곳 — 논쟁 지점")
            for f in cons or []:
                finding_card(f)
            if not cons:
                st.info("의견이 갈리는 곳이 없습니다.")
        if unk:
            st.markdown("### 확인 불가 — 근거 인용이 원문에 없어 판정을 보류")
            for f in unk:
                finding_card(f)

        if run.prior_art:
            with st.expander(f"선행연구 {len(run.prior_art)}편 — MCP 도구 서버 경유 OpenAlex 검색(혁신성 판정 참고)"):
                for w in run.prior_art:
                    st.markdown(f"- [{w['title']}]({w.get('doi') or '#'}) · {w.get('year')} · 피인용 {w.get('cited_by')} · 검색어 `{w.get('query')}`")
        with st.expander(f"공고 요건 매트릭스 ({len(run.requirements)}개) — 모두 공고 쪽 번호·원문 인용 포함"):
            import pandas as pd
            st.dataframe(pd.DataFrame([{"분류": r.category, "요건": r.text, "쪽": r.evidence.page, "원문 인용": r.evidence.quote}
                                       for r in run.requirements]), use_container_width=True, hide_index=True)
        with st.expander("에이전트 실행 기록·사용 모델"):
            used = next((t for t in run.trace if t.get("step") == "실제 판정 모델"), {})
            st.json({"trace": run.trace, "평가위원": [{"id": p.id, "렌즈": p.name, "실제 모델": used.get(p.id, p.model)}
                                                  for p in run.personas]})

# ---------------- ② 전·후 ----------------
with tab_ba:
    before, after = DATA / "runs" / "nais-hackathon-2026--original.json", DATA / "runs" / "nais-hackathon-2026--after.json"
    st.markdown("### 이 대회의 공고와 본선 심사표로 우리 예선 기획서를 먼저 채점했습니다")
    st.markdown('<div class="sub">심사표: 적합성 10 · 활용성 20 · 혁신성 25 · 실현가능성 25 · 확장성 20 (공고 p.3). '
                '항목 근거는 거의 다 채워져 있었지만, 평가위원 절반이 「보류」였습니다 — 결정 포인트가 우리가 오늘 준비할 것을 알려 줬습니다.</div>',
                unsafe_allow_html=True)
    if before.exists():
        rb = run_from_dict(json.loads(before.read_text()))
        pn = {p.id: p.name for p in rb.personas}
        cnt = {d: sum(1 for x in rb.stances if x.decision == d) for d in ("선정", "보류", "탈락")}
        c1, c2 = st.columns([1, 2])
        c1.markdown('<div class="sub">예선 기획서에 대한 심사위원의 마음</div>'
                    f'<div class="big">선정 {cnt["선정"]} · 보류 {cnt["보류"]}</div>'
                    f'<div class="muted">근거 충족도 {rb.table.expected_total:.1f} / {rb.table.total_points:g} · 합의 결핍 '
                    f'{len(rb.table.findings(FindingKind.CONSENSUS_GAP))} · 논쟁 {len(rb.table.findings(FindingKind.CONTESTED))}</div>',
                    unsafe_allow_html=True)
        with c2:
            for x in sorted(rb.stances, key=lambda x: x.decision != "보류"):
                pill = "con" if x.decision == "보류" else ("gap" if x.decision == "탈락" else "ok")
                st.markdown(f'<div class="card"><span class="pill {pill}">{x.decision}</span><b>{pn.get(x.reviewer_id)}</b>'
                            f'<div style="margin-top:6px">{x.key_point}</div></div>', unsafe_allow_html=True)
        st.markdown("#### 그래서 오늘 목표치 대신 실측치를 가져왔습니다")
        ev = DATA / "eval"
        rows = []
        if (ev / "extract-openai.json").exists():
            for r in json.loads((ev / "extract-openai.json").read_text()):
                rows.append({"측정": f"공고 파싱 — {EXAMPLES.get(r['id'], r['id'])}", "결과": f"요건 재현율 {r['recall'] * 100:.0f}% · 지표 일치 {r['criteria_agreement'] * 100:.0f}% · {r['seconds']:.0f}초"})
        if (ev / "planted.json").exists():
            pl = json.loads((ev / "planted.json").read_text())
            rows.append({"측정": f"결함 주입 실험(지표별 블록 삭제 초안 {pl['n']}개)",
                         "결과": f"탐지 {sum(x['detected'] for x in pl['rows'])}/{pl['n']} · 정밀도 {pl['precision'] * 100:.0f}%"})
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("실행 기록이 아직 없습니다.")

# ---------------- ③ 신뢰 ----------------
with tab_trust:
    st.markdown("### 가짜로 돌아가는 척을 못 하게 설계했습니다")
    st.markdown("""
- **인용 실재 검사(결정론)**: 평가위원이 「충족」이라 하면 초안에서 그대로 복사한 인용을 내야 하고, 코드가 원문과 글자 단위로 대조합니다. 없으면 그 판정은 버립니다(강등).
- **공고 인용 검사**: 요건·지표도 공고 쪽 번호와 원문 인용을 달아야 하고, 그 쪽에 없으면 버립니다.
- **독립 채점 + 모델 다양성**: 평가위원 6명은 서로의 답을 보지 않고, OpenAI · Google Gemini · Upstage Solar(국산) 3개 회사 모델에 2명씩 나눠 한 회사 모델의 치우침이 「합의」로 굳지 않게 합니다. 실제 심사처럼 최고점·최저점을 빼고 평균합니다.
- **문장 미생성**: 보완은 「무엇을·어디에」만 지정합니다. 최종 판단과 작성은 연구자가 합니다.
- **초안 비저장**: 초안은 세션 메모리에서만 처리합니다.
""")
    accuracy_panel()
    p = DATA / "eval" / "planted.json"
    if p.exists():
        d = json.loads(p.read_text())
        st.markdown(f"**결함 주입 실험** — 우리 기획서에서 지표별 블록을 하나씩 지운 초안 {d['n']}개: "
                    f"지운 곳 탐지율 **{d['detect_rate'] * 100:.0f}%** · 정밀도 **{(d.get('precision') or 0) * 100:.0f}%**")
    st.markdown("**사용 모델·라이브러리·데이터 출처**는 저장소 README 표에 모두 적었습니다.")
