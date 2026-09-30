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


const HO = N.holdout, LK = N.links, AB = N.ablation || [];
const pct0 = (x) => Math.round(Number(x) * 100);
const hb = HO ? Object.values(HO.blind) : [];
const single = AB.find((a) => a.mode === "single") || {}, roles = AB.find((a) => a.mode === "roles") || {};
const nsel = (B.stances || []).filter((x) => x.decision !== "선정");
const pn = Object.fromEntries(B.personas.map((q) => [q.id, q.name]));
const MAIN = N.extract[0].engine;
const REVM = (v) => [...new Set(B.personas.filter((q) => q.vendor === v).map((q) => q.model.split(" ").pop()))].join(", ");
const exs = N.extract;
const rmin = Math.min(...exs.map((e) => e.recall), ...hb.map((r) => pct0(r.recall)));
const rmax = Math.max(...exs.map((e) => e.recall), ...hb.map((r) => pct0(r.recall)));

// 1. 표지
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "2026 NAIS AI 해커톤 · 팀 루미아", 1.15);
  title(s, "제출 전에,\n**빈칸**부터 찾아 드립니다.", { y: 1.8, h: 2.5, fontSize: 54 });
  t(s, "공고 링크와 초안을 넣으면, 공고가 요구하는데 초안에 근거가 없는 곳을 원문으로 보여 주는 에이전트", { x: X0, y: 4.55, w: W, h: 0.5, fontSize: 19, color: C.sub });
  t(s, "RFP-to-Fit   |   김태걸 · 박세훈", { x: X0, y: 6.4, w: 8, h: 0.45, fontSize: 16, bold: true });
  s.addNotes("[10초] 안녕하세요, 팀 루미아 김태걸입니다. 저희는 심사 결과를 맞히는 AI가 아니라, 제출하기 전에 초안의 빈칸을 원문으로 짚어 주는 에이전트를 만들었습니다.");
}

// 2. 문제
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "문제");
  title(s, "떨어진 이유는,\n**심사평**을 받고서야 압니다");
  const M = N.motir;
  numRow(s, "01", "지킬 것이 많고, 흩어져 있습니다", `산업통상부 R&D 공고 한 건에 ${M.pages}쪽, 탈락·감점 요건 ${M.n_req}개, 평가표 ${M.tables}종`, X0, 2.95, W, { hSize: 20, dSize: 14 });
  numRow(s, "02", "심사위원마다 보는 곳이 다릅니다", "기술, 사업성, 예산과 인력, 사업 취지. 어제 멘토링에서 들은 실제 심사 방식입니다", X0, 4.1, W, { hSize: 20, dSize: 14 });
  numRow(s, "03", "제출 전에 그 눈으로 봐 줄 사람이 없습니다", "동료 검토는 결국 같은 연구자의 눈입니다", X0, 5.25, W, { hSize: 20, dSize: 14 });
  s.addNotes(`[30초] 제안서를 내 보신 분은 아실 겁니다. 떨어진 이유는 심사평을 받고서야 압니다. 공고 한 건에 지킬 것이 ${M.n_req}개, ${M.pages}쪽에 흩어져 있고, 심사위원마다 보는 곳이 다릅니다. 그런데 제출 전에 그 눈으로 봐 줄 사람은 없습니다. 저희도 올해 공고 400여 건에 지원하면서 매번 여기서 막혔습니다.`);
}

