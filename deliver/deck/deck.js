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
const gem = B.personas.filter((p) => /gemini/i.test(p.model)).length;
const sol = B.personas.filter((p) => /solar/i.test(p.model)).length;

// ---------- 1. 표지 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "2026 NAIS AI 해커톤 본선 · 팀 루미아", 1.15);
  title(s, "평가위원의 눈으로,\n제출 전에 **빈칸**을 먼저.", { y: 1.8, h: 2.5, fontSize: 56 });
  t(s, "RFP-to-Fit — 국가 R&D 공고를 넣으면, 가상 평가위원 5명이 초안을 먼저 채점합니다", { x: X0, y: 4.55, w: W, h: 0.5, fontSize: 19, color: C.sub });
  t(s, "김태걸 · 박세훈", { x: X0, y: 6.4, w: 5, h: 0.45, fontSize: 16, bold: true });
  s.addNotes("[10초] 안녕하세요, 팀 루미아입니다. 저희는 제안서를 대신 쓰는 AI가 아니라, 제출 전에 평가위원의 눈으로 먼저 읽어 주는 에이전트를 만들었습니다.");
}

// ---------- 2. 문제 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "문제");
  title(s, "제안서는 아이디어보다,\n**심사표**를 잘못 읽어서 떨어집니다");
  const M = N.motir;
  bigNum(s, `${M.pages}쪽`, "산업통상부 R&D 공고 한 건의 분량", X0, 3.35, 3.6);
  bigNum(s, `${M.n_req}개`, "지키지 않으면 탈락·감점되는 요건", X0 + 4.1, 3.35, 3.6);
  bigNum(s, `${M.tables}종`, "세부사업마다 따로 있는 평가표", X0 + 8.2, 3.35, 3.3, { color: C.blue });
  hline(s, 5.55);
  t(s, "연구자는 연구의 언어로 쓰고, 평가위원은 지표의 언어로 읽습니다. 그 사이의 빈칸은 제출 뒤에야 보입니다.",
    { x: X0, y: 5.85, w: W, h: 0.5, fontSize: 16, bold: true });
  src(s, "산업통상부 공고 제2026-64호 — 요건·평가표를 쪽마다 판독해 만든 정답표(data/gold, 저장소 공개)");
  s.addNotes("[35초] 여기 계신 분들 모두 제안서를 쓰고, 또 심사하시는 분들입니다. 공고 한 건이 37쪽, 지켜야 할 요건이 58개, 평가표가 3종입니다. 떨어지는 제안서의 상당수는 아이디어가 아니라 '이 지표에 대한 근거가 없다'에서 깎입니다. 문제는 그걸 제출 뒤에야 안다는 겁니다.");
}

// ---------- 3. 핵심 아이디어 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "핵심 아이디어");
  title(s, "한 명의 점수는 취향,\n**다섯 명**이 따로 보면 갈립니다");
  B.personas.forEach((p, i) => {
    const y = 2.95 + i * 0.66;
    t(s, String(i + 1).padStart(2, "0"), { x: X0, y, w: 0.6, h: 0.4, fontSize: 16, bold: true, color: C.blue });
    t(s, p.name, { x: X0 + 0.65, y, w: 3.4, h: 0.4, fontSize: 16, bold: true });
    t(s, /gemini/i.test(p.model) ? "Google Gemini" : "Upstage Solar(국산)", { x: X0 + 4.05, y: y + 0.03, w: 2.3, h: 0.4, fontSize: 12.5, color: C.gray });
    if (i < 4) hline(s, y + 0.53, X0, 6.35);
  });
  const cx = 7.85, cw = R - cx;
  [["합의 결핍", "5명 중 4명 이상이 깎은 곳", "반드시 고칠 곳"], ["논쟁 지점", "의견이 2~3명으로 갈린 곳", "연구자가 판단할 곳"]].forEach(([k, a, b], i) => {
    const y = 2.95 + i * 1.65;
    box(s, cx, y, cw, 1.4, { fill: i ? C.white : C.bg2 });
    t(s, k, { x: cx + 0.3, y: y + 0.22, w: cw - 0.6, h: 0.35, fontSize: 13, bold: true, color: C.blue });
    t(s, a, { x: cx + 0.3, y: y + 0.55, w: cw - 0.6, h: 0.4, fontSize: 17, bold: true });
    t(s, "→ " + b, { x: cx + 0.3, y: y + 0.96, w: cw - 0.6, h: 0.35, fontSize: 13, color: C.sub });
  });
  t(s, `평가위원 모델도 나눴습니다 — Gemini ${gem}명 + 국산 Solar ${sol}명. 한 회사 모델의 치우침이 '합의'로 굳지 않게.`,
    { x: X0, y: 6.45, w: W, h: 0.4, fontSize: 13.5, color: C.sub });
  s.addNotes("[35초] 평가위원 한 명의 점수는 취향입니다. 그래서 관점이 다른 다섯 명이 서로의 답을 모른 채 채점합니다. 네 명 이상이 깎으면 반드시 고칠 곳, 의견이 갈리면 연구자가 판단할 곳입니다. 모델도 Gemini와 국산 Solar로 나눠, 한 회사 모델의 치우침이 합의로 굳지 않게 했습니다.");
}

