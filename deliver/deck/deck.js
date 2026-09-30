// RFP-to-Fit 본선 발표 덱 — 숫자는 build/numbers.json(prepare.py가 data/ JSON에서 읽음)에서만 가져온다.
// 스타일: 토스풍(흰 배경 · 좌상단 파랑 아이브로우 · 2줄 굵은 제목 한 단어만 파랑 · 큰 숫자 ≤3 · 연한 테두리 카드 · Arial)
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const N = JSON.parse(fs.readFileSync(path.join(__dirname, "build", "numbers.json"), "utf8"));
const OUT = process.argv[2] || path.join(__dirname, "RFP-to-Fit_루미아.pptx");

const C = { ink: "191F28", sub: "4E5968", gray: "8B95A1", blue: "3182F6", blueInk: "1B64DA", blueBg: "EAF3FF",
  bg2: "F4F6F8", line: "E5E8EB", white: "FFFFFF" };
const F = "Arial";
const X0 = 0.9, W = 11.53, R = X0 + W;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.title = "RFP-to-Fit — 팀 루미아";
pres.company = "팀 루미아";

// ---------- helpers ----------
function runs(str, base) { // "**파랑**" 표기 → 텍스트 런
  const out = [];
  str.split("\n").forEach((line, li, arr) => {
    const parts = line.split("**");
    parts.forEach((p, i) => {
      if (!p) return;
      out.push({ text: p, options: Object.assign({}, base, i % 2 ? { color: C.blue } : {}) });
    });
    if (li < arr.length - 1) out.push({ text: "", options: { breakLine: true } });
  });
  // pptxgenjs: breakLine은 앞 런에 붙인다
  const fixed = [];
  out.forEach((r) => { if (r.text === "" && r.options.breakLine) { if (fixed.length) fixed[fixed.length - 1].options.breakLine = true; } else fixed.push(r); });
  return fixed;
}
function t(s, text, o) {
  s.addText(typeof text === "string" ? text : text, Object.assign({ fontFace: F, color: C.ink, margin: 0, valign: "top" }, o));
}
function eyebrow(s, text, y = 0.6) { t(s, text, { x: X0, y, w: 8, h: 0.4, fontSize: 14, bold: true, color: C.blue }); }
function title(s, text, o = {}) {
  t(s, runs(text, { bold: true, color: C.ink }), Object.assign({ x: X0 - 0.03, y: 1.05, w: W, h: 1.5, fontSize: 34, lineSpacingMultiple: 1.12 }, o));
}
function hline(s, y, x = X0, w = W) { s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: C.line, width: 1 } }); }
function src(s, text) { t(s, text, { x: X0, y: 6.95, w: W, h: 0.3, fontSize: 10, color: C.gray }); }
function box(s, x, y, w, h, o = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, Object.assign({ x, y, w, h, rectRadius: 0.08,
    fill: { color: o.fill || C.white }, line: { color: o.lineColor || C.line, width: o.lineWidth || 1, dashType: o.dash || "solid" } }, {}));
}
function arrow(s, x1, y1, x2, y2, color = C.gray) {
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: x2 < x1, flipV: y2 < y1, line: { color, width: 1.25, endArrowType: "triangle" } });
}
function numRow(s, n, head, desc, x, y, w, o = {}) {
  t(s, n, { x, y: y + 0.02, w: 0.6, h: 0.4, fontSize: o.nSize || 18, bold: true, color: C.blue });
  t(s, head, { x: x + 0.7, y, w: w - 0.7, h: 0.42, fontSize: o.hSize || 17, bold: true });
  if (desc) t(s, desc, { x: x + 0.7, y: y + 0.45, w: w - 0.7, h: 0.4, fontSize: o.dSize || 12.5, color: C.gray });
}
function bigNum(s, num, label, x, y, w, o = {}) {
  t(s, num, { x, y, w, h: 0.95, fontSize: o.size || 48, bold: true, color: o.color || C.ink });
  t(s, label, { x, y: y + (o.gap || 1.05), w, h: 0.75, fontSize: o.lSize || 13, color: C.gray, lineSpacingMultiple: 1.15 });
}
const B = N.before, A = N.after, P = N.planted;
const f1 = (x) => Number(x).toFixed(1);
const partial = (r) => (r.reviewers < r.of ? ` · 이번 실행 응답 ${r.reviewers}/${r.of}(실패 ${r.failed.join("·") || r.of - r.reviewers + "명"} — 기록에 남김)` : "");
const fp = (x) => (Number.isInteger(Number(x)) ? String(x) : Number(x).toFixed(1));
const NP = B.personas.length;
const KN = { 3: "세", 4: "네", 5: "다섯", 6: "여섯", 7: "일곱" }[NP] || String(NP);
const GAPK = Math.ceil(0.8 * NP - 1e-9), CLO = Math.floor(0.2 * NP) + 1, CHI = GAPK - 1;
const vcount = {}; B.personas.forEach((q) => { vcount[q.vendor] = (vcount[q.vendor] || 0) + 1; });
const VENDORS = Object.keys(vcount);
const vlabel = (v) => (v === "Upstage Solar" ? "국산 Upstage Solar" : v);
const VTXT = VENDORS.map((v) => `${vlabel(v)} ${vcount[v]}명`).join(" · ");