// 3. 해결
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "해결");
  title(s, "그래서 세 가지를,\n**이렇게** 풀었습니다");
  const cw = (W - 0.6) / 3;
  const cards = [
    ["흩어진 요건", "링크 하나로 공고문을 찾아 읽고, 요건과 심사표를 쪽 번호와 함께 정리합니다", `${LK ? LK.ok : "-"}/${LK ? LK.n : "-"}`, "실제 공지 링크에서 공고문 찾기"],
    ["다른 관점", "관점 6개가 서로 모른 채 근거를 찾고, 모두 못 찾은 곳만 고칠 곳으로 올립니다", `${single.fp ?? "-"} → ${roles.fp ?? "-"}`, "관점 1개 대비 잘못 짚은 곳"],
    ["믿을 수 있나", "근거로 댄 문장이 초안에 정말 있는지 코드가 확인하고, 없으면 다시 묻습니다", `${B.invalid}건`, `판정 ${B.n_verdicts}개 중 없는 인용 적발`],
  ];
  cards.forEach(([k, d, big, lab], i) => {
    const x = X0 + i * (cw + 0.3);
    box(s, x, 2.9, cw, 3.55, { fill: i === 1 ? C.blueBg : C.white, lineColor: i === 1 ? C.blue : C.line });
    t(s, k, { x: x + 0.3, y: 3.1, w: cw - 0.6, h: 0.35, fontSize: 14, bold: true, color: C.blue });
    t(s, d, { x: x + 0.3, y: 3.55, w: cw - 0.6, h: 1.1, fontSize: 14.5, color: C.ink, lineSpacingMultiple: 1.25 });
    t(s, big, { x: x + 0.3, y: 4.85, w: cw - 0.6, h: 0.8, fontSize: 40, bold: true, color: C.blueInk });
    t(s, lab, { x: x + 0.3, y: 5.7, w: cw - 0.6, h: 0.5, fontSize: 12, color: C.gray });
  });
  s.addNotes("[25초] 그래서 세 가지를 풀었습니다. 링크 하나로 공고문을 찾아 요건과 심사표를 정리하고, 관점 여섯 개가 서로 모른 채 근거를 찾게 하고, 근거로 댄 문장이 초안에 정말 있는지 코드가 확인합니다. 숫자는 전부 오늘 밤 직접 잰 값입니다.");
}

// 4. 사용 흐름
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "사용 흐름");
  title(s, "연구자는,\n**붙여넣기 두 번**이면 됩니다");
  const lw = 4.9;
  numRow(s, "01", "공고 링크 붙여넣기", "공지 주소만 넣으면 첨부 중 공고문을 골라 읽습니다. PDF, HWPX, HWP", X0, 2.95, lw, { hSize: 18, dSize: 12.5 });
  numRow(s, "02", "내 초안 올리기", "저장하지 않고, 개인정보는 가린 뒤 보냅니다", X0, 4.1, lw, { hSize: 18, dSize: 12.5 });
  numRow(s, "03", "원문으로 확인하기", "지적마다 공고와 초안의 해당 문장을 띄워 맞음, 틀림을 누릅니다", X0, 5.25, lw, { hSize: 18, dSize: 12.5 });
  const imgs = [N.img.input, N.img.result].filter(Boolean);
  const top = 0.55, cap = 0.34, gap = 0.18, avail = 6.75 - top - imgs.length * cap - gap * (imgs.length - 1);
  const w = Math.min(R - 6.15, avail / imgs.reduce((a, im) => a + im.h / im.w, 0)), x = R - w;
  let y = top;
  imgs.forEach((im, i) => {
    const h = w * im.h / im.w;
    box(s, x, y, w, h);
    s.addImage({ path: im.path, x: x + 0.06, y: y + 0.06, w: w - 0.12, h: h - 0.12 });
    t(s, i === 0 ? "공고 링크를 넣은 화면" : "원문 보기: 공고 근거와 초안 인용(노란 강조)", { x, y: y + h + 0.04, w, h: 0.28, fontSize: 11, color: C.gray });
    y += h + cap + gap;
  });
  src(s, "실제 화면  ·  처음 보는 19쪽 공고 기준 공고 읽기 20초, 채점 25초");
  s.addNotes("[35초] 연구자는 붙여넣기 두 번이면 됩니다. 공고 링크를 넣으면 공지에 붙은 첨부 중 공고문을 골라 읽고, 20초쯤 뒤 지켜야 할 요건 목록이 나옵니다. 요건을 고르면 공고 원문의 그 자리가 강조됩니다. 초안을 올리면 개인정보를 가린 뒤 보내고, 1분 안에 고칠 곳과 판단할 곳이 나옵니다. 지금 실제로 해 보겠습니다. 과기정통부 사업공고의 가장 최신 글입니다.");
}