// ---------- 4. 데모 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "데모 — 이 대회 공고로");
  title(s, `공고 한 건과 초안 한 편,\n**${B.seconds}초** 뒤 고칠 곳이 나옵니다`);
  const lw = 4.7;
  numRow(s, "01", `요건 ${B.n_req}개 · 심사표 ${B.n_crit}개 자동 추출`, "모두 공고 쪽 번호와 원문 인용이 붙습니다", X0, 2.95, lw, { hSize: 16 });
  numRow(s, "02", `점검 질문 ${B.n_items}개를 5명에게 따로`, "서로의 답을 모른 채 판정 + 인용", X0, 4.05, lw, { hSize: 16 });
  numRow(s, "03", `고칠 곳 ${B.n_gaps} · 판단할 곳 ${B.n_contested}`, "보완은 문장 대신 「무엇을·어디에」만", X0, 5.15, lw, { hSize: 16 });
  const ix = 6.05, iw = R - ix;
  const put = (img, y, maxH) => {
    let w = iw, h = iw * img.h / img.w; if (h > maxH) { h = maxH; w = h * img.w / img.h; }
    box(s, ix, y, iw, h + 0.2);
    s.addImage({ path: img.path, x: ix + (iw - w) / 2 + 0.1 * (w / iw), y: y + 0.1, w: w - 0.2 * (w / iw), h: h });
    return y + h + 0.2;
  };
  let y = 2.95;
  if (N.img.input) y = put(N.img.input, y, 1.95) + 0.2;
  if (N.img.result) put(N.img.result, y, 6.8 - y - 0.2);
  src(s, "라이브 앱 실제 화면(Streamlit) — 마지막 장의 주소에서 직접 눌러 볼 수 있습니다");
  s.addNotes(`[70초] 지금 보시는 건 이 대회 공고입니다. 공고에서 요건 ${B.n_req}개와 본선 심사표 ${B.n_crit}개를 스스로 찾아냈고, 저희 예선 기획서를 넣었습니다. 점검 질문 ${B.n_items}개가 다섯 명에게 따로 가고, 약 ${B.seconds}초 뒤 모두가 깎는 곳과 의견이 갈리는 곳이 나옵니다. 보완은 문장을 써 주지 않고 '어떤 근거를, 어느 절에'만 지정합니다.`);
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
  const steps = [["H", "공고·초안 올리기"], ["A", "3쪽씩 병렬 파싱"], ["R", "공고 인용 검사"], ["A", "점검 질문 생성"], ["M", "선행연구 탐색"], ["A", "5명 독립 채점"],
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
  t(s, "↺ 1회", { x: colX(4) + bw - 0.05, y: y2 + bh + 0.06, w: gap + 0.1, h: 0.25, fontSize: 10, bold: true, color: C.blue, align: "center" });
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
  title(s, "두 회사 모델, 그래프 하나,\n바꿔 끼우는 **MCP** 도구");
  const chip = (x, y, w, label, kind) => {
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
  t(s, "LangGraph 상태 그래프", { x: gx + 0.2, y: gy + 0.14, w: 3, h: 0.3, fontSize: 11.5, bold: true, color: C.sub });
  arrow(s, X0 + 2.3, 3.9, gx - 0.05, 3.9);
  const r1 = [["점검 질문", "A"], ["선행 탐색", "A"], ["5명 독립 채점", "A"]];
  const w1 = 1.55, g1 = (gw - 0.4 - 3 * w1) / 2;
  r1.forEach(([l, k], i) => { chip(gx + 0.2 + i * (w1 + g1), gy + 0.55, w1, l, k); if (i < 2) arrow(s, gx + 0.2 + i * (w1 + g1) + w1 + 0.03, gy + 0.86, gx + 0.2 + (i + 1) * (w1 + g1) - 0.03, gy + 0.86); });
  const r2 = [["인용 실재 검사", "R"], ["재질의 ↺", "A"], ["합의·논쟁 집계", "R"], ["보완 지정", "A"]];
  const w2 = 1.2, g2 = (gw - 0.4 - 4 * w2) / 3;
  r2.forEach(([l, k], i) => { chip(gx + 0.2 + i * (w2 + g2), gy + 1.55, w2, l, k); if (i < 3) arrow(s, gx + 0.2 + i * (w2 + g2) + w2 + 0.02, gy + 1.86, gx + 0.2 + (i + 1) * (w2 + g2) - 0.02, gy + 1.86); });
  const lastX = gx + 0.2 + 2 * (w1 + g1) + w1 / 2;
  arrow(s, lastX, gy + 1.2, gx + 0.2 + w2 / 2 + 0.2, gy + 1.52);
  // LLM
  [["Google Gemini", `파싱 · 점검 질문 · 평가위원 ${gem}명`], ["Upstage Solar (국산)", `평가위원 ${sol}명 · 장애 시 상호 대체`]].forEach(([a, b], i) => {
    const x = gx + i * (gw / 2 + 0.1), w = gw / 2 - 0.1, y = 5.3;
    box(s, x, y, w, 0.85, { fill: C.blueBg, lineColor: C.blue });
    t(s, a, { x: x + 0.18, y: y + 0.12, w: w - 0.3, h: 0.32, fontSize: 13.5, bold: true, color: C.blueInk });
    t(s, b, { x: x + 0.18, y: y + 0.47, w: w - 0.3, h: 0.3, fontSize: 10.5, color: C.sub });
  });
  // MCP
  const mx = 9.7, mw = R - mx;
  box(s, mx, 2.7, mw, 1.25, { lineColor: C.blue });
  t(s, "MCP 도구 서버", { x: mx + 0.18, y: 2.84, w: mw - 0.3, h: 0.32, fontSize: 13.5, bold: true, color: C.blueInk });
  t(s, "search_prior_art · stdio\n다른 AI 비서도 같은 도구 호출", { x: mx + 0.18, y: 3.2, w: mw - 0.3, h: 0.65, fontSize: 10.5, color: C.sub, lineSpacingMultiple: 1.2 });
  arrow(s, gx + gw + 0.03, 3.3, mx - 0.03, 3.3, C.blue);
  box(s, mx, 4.25, mw, 0.85);
  t(s, "OpenAlex", { x: mx + 0.18, y: 4.37, w: mw - 0.3, h: 0.32, fontSize: 13.5, bold: true });
  t(s, "공개 학술 DB · 선행연구 검색", { x: mx + 0.18, y: 4.72, w: mw - 0.3, h: 0.3, fontSize: 10.5, color: C.gray });
  arrow(s, mx + mw / 2, 3.98, mx + mw / 2, 4.22);
  box(s, mx, 5.3, mw, 0.85, { fill: C.bg2, lineColor: C.bg2 });
  t(s, "출력", { x: mx + 0.18, y: 5.42, w: mw - 0.3, h: 0.32, fontSize: 13.5, bold: true });
  t(s, "대조표 · 합의/논쟁 · 보완 위치", { x: mx + 0.18, y: 5.77, w: mw - 0.3, h: 0.3, fontSize: 10.5, color: C.sub });
  t(s, `데이터: 공개 R&D 공고 3건(국가과학기술연구회·우주항공청·산업통상부) + 쪽별 정답표 · 인용 검사·집계는 LLM을 모르는 순수 코드(테스트 ${N.tests}개)`,
    { x: X0, y: 6.5, w: W, h: 0.35, fontSize: 12, color: C.sub });
  s.addNotes("[20초] 평가위원은 Gemini와 국산 Solar로 나눴고, 전체 흐름은 LangGraph 상태 그래프입니다. 인용 검사에 실패하면 재질의로 되돌아가는 루프가 있습니다. 선행연구 탐색은 MCP 도구 서버로 감싸서, 검색기를 바꿔 끼울 수 있고 다른 AI 비서도 같은 도구를 부를 수 있습니다.");
}

// ---------- 7. 신뢰 장치 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "가짜로 돌아가는 척을 못 하게");
  title(s, "「충족」이라 말하려면,\n초안에서 **글자 그대로** 인용해야 합니다");
  const lw = 6.6;
  numRow(s, "01", "판정마다 초안 원문 인용을 함께 제출", "칭찬(충족)에도 증거를 요구합니다", X0, 2.95, lw);
  numRow(s, "02", "코드가 원문과 글자 단위로 대조", "공백·문장부호만 빼고 연속 문자열 일치 — LLM이 아닌 규칙", X0, 4.0, lw);
  numRow(s, "03", "없으면 무효 → 그 평가위원에게 한 번 재질의", "그래도 없으면 「충족」을 점수에서 뺍니다(강등)", X0, 5.05, lw);
  const rx = 8.35, rw = R - rx;
  bigNum(s, `${B.invalid}건`, `판정 ${B.n_verdicts}개 중 인용이 원문에 없던 것`, rx, 2.9, rw, { size: 44, gap: 0.95, lSize: 12.5 });
  const rest = B.invalid - B.fixed;
  bigNum(s, `${B.fixed}건`, `재질의로 원문 인용 교정${rest > 0 ? ` · 남은 ${rest}건 강등` : ""}`, rx, 4.45, rw, { size: 44, gap: 0.95, lSize: 12.5, color: C.blue });
  hline(s, 6.1);
  t(s, "같은 검사를 공고에도 겁니다 — 요건·심사표도 그 쪽에 원문이 없으면 버립니다.", { x: X0, y: 6.3, w: W, h: 0.4, fontSize: 15, bold: true });
  src(s, "숫자: 예선 기획서 실행 기록(data/runs/nais-hackathon-2026--original.json의 trace)");
  s.addNotes(`[25초] LLM 심사의 가장 큰 위험은 그럴듯한 칭찬입니다. 저희는 칭찬에도 증거를 요구합니다. 인용을 코드가 원문과 대조하고, 없으면 무효로 돌려 한 번 다시 묻습니다. 이 실행에서 ${B.n_verdicts}개 판정 중 ${B.invalid}건이 원문에 없는 인용이었고, 재질의로 ${B.fixed}건이 교정됐습니다.`);
}