// ---------- 1. 표지 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "2026 NAIS AI 해커톤 본선 · 팀 루미아", 1.15);
  title(s, "평가위원의 눈으로,\n제출 전에 **빈칸**을 먼저.", { y: 1.8, h: 2.5, fontSize: 56 });
  t(s, `RFP-to-Fit — 국가 R&D 공고를 넣으면, 가상 평가위원 ${NP}명이 초안을 먼저 채점합니다`, { x: X0, y: 4.55, w: W, h: 0.5, fontSize: 19, color: C.sub });
  t(s, "김태걸 · 박세훈", { x: X0, y: 6.4, w: 5, h: 0.45, fontSize: 16, bold: true });
  s.addNotes("[10초] 안녕하세요, 팀 루미아입니다. 저희는 제안서를 대신 쓰는 AI가 아니라, 제출 전에 평가위원의 눈으로 먼저 읽어 주는 에이전트를 만들었습니다.");
}

// ---------- 2. 문제 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "문제");
  title(s, "심사 기준은 공고에 다 있는데,\n그 눈으로 **내 초안**을 읽어 줄 사람은 없습니다");
  const M = N.motir;
  bigNum(s, `${M.pages}쪽`, "산업통상부 R&D 공고 한 건의 분량", X0, 3.35, 3.6);
  bigNum(s, `${M.n_req}개`, "지키지 않으면 탈락·감점되는 요건", X0 + 4.1, 3.35, 3.6);
  bigNum(s, `${M.tables}종`, "세부사업마다 따로 있는 평가표", X0 + 8.2, 3.35, 3.3, { color: C.blue });
  hline(s, 5.55);
  t(s, "연구자는 연구의 언어로 쓰고, 평가위원은 지표의 언어로 읽습니다. 그 사이의 빈칸은 심사평을 받은 뒤에야 보입니다.",
    { x: X0, y: 5.85, w: W, h: 0.5, fontSize: 16, bold: true });
  src(s, "산업통상부 공고 제2026-64호 — 요건·평가표 정답표(data/gold, 저장소 공개) · 정답표는 파이프라인과 다른 모델(Claude)로 쪽마다 판독");
  s.addNotes("[30초] 여기 계신 분들 모두 제안서를 쓰고, 또 심사하시는 분들입니다. 심사 기준은 공고에 이미 다 적혀 있습니다. 산업통상부 공고 한 건을 쪽마다 읽어 보니 37쪽에 지켜야 할 요건이 58개, 평가표가 3종이었습니다. 그런데 제출 전에 그 기준의 눈으로 내 초안을 읽어 줄 사람은 없습니다. 연구자는 연구의 언어로 쓰고 평가위원은 지표의 언어로 읽기 때문에, 그 사이의 빈칸은 심사평을 받은 뒤에야 보입니다. 저희가 푼 문제는 이 하나입니다.");
}

// ---------- 3. 핵심 아이디어 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "핵심 아이디어 — 현장 멘토링(국가 R&D 심사 경험) 반영", 0.6);
  title(s, `한 명의 점수는 취향,\n**${KN} 명**이 따로 보면 갈립니다`);
  const rh = 0.54;
  B.personas.forEach((q, i) => {
    const y = 2.85 + i * rh;
    t(s, String(i + 1).padStart(2, "0"), { x: X0, y, w: 0.6, h: 0.36, fontSize: 15, bold: true, color: C.blue });
    t(s, q.name, { x: X0 + 0.65, y, w: 3.4, h: 0.36, fontSize: 15, bold: true });
    t(s, vlabel(q.vendor), { x: X0 + 4.0, y: y + 0.03, w: 2.4, h: 0.36, fontSize: 12, color: C.gray });
    if (i < NP - 1) hline(s, y + 0.45, X0, 6.35);
  });
  const cx = 7.85, cw = R - cx;
  [["합의 결핍 — 다 같이 깎은 곳", `${NP}명 중 ${GAPK}명 이상이 깎음`, "반드시 고칠 곳"], ["논쟁 지점 — 의견이 갈린 곳", `${NP}명 중 ${CLO}~${CHI}명이 깎음`, "연구자가 판단할 곳"]].forEach(([k, a, b], i) => {
    const y = 2.85 + i * 1.35;
    box(s, cx, y, cw, 1.2, { fill: i ? C.white : C.bg2 });
    t(s, k, { x: cx + 0.3, y: y + 0.16, w: cw - 0.6, h: 0.32, fontSize: 12.5, bold: true, color: C.blue });
    t(s, a, { x: cx + 0.3, y: y + 0.46, w: cw - 0.6, h: 0.36, fontSize: 16, bold: true });
    t(s, "→ " + b, { x: cx + 0.3, y: y + 0.83, w: cw - 0.6, h: 0.3, fontSize: 12, color: C.sub });
  });
  t(s, "각자 「마음속 등수」(선정·보류·탈락)와 당락 포인트 1개도 냅니다 · 근거 충족도는 실제 심사처럼 최고·최저 제외 평균",
    { x: cx, y: 5.6, w: cw, h: 0.6, fontSize: 12, color: C.sub, lineSpacingMultiple: 1.2 });
  t(s, [{ text: "대필·첨삭이 아니라 심사입니다.", options: { bold: true, color: C.ink, breakLine: true } },
    { text: `과거 심사 기록 없이 이번 공고 심사표에서 질문을 만들고 · 평가위원 ${VTXT} · 칭찬에도 원문 인용`, options: {} }],
    { x: X0, y: 6.3, w: W, h: 0.75, fontSize: 13, color: C.sub, lineSpacingMultiple: 1.25 });
  s.addNotes(`[30초] 평가위원 한 명의 점수는 취향입니다. 그래서 오늘 현장 멘토링에서 들은 실제 심사위원 유형 ${NP}가지로 가상 평가위원을 만들어, 서로의 답을 모른 채 채점합니다. ${GAPK}명 이상이 깎으면 반드시 고칠 곳, 의견이 갈리면 연구자가 판단할 곳입니다. 심사위원은 항목 합산보다 몇 가지 결정 포인트로 마음속 등수를 먼저 정한다고 해서, 각자 선정·보류·탈락과 당락 포인트도 냅니다. 모델은 ${VENDORS.length}개 회사로 나눠 한 회사 모델의 치우침이 합의로 굳지 않게 했습니다.`);
}