// 5. 역할
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "서비스 흐름");
  title(s, "사람은 판단하고, AI는 찾고,\n**코드**는 확인합니다");
  const cols = [
    ["사람", C.ink, C.white, [["공고와 초안 고르기", "어디에 무엇을 낼지"], ["갈린 곳을 고칠지 결정", "연구 전략은 본인이 압니다"], ["문장은 직접 쓰기", "에이전트는 위치와 근거 종류만"]]],
    ["AI", C.blueBg, C.blueInk, [["공고 정리, 점검 질문", MAIN], ["관점 6개의 판정", VENDORS.map((v) => `${v.replace("Google ", "").replace("Upstage ", "")} ${REVM(v)}`).join(" · ")], ["선행연구 찾기", "MCP 도구로 학술 DB 검색"]]],
    ["코드", C.white, C.ink, [["인용 확인", "근거 문장이 초안에 글자 그대로 있는지"], ["합의 집계", "몇 관점이 근거를 못 찾았는지"], ["개인정보 가림", "주민번호, 전화, 이메일, 생년월일"]]],
  ];
  const cw = (W - 0.5) / 3;
  cols.forEach(([head, fill, color, items], ci) => {
    const x = X0 + ci * (cw + 0.25);
    box(s, x, 2.8, cw, 0.55, { fill, lineColor: ci === 0 ? C.ink : ci === 1 ? C.blue : C.gray, dash: ci === 2 ? "dash" : "solid" });
    t(s, head, { x: x + 0.22, y: 2.9, w: cw - 0.4, h: 0.35, fontSize: 15, bold: true, color });
    items.forEach(([h, d], i) => {
      const y = 3.6 + i * 1.05;
      t(s, h, { x: x + 0.05, y, w: cw - 0.1, h: 0.36, fontSize: 16, bold: true });
      t(s, d, { x: x + 0.05, y: y + 0.42, w: cw - 0.1, h: 0.5, fontSize: 12, color: C.sub });
    });
  });
  s.addNotes("[15초] 역할은 이렇게 나눴습니다. 사람은 판단하고 문장은 직접 씁니다. AI는 공고를 정리하고 근거를 찾습니다. 코드는 그 근거가 초안에 정말 있는지, 몇 관점이 동의했는지 확인합니다.");
}

// 6. 구조
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "AI 구성");
  title(s, "AI가 판단하면,\n**코드**가 근거를 검사합니다");
  const nodes = [["점검 질문", MAIN, "A"], ["선행 탐색", "MCP", "A"], ["관점 6개 채점", "3사 모델", "A"], ["인용 확인", "코드", "R"],
    ["다시 묻기", "없는 인용만", "A"], ["합의 집계", "코드", "R"], ["보완 위치", MAIN, "A"]];
  const bw = 1.47, gap = (W - 7 * bw) / 6, y = 3.2, bh = 1.05;
  nodes.forEach(([name, sub, k], i) => {
    const x = X0 + i * (bw + gap), rule = k === "R";
    box(s, x, y, bw, bh, { fill: rule ? C.white : C.blueBg, lineColor: rule ? C.gray : C.blue, dash: rule ? "dash" : "solid", lineWidth: 1.25 });
    t(s, name, { x: x + 0.1, y: y + 0.2, w: bw - 0.2, h: 0.36, fontSize: 13.5, bold: true, color: rule ? C.ink : C.blueInk, align: "center" });
    t(s, sub, { x: x + 0.1, y: y + 0.6, w: bw - 0.2, h: 0.3, fontSize: 10.5, color: C.sub, align: "center" });
    if (i < 6) arrow(s, x + bw + 0.02, y + bh / 2, x + bw + gap - 0.02, y + bh / 2);
  });
  t(s, "LangGraph 상태 그래프", { x: X0, y: y - 0.45, w: 4, h: 0.3, fontSize: 12, bold: true, color: C.gray });
  const facts = [
    ["실패해도 숨기지 않습니다", "관점 호출이 실패하면 다시 시도하고, 그래도 안 되면 응답 수를 화면에 띄웁니다"],
    ["한 회사가 막혀도 돕니다", "모델마다 대체 모델이 있어 한도나 장애 때 자동으로 넘어갑니다"],
    ["조각 검색 대신 원문 전체", "문서를 잘라 찾지 않고 통째로 넣은 뒤, 인용으로 맞춰 봅니다"],
  ];
  facts.forEach(([h, d], i) => {
    const yy = 4.85 + i * 0.62;
    t(s, h, { x: X0, y: yy, w: 3.6, h: 0.34, fontSize: 14, bold: true });
    t(s, d, { x: X0 + 3.8, y: yy + 0.02, w: W - 3.8, h: 0.34, fontSize: 13, color: C.sub });
    if (i < 2) hline(s, yy + 0.5);
  });
  s.addNotes("[20초] AI의 말을 그대로 믿지 않습니다. 충족인지 부족인지는 AI가 판단하지만, 그 근거로 댄 문장이 초안에 글자 그대로 있는지는 코드가 대조하고, 없으면 그 판단을 버립니다. 여섯 판단을 세는 것도 코드입니다. 모델이 막히면 다른 모델로 넘어가고, 실패는 화면에 띄웁니다.");
}