// ---------- 8. 측정 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "측정");
  title(s, "정답표를 먼저 만들고,\n**숫자**로 쟀습니다");
  const ex = N.extract;
  const lbl = (e) => `${e.agency.replace("국가과학기술연구회", "NAIS 해커톤")} (${e.pages}쪽)`;
  t(s, "공고 파싱 — 정답표 대비 요건 재현율 (목표 90%)", { x: X0, y: 2.85, w: 6.4, h: 0.35, fontSize: 13, bold: true, color: C.sub });
  s.addChart(pres.charts.BAR, [{ name: "재현율", labels: ex.map(lbl), values: ex.map((e) => e.recall) }], {
    x: X0 - 0.1, y: 3.2, w: 6.5, h: 2.55, barDir: "bar", chartColors: [C.blue],
    catAxisLabelColor: C.ink, catAxisLabelFontSize: 12, catAxisLabelFontFace: F, catAxisOrientation: "maxMin",
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 100, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showValue: true, dataLabelFormatCode: '0"%"', dataLabelColor: C.ink, dataLabelFontSize: 13, dataLabelFontBold: true, dataLabelFontFace: F,
    dataLabelPosition: "outEnd", barGapWidthPct: 70, showLegend: false,
  });
  const weak = ex.filter((e) => e.recall < 90);
  t(s, ex.map((e) => `${e.agency.replace("국가과학기술연구회", "NAIS")} ${e.hit}/${e.n_gold}`).join(" · ")
    + (weak.length ? ` — ${weak.map((e) => e.agency.replace("국가과학기술연구회", "NAIS 공고")).join("·")}가 가장 약한 곳, 그대로 공개합니다` : ""),
    { x: X0, y: 5.85, w: 6.4, h: 0.55, fontSize: 11.5, color: C.gray, lineSpacingMultiple: 1.15 });
  const rx = 8.1, rw = R - rx;
  const pWeak = P.ready && P.detected / P.n < 0.6;
  bigNum(s, P.ready ? P.detect : P.detect, `결함 주입 — 지표별 블록을 하나씩 지운 초안 ${P.n}개 중 지운 곳을 짚은 수 · 정밀도 ${P.precision}`,
    rx, 2.85, rw, { size: 44, gap: 0.95, lSize: 12.5, color: C.blue });
  if (pWeak) t(s, "약한 숫자도 그대로 둡니다 — 항목 단위 감도가 다음 과제", { x: rx, y: 4.3, w: rw, h: 0.3, fontSize: 11.5, bold: true, color: C.sub });
  bigNum(s, `${B.seconds}초`, "1건 실행 — 평가위원 5명 · 선행연구 탐색 포함", rx, 4.75, rw, { size: 44, gap: 0.95, lSize: 12.5 });
  src(s, "정답표: 파이프라인(Gemini·Solar)과 독립된 모델이 공고를 쪽마다 판독 · 측정 스크립트 scripts/eval_extract.py · eval_planted.py 공개");
  s.addNotes(`[25초] 정확도는 말이 아니라 숫자로 보여 드립니다. 공고를 쪽마다 판독한 정답표 대비 요건 재현율이 ${ex.map((e) => `${e.agency} ${e.recall}%`).join(", ")}입니다. 기획서에서 지표별 블록을 하나씩 지운 초안 ${P.n}개로 결함 주입 실험을 했고 ${P.detect}를 짚었습니다. 약한 숫자도 그대로 공개합니다.`);
}