// ---------- 4. 데모 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "데모 — 이 대회 공고로");
  title(s, `초안 한 편을 넣으면,\n**${B.seconds}초** 뒤 고칠 곳이 나옵니다`);
  const lw = 4.7;
  const mo = N.extract.find((e) => e.pages === N.motir.pages) || N.extract[0];
  const na = N.extract.find((e) => /nais/.test(e.id)) || mo;
  numRow(s, "01", `요건 ${B.n_req}개 · 심사표 ${B.n_crit}개 자동 추출`, `파싱은 처음 한 번(${na.pages}쪽 ${Math.round(na.seconds)}초·${mo.pages}쪽 ${Math.round(mo.seconds)}초) · 시연은 저장본`, X0, 2.95, lw, { hSize: 16 });
  numRow(s, "02", `점검 질문 ${B.n_items}개를 ${NP}명에게 따로`, "서로의 답을 모른 채 판정 + 인용 + 마음속 등수", X0, 4.05, lw, { hSize: 16 });
  numRow(s, "03", "고칠 곳과 판단할 곳을 나눠 표시", "보완은 문장 대신 「무엇을·어디에」만 지정", X0, 5.15, lw, { hSize: 16 });
  const ix = 6.05, iw = R - ix;
  const put = (img, y, maxH) => {
    let w = iw, h = iw * img.h / img.w; if (h > maxH) { h = maxH; w = h * img.w / img.h; }
    box(s, ix, y, w, h + 0.2);
    s.addImage({ path: img.path, x: ix + 0.1, y: y + 0.1, w: w - 0.2, h: h * (w - 0.2) / w });
    return y + h + 0.2;
  };
  let y = 2.95;
  if (N.img.input) y = put(N.img.input, y, 1.75) + 0.2;
  if (N.img.result) put(N.img.result, y, 6.8 - y - 0.2);
  src(s, "라이브 앱 실제 화면(Streamlit) — 시연 공고는 저장된 파싱 결과(8장 재현율은 별도 측정 실행) · 마지막 장 주소에서 직접 눌러 볼 수 있습니다");
  s.addNotes(`[60초] 지금 보시는 건 이 대회 공고입니다. 공고에서 요건 ${B.n_req}개와 본선 심사표 ${B.n_crit}개를 스스로 찾아냈고, 저희 예선 기획서를 넣었습니다. 점검 질문 ${B.n_items}개가 ${KN} 명에게 따로 가고, 약 ${B.seconds}초 뒤 모두가 깎는 곳과 의견이 갈리는 곳이 나옵니다. 보완은 문장을 써 주지 않고 '어떤 근거를, 어느 절에'만 지정합니다.`);
}