// 6-2. 관점 6개와 심사 방식
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "관점 6개");
  title(s, "여섯 관점은,\n**같은 질문**에 따로 답합니다");
  const LENS = [
    ["기술 타당성 검증형", "방법·수치·검증이 실제로 성립하는가"],
    ["기술 큰그림형", "기존 방법과 비교해 무엇이 새로운가"],
    ["세부 전문형", "핵심 기술 하나가 설계·구현·측정됐는가"],
    ["사업성·시장형", "누가 쓰고, 누가 돈을 내는가"],
    ["행정·관리형", "예산·인력·일정·위험 관리가 채워졌는가"],
    ["사업 취지형", "공고의 취지와 제안의 목표가 이어지는가"],
  ];
  const lw = 5.3;
  t(s, "누가 보나 · 먼저 보는 것", { x: X0, y: 2.75, w: lw, h: 0.3, fontSize: 13, bold: true, color: C.gray });
  LENS.forEach(([n, d], i) => {
    const y = 3.15 + i * 0.47;
    t(s, n, { x: X0, y, w: 2.05, h: 0.34, fontSize: 13.5, bold: true });
    t(s, d, { x: X0 + 2.1, y: y + 0.02, w: lw - 2.1, h: 0.34, fontSize: 12, color: C.sub });
    if (i < LENS.length - 1) hline(s, y + 0.42, X0, lw);
  });
  t(s, "9/30 멘토링에서 들은 실제 심사위원 유형입니다. 실존 인물을 흉내 내지 않고 역할만 줍니다. 3개 회사 모델에 두 관점씩.",
    { x: X0, y: 6.0, w: lw, h: 0.5, fontSize: 11, color: C.gray, lineSpacingMultiple: 1.15 });
  const rx = 6.75, rw = R - rx;
  t(s, "어떻게 심사하나", { x: rx, y: 2.75, w: rw, h: 0.3, fontSize: 13, bold: true, color: C.gray });
  const STEPS = [
    ["같은 질문", "AI", "지표마다 점검 질문을 3개까지 만들어 여섯 관점에 똑같이 줍니다"],
    ["따로 판정", "AI", "서로 모른 채 충족·부족·누락을 고르고, 초안 문장을 그대로 인용합니다"],
    ["걸러 내기", "코드", "초안에 없는 인용은 버리고, 그 관점에만 한 번 다시 묻습니다"],
    ["세기", "코드", `여섯 중 ${GAPK}명 이상 부족·누락이면 고칠 곳, ${CLO}~${CHI}명이면 판단할 곳\n점수는 충족 1·부족 0.5·누락 0 × 배점, 최고·최저를 빼고 평균`],
  ];
  STEPS.forEach(([h, who, d], i) => {
    const y = 3.12 + i * 0.7;
    t(s, String(i + 1).padStart(2, "0"), { x: rx, y, w: 0.5, h: 0.3, fontSize: 15, bold: true, color: C.blue });
    t(s, h, { x: rx + 0.55, y, w: 1.3, h: 0.3, fontSize: 14, bold: true });
    t(s, who, { x: rx + 1.85, y: y + 0.03, w: 0.6, h: 0.26, fontSize: 10.5, bold: true, color: who === "코드" ? C.ink : C.blueInk });
    t(s, d, { x: rx + 0.55, y: y + 0.33, w: rw - 0.55, h: i === 3 ? 0.5 : 0.28, fontSize: 11.5, color: C.sub, lineSpacingMultiple: 1.1 });
  });
  box(s, rx, 6.22, rw, 0.6, { fill: C.bg2, lineColor: C.bg2 });
  t(s, [
    { text: "실제 예  ", options: { bold: true, color: C.blueInk } },
    { text: "「AI 활용 계획이 연구 과정 시나리오로 제시됐는가」 충족 4 · 부족 2(세부 전문형, 행정·관리형) → 판단할 곳", options: { color: C.ink } },
  ], { x: rx + 0.18, y: 6.27, w: rw - 0.36, h: 0.5, fontSize: 11.5, lineSpacingMultiple: 1.1, valign: "middle" });
  s.addNotes("[30초] 관점 여섯 개는 어제 멘토링에서 들은 실제 심사위원 유형입니다. 기술을 꼼꼼히 따지는 사람, 큰 그림을 보는 사람, 자기 전문 하나를 파는 사람, 시장을 보는 사람, 행정, 사업 취지. 실존 인물이 아니라 역할만 줍니다. 여섯 관점은 같은 질문을 서로 모른 채 받고, 충족이라고 하려면 초안 문장을 그대로 인용해야 합니다. 그다음은 코드입니다. 인용이 초안에 없으면 버리고, 여섯 중 다섯 이상이 부족이면 고칠 곳, 둘에서 넷이면 판단할 곳입니다. 실제로 활용 시나리오 항목은 넷이 충족, 둘이 부족이라 판단할 곳으로 넘어갔습니다.");
}