// ---------- 9. 메타 데모 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "우리 자신에게 먼저");
  title(s, "이 대회 심사표로,\n**우리**를 먼저 채점했습니다");
  bigNum(s, `${B.total}점`, "예선 기획서 — 본선 심사표 기준", X0, 2.9, 3.2, { size: 50, gap: 1.0 });
  t(s, "→", { x: X0 + 3.2, y: 3.0, w: 0.6, h: 0.8, fontSize: 36, color: C.gray });
  bigNum(s, `${A.total}점`, "보완 후", X0 + 3.95, 2.9, 3.0, { size: 50, gap: 1.0, color: C.blue });
  const gy = 4.55;
  box(s, X0, gy, 6.9, 1.35, { fill: C.bg2, lineColor: C.bg2 });
  t(s, `도구가 짚은 합의 결핍 ${B.n_gaps}곳 · 논쟁 지점 ${B.n_contested}곳`, { x: X0 + 0.25, y: gy + 0.18, w: 6.4, h: 0.3, fontSize: 12, bold: true, color: C.blue });
  t(s, [...B.gaps, ...B.contested].slice(0, 3).map((q) => ({ text: "“" + q + "”", options: { breakLine: true } })),
    { x: X0 + 0.25, y: gy + 0.5, w: 6.45, h: 0.8, fontSize: 11.5, color: C.ink, lineSpacingMultiple: 1.15 });
  // 오른쪽: 지표별 전·후
  const tx = 8.35, tw = R - tx;
  t(s, "지표(배점)", { x: tx, y: 2.95, w: 2.2, h: 0.3, fontSize: 11.5, color: C.gray });
  t(s, "전", { x: tx + 2.3, y: 2.95, w: 0.8, h: 0.3, fontSize: 11.5, color: C.gray, align: "right" });
  t(s, "후", { x: tx + 3.2, y: 2.95, w: 0.85, h: 0.3, fontSize: 11.5, color: C.gray, align: "right" });
  B.per.forEach((r, i) => {
    const y = 3.35 + i * 0.5, a = A.per.find((x) => x.name === r.name) || { got: "-" };
    hline(s, y - 0.06, tx, 4.05);
    const up = a.got - r.got >= 1;
    t(s, `${r.name} (${r.points})`, { x: tx, y: y + 0.04, w: 2.3, h: 0.35, fontSize: 13.5, bold: true });
    t(s, String(r.got), { x: tx + 2.3, y: y + 0.04, w: 0.8, h: 0.35, fontSize: 13.5, color: C.sub, align: "right" });
    t(s, String(a.got), { x: tx + 3.2, y: y + 0.04, w: 0.85, h: 0.35, fontSize: 13.5, bold: true, color: up ? C.blue : C.ink, align: "right" });
  });
  hline(s, 6.1);
  t(s, "그래서 오늘 이 발표에 흐름도·AI 구성도·실제 화면을 넣었습니다.", { x: X0, y: 6.28, w: W, h: 0.4, fontSize: 16, bold: true });
  src(s, "보완 후 = 예선 기획서에 「본선 구현 결과」 절을 사람이 추가(에이전트는 위치·근거 종류만 지정) · data/runs/*--original.json · *--after.json");
  s.addNotes(`[30초] 저희 도구로 저희 예선 기획서를 이 대회 본선 심사표로 먼저 채점했습니다. ${B.total}점, 그리고 '핵심 기능 UI 구성이 없다', '서비스 흐름도가 없다'는 지적이 나왔습니다. 오늘 이 발표는 그 지적을 반영한 결과이고, 보완 후 ${A.total}점입니다.`);
}