// ---------- 5. 서비스 흐름도 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "서비스 흐름도 — AI 개입과 사람 판단 지점");
  title(s, "사람은 **판단**만 하고,\n나머지는 AI와 규칙이 나눕니다");
  const K = {
    H: { tag: "사람", fill: C.ink, line: C.ink, color: C.white, tagColor: "B0B8C1" },
    A: { tag: "AI", fill: C.blueBg, line: C.blue, color: C.blueInk, tagColor: C.blue },
    M: { tag: "AI + MCP", fill: C.blueBg, line: C.blue, color: C.blueInk, tagColor: C.blue },
    R: { tag: "규칙(코드)", fill: C.white, line: C.gray, color: C.ink, tagColor: C.gray, dash: "dash" },
  };
  const steps = [["H", "공고·초안 올리기"], ["A", "3쪽씩 병렬 파싱"], ["R", "공고 인용 검사"], ["A", "점검 질문 생성"], ["M", "선행연구 탐색"], ["A", `${NP}명 독립 채점`],
    ["R", "인용 실재 검사"], ["A", "무효 판정만 재질의"], ["R", "합의·논쟁 집계"], ["A", "보완 위치 지정"], ["H", "논쟁 지점 판단 문장·제출"]];
  const bw = 1.6, gap = (W - 6 * bw) / 5, bh = 1.05, y1 = 2.85, y2 = 4.5;
  const colX = (c) => X0 + c * (bw + gap);
  const pos = steps.map((_, i) => (i < 6 ? { x: colX(i), y: y1 } : { x: colX(11 - i), y: y2 }));
  steps.forEach(([k, label], i) => {
    const st = K[k], p = pos[i];
    box(s, p.x, p.y, bw, bh, { fill: st.fill, lineColor: st.line, dash: st.dash, lineWidth: 1.25 });
    t(s, st.tag, { x: p.x + 0.14, y: p.y + 0.12, w: bw - 0.28, h: 0.25, fontSize: 10, bold: true, color: st.tagColor });
    t(s, label, { x: p.x + 0.14, y: p.y + 0.38, w: bw - 0.28, h: 0.6, fontSize: 13, bold: true, color: st.color, lineSpacingMultiple: 1.05 });
  });
  for (let i = 0; i < 5; i++) arrow(s, colX(i) + bw + 0.04, y1 + bh / 2, colX(i + 1) - 0.04, y1 + bh / 2);
  arrow(s, colX(5) + bw / 2, y1 + bh + 0.04, colX(5) + bw / 2, y2 - 0.04);
  for (let c = 5; c > 1; c--) arrow(s, colX(c) - 0.04, y2 + bh / 2, colX(c - 1) + bw + 0.04, y2 + bh / 2);
  // 범례 — 비어 있는 왼쪽 아래 칸
  [["H", "사람이 판단"], ["A", "AI(LLM)가 생성"], ["R", "규칙(코드)이 검사"]].forEach(([k, label], i) => {
    const st = K[k], y = y2 + 0.05 + i * 0.36;
    box(s, X0, y + 0.03, 0.26, 0.22, { fill: st.fill, lineColor: st.line, dash: st.dash });
    t(s, label, { x: X0 + 0.38, y, w: 1.4, h: 0.3, fontSize: 11.5, color: C.sub });
  });
  hline(s, 5.95);
  t(s, "AI가 말한 것은 규칙이 검사하고, 최종 판단과 문장은 사람이 합니다.", { x: X0, y: 6.15, w: W, h: 0.4, fontSize: 16, bold: true });
  t(s, "AI 6단계 · 규칙 3단계 · 사람 2단계 — 재질의는 인용이 원문에 없는 판정에만, 평가위원당 한 번", { x: X0, y: 6.58, w: W, h: 0.3, fontSize: 12, color: C.gray });
  s.addNotes("[20초] 검은 칸이 사람, 파란 칸이 AI, 점선 칸이 코드 규칙입니다. 사람은 처음에 올리고, 마지막에 논쟁 지점을 판단하고 문장을 씁니다. AI가 말한 것은 매번 규칙이 검사합니다.");
}