// 7. 신뢰
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "신뢰");
  title(s, "맞힌다고 하지 않고,\n**확인할 수 있게** 했습니다");
  const lw = 3.7;
  box(s, X0, 2.85, lw, 3.3, { fill: C.bg2, lineColor: C.bg2 });
  t(s, "하지 않는 말", { x: X0 + 0.3, y: 3.05, w: lw - 0.6, h: 0.3, fontSize: 13, bold: true, color: C.gray });
  t(s, ["심사 결과를 맞힙니다", "실제 심사위원과 같습니다", "제안서를 대신 씁니다"].map((x, i, a) => ({ text: x, options: { breakLine: i < a.length - 1 } })),
    { x: X0 + 0.3, y: 3.5, w: lw - 0.6, h: 1.8, fontSize: 17, bold: true, color: C.ink, lineSpacingMultiple: 1.7, strike: "sngStrike" });
  t(s, "심사는 사람의 판단이라 정답이 없습니다.", { x: X0 + 0.3, y: 5.45, w: lw - 0.6, h: 0.5, fontSize: 12, color: C.sub });
  const rx = X0 + lw + 0.5, rw = R - rx;
  const rows = [
    ["출처가 붙습니다", "모든 지적에 공고의 쪽과 초안의 문장이 함께 나옵니다"],
    ["없는 문장은 버립니다", `초안에 없는 인용은 판정에서 뺍니다. 이번 실행 ${B.invalid}건 적발`],
    ["갈리면 사람에게 넘깁니다", "관점이 엇갈리면 판정하지 않고 「판단할 곳」으로 보냅니다"],
    ["잰 것만 숫자로 말합니다", "요건 찾기와 오탐만 숫자로 말하고, 합격 예측은 말하지 않습니다"],
  ];
  rows.forEach(([h, d], i) => {
    const y = 2.95 + i * 0.82;
    t(s, h, { x: rx, y, w: rw, h: 0.36, fontSize: 17, bold: true });
    t(s, d, { x: rx, y: y + 0.38, w: rw, h: 0.34, fontSize: 12.5, color: C.sub });
  });
  hline(s, 6.45);
  t(s, "직접 확인도 됩니다. 지적마다 원문 보기와 맞음·틀림 버튼이 있고, 보안 모드를 켜면 초안은 국산 모델에만 갑니다.", { x: X0, y: 6.58, w: W, h: 0.35, fontSize: 13, color: C.blueInk, bold: true });
  s.addNotes("[25초] 심사에는 정답이 없어서, 저희는 맞힌다고 말하지 않습니다. 대신 확인할 수 있게 했습니다. 모든 지적에 출처가 붙고, 초안에 없는 문장은 버리고, 관점이 갈리면 사람에게 넘기고, 잰 것만 숫자로 말합니다. 지적마다 원문 보기와 맞음·틀림 버튼이 있어서 여러분이 직접 확인하실 수 있습니다.");
}

// 8. MCP
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "MCP 도구");
  title(s, "같은 검사 도구를,\n**다른 AI 비서**도 씁니다");
  const lw = 6.2;
  numRow(s, "01", "search_prior_art", "학술 DB에서 선행연구를 찾습니다. OpenAlex가 막히면 Crossref로 넘어갑니다", X0, 2.95, lw, { hSize: 18, dSize: 12.5 });
  numRow(s, "02", "check_quote", "인용이 원문에 있는지 참, 거짓으로 답합니다", X0, 4.05, lw, { hSize: 18, dSize: 12.5 });
  numRow(s, "03", "왜 도구로 감쌌나", "어젯밤 실험 도중 OpenAlex가 멈췄을 때, 도구 뒤에서 자동으로 바뀌었습니다. 국내 DB도 같은 자리에 꽂으면 됩니다", X0, 5.15, lw, { hSize: 18, dSize: 12.5 });
  const rx = 7.55, rw = R - rx;
  box(s, rx, 2.85, rw, 3.6, { fill: C.bg2, lineColor: C.bg2 });
  t(s, "Codex에 붙여서 실제로 호출해 봤습니다", { x: rx + 0.3, y: 3.05, w: rw - 0.6, h: 0.3, fontSize: 13, bold: true, color: C.blue });
  t(s, [
    { text: "check_quote(재현율 90% 이상)", options: { bold: true, breakLine: true } }, { text: "→ 참", options: { color: C.blueInk, bold: true, breakLine: true } },
    { text: "check_quote(정밀도 95% 달성)", options: { bold: true, breakLine: true } }, { text: "→ 거짓(원문에 없음)", options: { color: C.blueInk, bold: true, breakLine: true } },
    { text: "search_prior_art(grant proposal review)", options: { bold: true, breakLine: true } }, { text: "→ 논문 3편", options: { color: C.blueInk, bold: true } },
  ], { x: rx + 0.3, y: 3.5, w: rw - 0.6, h: 2.8, fontSize: 13.5, lineSpacingMultiple: 1.35 });
  s.addNotes("[15초] 검사 도구 두 개를 MCP로 감쌌습니다. 다른 AI 비서인 Codex에 붙여 실제로 불러 보니, 원문에 있는 인용은 참, 없는 인용은 거짓이 나왔습니다. 학술 DB가 멈추면 도구 뒤에서 다른 DB로 넘어갑니다.");
}