// ---------- 10. 확장 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "확장");
  title(s, "연구자에서 **전문기관**까지,\n같은 엔진이 갑니다");
  const cols = [["연구자", "제출 전 셀프 점검", "고칠 곳부터 고치고, 갈리는 곳은 판단"],
    ["전문기관", "접수 후 요건 사전검토", "형식 미비·필수 서류 누락 스크리닝"],
    ["평가위원", "지표별 근거 위치 표시", "심사 보조 — 판정은 사람이"]];
  const cw = 3.4, cg = (W - 3 * cw) / 2;
  cols.forEach(([who, what, desc], i) => {
    const x = X0 + i * (cw + cg);
    t(s, String(i + 1).padStart(2, "0") + "  " + who, { x, y: 2.95, w: cw, h: 0.4, fontSize: 15, bold: true, color: C.blue });
    t(s, what, { x, y: 3.4, w: cw, h: 0.45, fontSize: 19, bold: true });
    t(s, desc, { x, y: 3.9, w: cw, h: 0.4, fontSize: 12.5, color: C.gray });
    if (i < 2) arrow(s, x + cw + 0.12, 3.62, x + cw + cg - 0.12, 3.62);
  });
  hline(s, 4.7);
  t(s, "같은 엔진, 다른 문서", { x: X0, y: 4.95, w: 4, h: 0.35, fontSize: 13, bold: true, color: C.sub });
  [["연차·성과보고서", "계획 지표 대비 실적"], ["연구비 정산", "증빙 대비 집행 항목"], ["MCP로 연결", "NAIS 플랫폼 · 어떤 AI 비서든"]].forEach(([a, b], i) => {
    const x = X0 + i * (cw + cg);
    box(s, x, 5.4, cw, 0.95);
    t(s, a, { x: x + 0.22, y: 5.52, w: cw - 0.4, h: 0.35, fontSize: 15, bold: true });
    t(s, b, { x: x + 0.22, y: 5.9, w: cw - 0.4, h: 0.3, fontSize: 12, color: C.gray });
  });
  t(s, "정답표·측정 스크립트를 공개해 「R&D 공고 결핍 벤치마크」로 — 첫 실증 후보는 전문기관 접수 사전검토", { x: X0, y: 6.6, w: W, h: 0.35, fontSize: 12.5, color: C.sub });
  s.addNotes("[20초] 같은 엔진이 연구자의 셀프 점검에서 전문기관 접수 사전검토, 평가위원 심사 보조로 갑니다. 문서만 바꾸면 성과보고서와 연구비 정산에도 씁니다. MCP로 NAIS 플랫폼 어디에든 붙고, 정답표는 공개해 벤치마크로 키웁니다.");
}