// ---------- 6. AI 구성·데이터 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "AI 구성 · 데이터");
  title(s, `${{ 1: "한", 2: "두", 3: "세", 4: "네" }[VENDORS.length]} 회사 모델, 그래프 하나,\n바꿔 끼우는 **MCP** 도구`);
  const chip = (s, x, y, w, label, kind) => {
    const rule = kind === "R";
    box(s, x, y, w, 0.62, { fill: rule ? C.white : C.blueBg, lineColor: rule ? C.gray : C.blue, dash: rule ? "dash" : "solid" });
    t(s, label, { x: x + 0.05, y: y + 0.08, w: w - 0.1, h: 0.46, fontSize: 12, bold: true, color: rule ? C.ink : C.blueInk, align: "center", valign: "middle" });
  };
  // 입력
  [["공고 PDF · HWPX", "쪽 번호·원문 인용 유지"], ["연구자 초안", "서버 비저장 · 세션 메모리"]].forEach(([a, b], i) => {
    const y = 2.85 + i * 1.1;
    box(s, X0, y, 2.25, 0.9);
    t(s, a, { x: X0 + 0.18, y: y + 0.14, w: 1.95, h: 0.32, fontSize: 13.5, bold: true });
    t(s, b, { x: X0 + 0.18, y: y + 0.5, w: 1.95, h: 0.3, fontSize: 10.5, color: C.gray });
  });
  // LangGraph 컨테이너
  const gx = 3.55, gw = 5.75, gy = 2.7, gh = 2.4;
  box(s, gx, gy, gw, gh, { fill: "F9FAFB" });
  t(s, "LangGraph 상태 그래프 — 원문을 통째로 넣고 인용으로 대조(RAG 대신)", { x: gx + 0.2, y: gy + 0.14, w: gw - 0.4, h: 0.3, fontSize: 11, bold: true, color: C.sub });
  arrow(s, X0 + 2.3, 3.9, gx - 0.05, 3.9);
  const r1 = [["점검 질문", "A"], ["선행 탐색", "A"], [`${NP}명 독립 채점`, "A"]];
  const w1 = 1.55, g1 = (gw - 0.4 - 3 * w1) / 2;
  r1.forEach(([l, k], i) => { chip(s, gx + 0.2 + i * (w1 + g1), gy + 0.55, w1, l, k); if (i < 2) arrow(s, gx + 0.2 + i * (w1 + g1) + w1 + 0.03, gy + 0.86, gx + 0.2 + (i + 1) * (w1 + g1) - 0.03, gy + 0.86); });
  const r2 = [["인용 실재 검사", "R"], ["재질의(1회)", "A"], ["합의·논쟁 집계", "R"], ["보완 지정", "A"]];
  const w2 = 1.2, g2 = (gw - 0.4 - 4 * w2) / 3;
  const c2x = (i) => gx + gw - 0.2 - w2 - i * (w2 + g2); // 오른쪽 → 왼쪽(뱀 모양)
  r2.forEach(([l, k], i) => { chip(s, c2x(i), gy + 1.55, w2, l, k); if (i < 3) arrow(s, c2x(i) - 0.02, gy + 1.86, c2x(i + 1) + w2 + 0.02, gy + 1.86); });
  arrow(s, gx + gw - 0.2 - 0.6, gy + 1.19, gx + gw - 0.2 - 0.6, gy + 1.53);
  // LLM
  const mdl = (v) => [...new Set(B.personas.filter((q) => q.vendor === v).map((q) => q.model.split(" ").pop()))].join("·");
  const eng = N.extract[0].engine;
  const vbox = {
    "OpenAI": ["OpenAI", `주 엔진 ${eng}${vcount["OpenAI"] ? `\n평가위원 ${vcount["OpenAI"]}명 ${mdl("OpenAI")}` : ""}`],
    "Google Gemini": ["Google Gemini", `평가위원 ${vcount["Google Gemini"] || 0}명\n한도 소진 시 gpt-4.1-mini`],
    "Upstage Solar": ["Upstage Solar", `국산 · 평가위원 ${vcount["Upstage Solar"] || 0}명\n주 엔진 장애 시 대체`],
  };
  const order = ["OpenAI", "Google Gemini", "Upstage Solar"].filter((v) => vcount[v] || v === "OpenAI");
  const bw3 = (gw - 0.15 * (order.length - 1)) / order.length;
  order.forEach((v, i) => {
    const [a, b] = vbox[v]; const x = gx + i * (bw3 + 0.15), y = 5.25;
    box(s, x, y, bw3, 1.0, { fill: C.blueBg, lineColor: C.blue });
    t(s, a, { x: x + 0.14, y: y + 0.1, w: bw3 - 0.22, h: 0.3, fontSize: 12.5, bold: true, color: C.blueInk });
    t(s, b, { x: x + 0.14, y: y + 0.44, w: bw3 - 0.22, h: 0.5, fontSize: 9.5, color: C.sub, lineSpacingMultiple: 1.1 });
  });
  // MCP
  const mx = 9.7, mw = R - mx;
  box(s, mx, 2.7, mw, 1.25, { lineColor: C.blue });
  t(s, "MCP 도구 서버", { x: mx + 0.18, y: 2.84, w: mw - 0.3, h: 0.32, fontSize: 13.5, bold: true, color: C.blueInk });
  t(s, "AI 도구 연결 표준\nsearch_prior_art · check_quote\n다른 AI 비서도 같은 도구 호출", { x: mx + 0.18, y: 3.17, w: mw - 0.3, h: 0.75, fontSize: 10.5, color: C.sub, lineSpacingMultiple: 1.1 });
  arrow(s, gx + gw + 0.03, 3.3, mx - 0.03, 3.3, C.blue);
  box(s, mx, 4.25, mw, 0.85);
  t(s, "OpenAlex", { x: mx + 0.18, y: 4.37, w: mw - 0.3, h: 0.32, fontSize: 13.5, bold: true });
  t(s, "선행연구 → 혁신성 판정 참고", { x: mx + 0.18, y: 4.72, w: mw - 0.3, h: 0.3, fontSize: 10.5, color: C.gray });
  arrow(s, mx + mw / 2, 3.98, mx + mw / 2, 4.22);
  box(s, mx, 5.3, mw, 0.85, { fill: C.bg2, lineColor: C.bg2 });
  t(s, "출력", { x: mx + 0.18, y: 5.42, w: mw - 0.3, h: 0.32, fontSize: 13.5, bold: true });
  t(s, "대조표 · 합의/논쟁 · 보완 위치", { x: mx + 0.18, y: 5.77, w: mw - 0.3, h: 0.3, fontSize: 10.5, color: C.sub });
  t(s, `데이터: 공개 R&D 공고 3건(국가과학기술연구회·우주항공청·산업통상부) + 쪽별 정답표 · 인용 검사·집계는 LLM을 모르는 순수 코드(테스트 ${N.tests}개)`,
    { x: X0, y: 6.4, w: W, h: 0.3, fontSize: 12, color: C.sub });
  t(s, "보안: 초안은 서버에 저장하지 않지만 외부 모델 API로는 전송됩니다 — LLM은 포트로 분리돼 국산·기관 내부 모델로 교체할 수 있는 구조",
    { x: X0, y: 6.75, w: W, h: 0.3, fontSize: 12, color: C.sub });
  s.addNotes(`[20초] 평가위원은 ${VENDORS.join(", ")} ${VENDORS.length}개 회사 모델로 나눴고, 공고 파싱과 점검 질문은 주 엔진 ${N.extract[0].engine}가 맡습니다. 전체 흐름은 LangGraph 상태 그래프입니다. 검색으로 조각을 넣는 대신 원문을 통째로 넣고 인용으로 대조합니다. 인용 검사에 실패하면 재질의로 되돌아가는 루프가 있습니다. 선행연구 탐색은 MCP 도구 서버로 감싸서, 검색기를 바꿔 끼울 수 있고 다른 AI 비서도 같은 도구를 부를 수 있습니다.`);
}