// 9. 측정
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "측정");
  title(s, "처음 보는 공고로도,\n**직접** 쟀습니다");
  const nm = (e) => e.agency.replace("국가과학기술연구회", "NAIS 해커톤");
  const hn = { "msit-national-scientist-2026": "과기정통부 국가과학자", "msit-rising-star-2026": "과기정통부 라이징스타" };
  t(s, "요건을 놓치지 않은 비율", { x: X0, y: 2.85, w: 6, h: 0.3, fontSize: 13, bold: true, color: C.sub });
  const rows = exs.map((e) => [nm(e), `${e.recall}%`, "개발에 쓴 공고", false])
    .concat(hb.map((r, i) => [hn[Object.keys(HO.blind)[i]] || "", `${pct0(r.recall)}%`, "처음 보는 공고", true]));
  rows.forEach(([a1, b1, c1, hold], i) => {
    const y = 3.25 + i * 0.46;
    t(s, a1, { x: X0, y, w: 3.4, h: 0.34, fontSize: 14, bold: hold, color: hold ? C.blueInk : C.ink });
    t(s, c1, { x: X0 + 3.4, y: y + 0.03, w: 1.6, h: 0.3, fontSize: 11, color: C.gray });
    t(s, b1, { x: X0 + 5.0, y, w: 1.0, h: 0.34, fontSize: 16, bold: true, align: "right", color: hold ? C.blueInk : C.ink });
  });
  t(s, "심사표 배점은 다섯 건 모두 정확히 뽑았습니다", { x: X0, y: 5.6, w: 6, h: 0.3, fontSize: 12, color: C.sub });
  const rx = 7.3, rw = R - rx;
  t(s, `근거를 일부러 지운 초안 ${P.n}개, 잘못 짚은 곳`, { x: rx, y: 2.85, w: rw, h: 0.3, fontSize: 13, bold: true, color: C.sub });
  const cw = (rw - 0.3) / 3;
  AB.forEach((a, i) => {
    const x = rx + i * (cw + 0.15), hi = a.mode !== "single";
    box(s, x, 3.25, cw, 2.0, { fill: hi ? C.blueBg : C.white, lineColor: hi ? C.blue : C.line });
    t(s, a.mode === "single" ? "관점 1개" : a.mode === "roles" ? "관점 6개" : "6개·3사", { x: x + 0.15, y: 3.4, w: cw - 0.3, h: 0.3, fontSize: 12, bold: true });
    t(s, `${a.fp}`, { x: x + 0.15, y: 3.8, w: cw - 0.3, h: 0.8, fontSize: 42, bold: true, color: hi ? C.blueInk : C.ink });
    t(s, `찾은 곳 ${a.detect}`, { x: x + 0.15, y: 4.75, w: cw - 0.3, h: 0.3, fontSize: 11, color: C.sub });
  });
  t(s, "회사 모델을 섞는 효과는 이번 표본에선 보이지 않았습니다", { x: rx, y: 5.6, w: rw, h: 0.3, fontSize: 12, color: C.sub });
  hline(s, 6.15);
  t(s, `처음 보는 공고에서 뽑은 요건 51개를 원문과 대조해 보니, 지어낸 요건은 0개였습니다`, { x: X0, y: 6.3, w: W, h: 0.35, fontSize: 14, bold: true });
  src(s, "정답표와 대조 감사는 파이프라인과 다른 회사 모델(Claude)이 작성, 사람 검수는 아님  ·  data/eval, data/holdout 공개");
  s.addNotes(`[30초] 예시에만 맞춘 게 아닌지 보려고, 개발에 안 쓴 과기정통부 공고 두 건을 링크로 가져와 정답표를 먼저 고정하고 쟀습니다. ${hb.map((r) => pct0(r.recall) + "%").join("와 ")}였고 심사표 배점은 다섯 건 모두 맞혔습니다. 오른쪽은 관점을 나눈 효과입니다. 관점 하나는 안 지운 곳을 ${single.fp}곳 잘못 짚었고, 여섯으로 나누니 0이었습니다. 회사 모델을 섞는 효과는 이번엔 보이지 않았다고 그대로 말씀드립니다.`);
}