// ---------- 11. 마무리 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "지금 직접 눌러 보세요", 1.15);
  title(s, "다섯 명의 평가위원이,\n**먼저** 읽어 드립니다.", { y: 1.8, h: 2.3, fontSize: 46 });
  t(s, `커밋 ${N.git.commits}개 · 코드는 전부 본선 중 커밋(첫 코드 커밋 ${N.git.first_code}, 그 전엔 문서뿐)`, { x: X0, y: 4.45, w: 6.6, h: 0.4, fontSize: 14, color: C.sub });
  t(s, "팀 루미아 · 김태걸 · 박세훈", { x: X0, y: 6.4, w: 6, h: 0.45, fontSize: 16, bold: true });
  const qs = [["라이브 앱", N.qr_live, N.live_url.replace(/^https?:\/\//, "")], ["GitHub", N.qr_repo, N.repo_url.replace(/^https?:\/\//, "")]];
  qs.forEach(([k, img, url], i) => {
    const x = 7.95 + i * 2.3, y = 2.6;
    box(s, x, y, 2.05, 3.55);
    s.addImage({ path: img, x: x + 0.28, y: y + 0.28, w: 1.5, h: 1.5 });
    t(s, k, { x: x + 0.2, y: y + 1.98, w: 1.65, h: 0.35, fontSize: 14, bold: true });
    t(s, url, { x: x + 0.2, y: y + 2.38, w: 1.7, h: 1.0, fontSize: 9.5, color: C.gray, lineSpacingMultiple: 1.15, fit: "none" });
  });
  s.addNotes("[10초] 다섯 명의 평가위원이, 먼저 읽어 드립니다. 화면의 주소에서 지금 직접 눌러 보실 수 있습니다. 감사합니다.");
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("wrote", f));