// ---------- 7. 신뢰 장치 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "없는 인용은 통과하지 못하게");
  title(s, "「충족」이라 말하려면,\n초안에서 **글자 그대로** 인용해야 합니다");
  const lw = 6.6;
  numRow(s, "01", "판정마다 초안 원문 인용을 함께 제출", "칭찬(충족)에도 증거를 요구합니다", X0, 2.95, lw);
  numRow(s, "02", "코드가 원문과 글자 단위로 대조", "공백·문장부호만 빼고 연속 문자열 일치 — LLM이 아닌 규칙", X0, 4.0, lw);
  numRow(s, "03", "없으면 무효 → 그 평가위원에게 한 번 재질의", "그래도 없으면 「충족」을 인정하지 않습니다(강등)", X0, 5.05, lw);
  const rx = 8.35, rw = R - rx;
  bigNum(s, `${B.invalid}건`, `판정 ${B.n_verdicts}개 중 인용이 원문에 없던 것`, rx, 2.9, rw, { size: 44, gap: 0.95, lSize: 12.5 });
  if (B.cited !== null && B.cited !== undefined) {
    bigNum(s, `${B.cited}건`, "다시 물어 원문 인용을 찾은 판정(충족 유지)", rx, 4.35, rw, { size: 44, gap: 0.95, lSize: 12.5, color: C.blue });
    t(s, `「부족·누락」으로 정정 ${B.downgraded}건 · 여전히 무효 ${B.still}건(충족 인정 안 함)`, { x: rx, y: 5.65, w: rw, h: 0.35, fontSize: 12, bold: true, color: C.sub });
  } else {
    const rest = B.invalid - B.fixed;
    bigNum(s, `${B.fixed}건`, `다시 물은 뒤 무효에서 벗어남(인용 통과 또는 「부족」으로 하향)${rest > 0 ? ` · 남은 ${rest}건은 점수에서 제외` : ""}`, rx, 4.45, rw, { size: 44, gap: 0.95, lSize: 12.5, color: C.blue });
  }
  hline(s, 6.1);
  t(s, "한계: 인용이 판정을 뒷받침하는지는 사람이 봅니다 — 그래서 화면에 인용을 그대로 펼쳐 둡니다.", { x: X0, y: 6.3, w: W, h: 0.4, fontSize: 15, bold: true });
  src(s, "숫자: 예선 기획서 실행 기록(data/runs/nais-hackathon-2026--original.json의 trace)" + partial(B));
  s.addNotes(`[25초] LLM 심사의 가장 큰 위험은 그럴듯한 칭찬입니다. 저희는 칭찬에도 증거를 요구합니다. 인용을 코드가 원문과 대조하고, 없으면 무효로 돌려 한 번 다시 묻습니다. 이 실행에서 ${B.n_verdicts}개 판정 중 ${B.invalid}건이 원문에 없는 인용이었고, 다시 물은 뒤 ${B.cited ?? B.fixed}건은 원문 인용을 찾았고${B.cited !== null && B.cited !== undefined ? `, ${B.downgraded}건은 부족으로 정정, ${B.still}건은 끝까지 무효라 점수에서 뺐습니다` : ""}. 인용이 판정을 뒷받침하는지는 사람이 보도록 화면에 그대로 둡니다.`);
}

// ---------- 8. 측정 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "측정");
  title(s, "정답표를 먼저 만들고,\n**숫자**로 쟀습니다");
  const ex = N.extract;
  const nm = (e) => e.agency.replace("국가과학기술연구회", "NAIS 해커톤");
  t(s, "① 공고 파싱 — 정답표 요건을 놓치지 않은 비율(재현율, 목표 90%)", { x: X0, y: 2.85, w: 6.6, h: 0.35, fontSize: 13, bold: true, color: C.sub });
  s.addChart(pres.charts.BAR, [{ name: "재현율", labels: ex.map((e) => `${nm(e)} · ${e.pages}쪽`), values: ex.map((e) => e.recall) }], {
    x: X0 - 0.1, y: 3.2, w: 6.5, h: 2.45, barDir: "bar", chartColors: [C.blue],
    catAxisLabelColor: C.ink, catAxisLabelFontSize: 12, catAxisLabelFontFace: F, catAxisOrientation: "maxMin",
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 100, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showValue: true, dataLabelFormatCode: '0"%"', dataLabelColor: C.ink, dataLabelFontSize: 13, dataLabelFontBold: true, dataLabelFontFace: F,
    dataLabelPosition: "outEnd", barGapWidthPct: 70, showLegend: false,
  });
  const weak = ex.filter((e) => e.recall < 90);
  const ca = [...new Set(ex.map((e) => e.crit_agree))];
  const catxt = ca.length === 1 ? `심사표 이름·배점 일치 ${ex.length}건 모두 ${ca[0]}%` : `심사표 일치 ${ex.map((e) => `${nm(e)} ${e.crit_agree}%`).join(" · ")}`;
  const secs = ex.map((e) => Math.round(e.seconds));
  t(s, `${ex.map((e) => `${nm(e)} ${e.hit}/${e.n_gold}`).join(" · ")}${weak.length ? `(가장 약한 곳: ${weak.map(nm).join("·")})` : ""}\n${catxt} · 1건 ${Math.min(...secs)}~${Math.max(...secs)}초`,
    { x: X0, y: 5.75, w: 6.6, h: 0.6, fontSize: 11.5, color: C.gray, lineSpacingMultiple: 1.15 });
  const rx = 8.1, rw = R - rx;
  t(s, `② 일부러 지운 초안 시험${P.stage ? ` (${P.stage} 심사표)` : ""}`, { x: rx, y: 2.85, w: rw, h: 0.35, fontSize: 13, bold: true, color: C.sub });
  bigNum(s, P.detect, `근거 블록을 하나씩 지운 초안 ${P.n}개 중 짚은 수\n짚은 곳의 정확도 ${P.precision}`,
    rx, 3.2, rw, { size: 44, gap: 0.95, lSize: 12.5, color: C.blue });
  if (P.ready) {
    const v1 = P.v1 && P.v1.length ? `첫 초안 세트 ${Math.min(...P.v1)}~${Math.max(...P.v1)}/${P.n} → 블록 재설계 후 결과(사전 등록 아님). ` : "";
    t(s, `${v1}${P.higher ? `지운 초안 ${P.n}개 중 ${P.lower}개만 근거 충족도가 원본(${P.base})보다 낮음 — 판정은 총점이 아니라 「짚은 곳」.` : `지운 초안의 점수는 원본 ${P.base}점보다 ${P.drop_min}~${P.drop_max}점 낮았습니다.`}`,
      { x: rx, y: 4.85, w: rw, h: 0.75, fontSize: 12, color: C.sub, lineSpacingMultiple: 1.15 });
  }
  t(s, `③ 1건 채점 ${B.seconds}초 — 평가위원 ${B.reviewers}/${B.of}명 응답${B.prior_n ? " · 선행연구 탐색 포함" : ""}(공고 파싱 제외)`, { x: rx, y: 5.95, w: rw, h: 0.55, fontSize: 12, bold: true, color: C.ink, lineSpacingMultiple: 1.15 });
  src(s, `정답표: 다른 모델(Claude)이 쪽마다 판독 · 파싱 주 엔진 ${[...new Set(ex.map((e) => e.engine))].join(", ")} · 추출 수는 정답보다 많음(${ex.map((e) => e.n_extracted).join("·")}개 vs ${ex.map((e) => e.n_gold).join("·")}개) · 시연은 저장된 파싱 결과`);
  s.addNotes(`[25초] 정확도는 숫자로 보여 드립니다. 정답표 대비 요건을 놓치지 않은 비율이 ${ex.map((e) => `${nm(e)} ${e.recall}%`).join(", ")}입니다. 가장 약한 곳도 그대로 둡니다. 기획서에서 근거 블록을 일부러 하나씩 지운 초안 ${P.n}개 중 ${P.detect}를 짚었고, 지운 초안은 점수도 내려갔습니다.`);
}