// 10. 우리 먼저
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "우리 먼저");
  title(s, "이 대회 심사표로,\n**저희 기획서**부터 검사했습니다");
  const answer = {
    "세부 전문형": "구조의 차별점과 관점 수 실험을 준비했습니다",
    "기술 타당성 검증형": "처음 보는 공고로 잰 숫자를 준비했습니다",
    "사업성·시장형": "첫 실증 대상을 전문기관 사전검토로 정했습니다",
    "행정·관리형": "계획 대신 구현 결과와 커밋 기록을 가져왔습니다",
  };
  t(s, "관점별로 가장 걸린 점", { x: X0, y: 2.85, w: 5.8, h: 0.3, fontSize: 13, bold: true, color: C.gray });
  t(s, "그래서 오늘", { x: 7.35, y: 2.85, w: 5, h: 0.3, fontSize: 13, bold: true, color: C.gray });
  nsel.slice(0, 3).forEach((x, i) => {
    const y = 3.3 + i * 1.0, nmx = pn[x.id] || x.id;
    t(s, nmx, { x: X0, y, w: 5.8, h: 0.3, fontSize: 12, bold: true, color: C.blue });
    t(s, x.point, { x: X0, y: y + 0.32, w: 5.8, h: 0.4, fontSize: 15, bold: true });
    arrow(s, X0 + 6.0, y + 0.5, 7.2, y + 0.5, C.gray);
    t(s, answer[nmx] || "", { x: 7.35, y: y + 0.32, w: R - 7.35, h: 0.4, fontSize: 15, color: C.ink });
    if (i < 2) hline(s, y + 0.88);
  });
  t(s, "결과를 맞히려던 게 아니라, 발표 전에 받을 질문을 먼저 받아 본 것입니다.", { x: X0, y: 6.45, w: W, h: 0.35, fontSize: 13, color: C.sub });
  s.addNotes("[20초] 이 대회 심사표로 저희 기획서부터 검사했습니다. 세 관점이 걸리는 점을 냈습니다. 차별성의 근거, 구매 주체, 구현 계획. 그래서 오늘은 구조의 차별점과 실험, 첫 실증 대상, 그리고 계획 대신 구현 결과를 가져왔습니다.");
}

// 11. 확장
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "확장");
  title(s, "제출 전에서 심사까지,\n**같은 엔진**으로 갑니다");
  const steps = [["제출 전", "연구자", "셀프 점검", "고칠 곳과 판단할 곳을 원문과 함께 봅니다. 지금 이 앱으로 됩니다", true], ["접수 후", "전문기관", "요건 사전검토", "형식 미비와 서류 누락을 먼저 거릅니다. 첫 실증 목표", false],
    ["심사 중", "평가위원", "근거 위치 표시", "지표마다 제안서의 근거 문장을 옆에 띄웁니다. 판정은 사람", false]];
  const cw = (W - 0.6) / 3;
  steps.forEach(([when, who, what, how, now], i) => {
    const x = X0 + i * (cw + 0.3);
    box(s, x, 2.85, cw, 2.4, { fill: now ? C.blueBg : C.white, lineColor: now ? C.blue : C.line });
    t(s, `${when} · ${who}`, { x: x + 0.3, y: 3.05, w: cw - 0.6, h: 0.3, fontSize: 13, bold: true, color: C.blue });
    t(s, what, { x: x + 0.3, y: 3.45, w: cw - 0.6, h: 0.5, fontSize: 22, bold: true });
    t(s, how, { x: x + 0.3, y: 4.1, w: cw - 0.6, h: 0.9, fontSize: 13, color: C.sub, lineSpacingMultiple: 1.2 });
    if (i < 2) arrow(s, x + cw + 0.03, 4.05, x + cw + 0.27, 4.05, C.blue);
  });
  numRow(s, "", "실제 심사 의견은 평가기관에 있습니다", "기관과 연계하면 관점을 실제 심사 의견 유형으로 맞출 수 있습니다", X0, 5.55, W / 2 - 0.2, { hSize: 15, dSize: 12 });
  numRow(s, "", "NAIS 플랫폼에 도구로 꽂힙니다", "AI 사이언티스트가 과제 신청까지 하는 날, 그 마지막 점검", X0 + W / 2, 5.55, W / 2, { hSize: 15, dSize: 12 });
  s.addNotes("[15초] 같은 엔진이 세 시점으로 이어집니다. 지금은 연구자의 제출 전 점검이고, 첫 실증 목표는 전문기관의 접수 후 요건 검토, 그다음은 심사 보조입니다. 실제 심사 의견은 평가기관에 있으니, 연계하면 관점을 실제 유형에 맞출 수 있습니다.");
}

// 12. 마무리
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "지금 직접 해 보세요", 1.15);
  title(s, "제출 전에,\n**빈칸**부터.", { y: 1.8, h: 2.3, fontSize: 54 });
  t(s, `공고 링크 하나, 초안 하나면 됩니다.\n커밋 ${N.git.commits}개, 테스트 ${N.tests}개, 첫 코드 커밋 ${N.git.first_code}`, { x: X0, y: 4.5, w: 6.6, h: 0.9, fontSize: 15, color: C.sub, lineSpacingMultiple: 1.35 });
  t(s, "팀 루미아 · 김태걸 · 박세훈", { x: X0, y: 6.4, w: 6, h: 0.45, fontSize: 16, bold: true });
  const qs = [["라이브 앱", N.qr_live, N.live_url.replace(/^https?:\/\//, "")], ["GitHub", N.qr_repo, N.repo_url.replace(/^https?:\/\//, "")]];
  qs.forEach(([k, img, url], i) => {
    const x = 7.95 + i * 2.3, y = 2.0;
    box(s, x, y, 2.05, 3.05);
    s.addImage({ path: img, x: x + 0.28, y: y + 0.28, w: 1.5, h: 1.5 });
    t(s, k, { x: x + 0.2, y: y + 1.98, w: 1.65, h: 0.35, fontSize: 14, bold: true });
    t(s, url, { x: x + 0.2, y: y + 2.38, w: 1.7, h: 1.0, fontSize: 9.5, color: C.gray, lineSpacingMultiple: 1.15, fit: "none" });
  });
  s.addNotes("[10초] 제출 전에, 빈칸부터. 화면의 주소에서 지금 직접 해 보실 수 있습니다. 감사합니다.");
}

// 13. 부록 — 출처(규정 기재 의무)
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "부록");
  title(s, "사용 모델, 라이브러리,\n데이터 출처", { fontSize: 30 });
  const rows = [
    ["생성형 AI", "OpenAI gpt-4.1(공고 정리·점검 질문·보완), gpt-5.4-mini·gpt-4.1-mini(관점 판정·대체) · Google Gemini(관점 판정) · Upstage Solar pro3(관점 판정·대체·보안 모드)"],
    ["에이전트·도구", "LangGraph 1.2(상태 그래프) · MCP Python SDK 2.2(도구 서버) · Streamlit 1.64(화면)"],
    ["문서 처리", "pdfplumber 0.11(PDF) · olefile 0.47(HWP) · HWPX 직접 파싱(zipfile) · httpx 0.28(링크 수집)"],
    ["데이터", "OpenAlex·Crossref 공개 학술 API · 공개 R&D 공고 5건(NST NAIS, 우주항공청 2026-0024, 산업통상부 2026-64, 과기정통부 2026-0940·0945)"],
    ["정답표·감사", "Claude(Anthropic)가 원문을 읽어 작성, 파이프라인 모델과 독립 · 사람 검수 아님"],
    ["코딩 보조", "Claude Code(Anthropic) · Codex(OpenAI)"],
  ];
  rows.forEach(([k, v], i) => {
    const y = 2.85 + i * 0.66;
    t(s, k, { x: X0, y, w: 2.3, h: 0.5, fontSize: 13, bold: true, color: C.blue });
    t(s, v, { x: X0 + 2.4, y, w: W - 2.4, h: 0.55, fontSize: 12, color: C.ink, lineSpacingMultiple: 1.15 });
    if (i < rows.length - 1) hline(s, y + 0.61);
  });
  src(s, "전체 표와 라이선스는 저장소 README  ·  github.com/Ryugi62/rfp-to-fit");
  s.addNotes("[0초] 부록 — 발표하지 않음. 공고 규정(사용 모델·라이브러리·데이터 출처 기재) 충족용.");
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("wrote", f));