// ---------- 9. 심사위원의 마음 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "우리 자신에게 먼저 — 이 대회 본선 심사표로 예선 기획서를");
  const nonSel = B.stances.filter((x) => x.decision !== "선정");
  title(s, B.n_gaps + B.n_contested === 0 ? `항목 판정은 모두 충족인데,\n**${nonSel.length}명**은 보류였습니다` : `평가위원 ${KN} 명 중,\n**${nonSel.length}명**은 보류였습니다`);
  const pname = Object.fromEntries(B.personas.map((q) => [q.id, q.name]));
  B.stances.forEach((x, i) => {
    const y = 2.9 + i * 0.5, sel = x.decision === "선정";
    t(s, pname[x.id] || x.id, { x: X0, y, w: 3.0, h: 0.36, fontSize: 15, bold: true });
    t(s, x.decision, { x: X0 + 3.1, y, w: 1.0, h: 0.36, fontSize: 15, bold: true, color: sel ? C.gray : C.blue });
    if (i < B.stances.length - 1) hline(s, y + 0.43, X0, 4.1);
  });
  const bx = 5.7, bw = R - bx, by = 2.85;
  box(s, bx, by, bw, 2.85, { fill: C.bg2, lineColor: C.bg2 });
  t(s, "보류의 결정 포인트 — 평가위원이 쓴 원문 그대로", { x: bx + 0.3, y: by + 0.2, w: bw - 0.6, h: 0.3, fontSize: 12, bold: true, color: C.blue });
  t(s, nonSel.map((x, i) => ({ text: `${pname[x.id] || x.id}  “${x.point}”`, options: { breakLine: i < nonSel.length - 1, paraSpaceAfter: 8 } })),
    { x: bx + 0.3, y: by + 0.6, w: bw - 0.6, h: 2.15, fontSize: 12, color: C.ink, lineSpacingMultiple: 1.15 });
  hline(s, 6.0);
  const ex = N.extract;
  const ca = [...new Set(ex.map((e) => e.crit_agree))];
  t(s, "그래서 오늘은 목표치가 아니라 실측치를 가져왔습니다.", { x: X0, y: 6.13, w: W, h: 0.4, fontSize: 16, bold: true });
  t(s, `공고 파싱 요건 재현율 ${ex.map((e) => e.recall + "%").join("·")}(심사표 이름·배점 ${ca.length === 1 ? ca[0] + "%" : ca.join("·") + "%"}) · 일부러 지운 초안 탐지 ${P.detect} · 정밀도 ${P.precision} — 8장`,
    { x: X0, y: 6.55, w: W, h: 0.35, fontSize: 13, color: C.sub });
  src(s, "data/runs/nais-hackathon-2026--original.json 의 stances(선정·보류·탈락 + 결정 포인트) · 항목 합산보다 결정 포인트로 등수를 먼저 정한다(현장 멘토링)" + partial(B));
  s.addNotes(`[25초] 저희 도구로 저희 예선 기획서를 이 대회 본선 심사표로 먼저 읽혔습니다. 여섯 명 중 ${nonSel.length}명이 보류였고, 이유가 분명했습니다. ${nonSel.map((x) => `${pname[x.id]}은 '${x.point}'`).join(", ")}. 그래서 오늘은 목표치가 아니라 실측치를 가져왔습니다. 요건 재현율 ${ex.map((e) => e.recall + "%").join(", ")}, 일부러 지운 초안 ${P.n}개 중 ${P.detect}를 짚었습니다.`);
}

// ---------- 10. 확장 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "확장");
  title(s, "연구자에서 **전문기관**까지,\n같은 엔진이 갑니다");
  const cols = [["연구자 · 구현", "제출 전 셀프 점검", "지금 이 앱 — 고칠 곳부터, 갈리는 곳은 판단"],
    ["전문기관 · 계획", "접수 후 요건 사전검토", "형식 미비·필수 서류 누락 스크리닝"],
    ["평가위원 · 계획", "지표별 근거 위치 표시", "심사 보조 — 판정은 사람이"]];
  const cw = 3.4, cg = (W - 3 * cw) / 2;
  cols.forEach(([who, what, desc], i) => {
    const x = X0 + i * (cw + cg);
    t(s, String(i + 1).padStart(2, "0") + "  " + who, { x, y: 2.95, w: cw, h: 0.4, fontSize: 15, bold: true, color: C.blue });
    t(s, what, { x, y: 3.4, w: cw, h: 0.45, fontSize: 19, bold: true });
    t(s, desc, { x, y: 3.9, w: cw, h: 0.4, fontSize: 12.5, color: C.gray });
    if (i < 2) arrow(s, x + cw + 0.12, 3.62, x + cw + cg - 0.12, 3.62);
  });
  hline(s, 4.55);
  t(s, "같은 엔진, 다른 문서", { x: X0, y: 4.75, w: 4, h: 0.35, fontSize: 13, bold: true, color: C.sub });
  [["연차·성과보고서 · 계획", "계획 지표 대비 실적"], ["연구비 정산 · 계획", "증빙 대비 집행 항목"], ["MCP로 연결 · 구현", "도구 2개 · NAIS 플랫폼·AI 비서 연결"]].forEach(([a, b], i) => {
    const x = X0 + i * (cw + cg);
    box(s, x, 5.15, cw, 0.95);
    t(s, a, { x: x + 0.22, y: 5.27, w: cw - 0.4, h: 0.35, fontSize: 15, bold: true });
    t(s, b, { x: x + 0.22, y: 5.65, w: cw - 0.4, h: 0.3, fontSize: 12, color: C.gray });
  });
  t(s, [{ text: "다음 단계 — 심사 의견 데이터는 평가기관에 있습니다. 전문기관과 연계하면 실제 심사 의견 유형으로 평가위원을 보정합니다.", options: { bold: true, color: C.ink, breakLine: true } },
    { text: "지금은 공개 자료 + 현장 심사 경험 기반 유형 · 첫 실증 목표: 전문기관 접수 사전검토 1회(형식 미비 재현율 90%)", options: {} }],
    { x: X0, y: 6.45, w: W, h: 0.7, fontSize: 12.5, color: C.sub, lineSpacingMultiple: 1.2 });
  s.addNotes("[20초] 같은 엔진이 연구자의 셀프 점검에서 전문기관 접수 사전검토, 평가위원 심사 보조로 갑니다. 오늘 멘토링에서, 실제 심사 의견 데이터는 평가기관에 있다고 들었습니다. 전문기관과 연계하면 그 의견 유형으로 가상 평가위원을 보정할 수 있습니다. 지금은 공개 자료와 심사 경험 기반 유형입니다.");
}

// ---------- 11. 마무리 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "지금 직접 눌러 보세요", 1.15);
  title(s, `${KN} 명의 평가위원이,\n**먼저** 읽어 드립니다.`, { y: 1.8, h: 2.3, fontSize: 46 });
  t(s, `커밋 ${N.git.commits}개 · 코드는 전부 본선 중 커밋(첫 코드 커밋 ${N.git.first_code}, 그 전엔 문서뿐)\nSPEC → 테스트 → 구현 순서 · 코딩 에이전트 활용 규칙까지 공개(AGENTS.md)`, { x: X0, y: 4.45, w: 6.6, h: 0.8, fontSize: 14, color: C.sub, lineSpacingMultiple: 1.25 });
  t(s, "라이브가 끊기면 — 앱의 「② 우리 기획서 전·후」 탭이 저장된 실행 기록으로 같은 결과를 보여 줍니다", { x: X0, y: 5.45, w: 6.6, h: 0.6, fontSize: 12, color: C.gray, lineSpacingMultiple: 1.2 });
  t(s, "팀 루미아 · 김태걸 · 박세훈", { x: X0, y: 6.4, w: 6, h: 0.45, fontSize: 16, bold: true });
  const qs = [["라이브 앱", N.qr_live, N.live_url.replace(/^https?:\/\//, "")], ["GitHub", N.qr_repo, N.repo_url.replace(/^https?:\/\//, "")]];
  qs.forEach(([k, img, url], i) => {
    const x = 7.95 + i * 2.3, y = 2.0;
    box(s, x, y, 2.05, 3.05);
    s.addImage({ path: img, x: x + 0.28, y: y + 0.28, w: 1.5, h: 1.5 });
    t(s, k, { x: x + 0.2, y: y + 1.98, w: 1.65, h: 0.35, fontSize: 14, bold: true });
    t(s, url, { x: x + 0.2, y: y + 2.38, w: 1.7, h: 1.0, fontSize: 9.5, color: C.gray, lineSpacingMultiple: 1.15, fit: "none" });
  });
  s.addNotes(`[10초] ${KN} 명의 평가위원이, 먼저 읽어 드립니다. 화면의 주소에서 지금 직접 눌러 보실 수 있습니다. 감사합니다.`);
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("wrote", f));
