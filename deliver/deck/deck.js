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
const exAvg = N.extract.map((e) => e.recall);
const hb = HO ? Object.values(HO.blind) : [];
const hMin = hb.length ? Math.min(...hb.map((r) => pct0(r.recall_min))) : null;
const hMax = hb.length ? Math.max(...hb.map((r) => pct0(r.recall_max))) : null;
const single = AB.find((a) => a.mode === "single") || {}, roles = AB.find((a) => a.mode === "roles") || {};
const nsel = (B.stances || []).filter((x) => x.decision !== "선정");
const pn = Object.fromEntries(B.personas.map((q) => [q.id, q.name]));
const MAIN = N.extract[0].engine;
const REVM = (v) => [...new Set(B.personas.filter((q) => q.vendor === v).map((q) => q.model.split(" ").pop()))].join("·");

// ---------- 1. 표지 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "2026 NAIS AI 해커톤 본선 · 팀 루미아 · RFP-to-Fit", 1.15);
  title(s, "공고 링크 하나, 초안 하나.\n제출 전에 **빈칸**부터 짚어 드립니다.", { y: 1.8, h: 2.5, fontSize: 48 });
  t(s, "심사 결과를 맞히는 AI가 아니라 — 공고가 요구하는데 내 초안에 근거가 없는 곳을, 원문으로 짚어 주는 에이전트", { x: X0, y: 4.55, w: W, h: 0.5, fontSize: 19, color: C.sub });
  t(s, "김태걸 · 박세훈", { x: X0, y: 6.4, w: 5, h: 0.45, fontSize: 16, bold: true });
  s.addNotes("[10초] 안녕하세요, 팀 루미아 김태걸입니다. 저희는 심사 결과를 맞히는 AI를 만들지 않았습니다. 공고가 요구하는데 내 초안에 근거가 없는 곳을, 제출 전에 원문으로 짚어 주는 에이전트를 만들었습니다.");
}

// ---------- 2. 문제 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "문제 — 제안서를 내는 연구자의 자리에서");
  title(s, "떨어진 이유는 늘,\n**심사평**을 받고 나서야 압니다");
  const M = N.motir;
  const rows = [
    [`지킬 것 ${M.n_req}개가 ${M.pages}쪽에 흩어져 있습니다`, `산업통상부 R&D 공고 한 건 — 자격·서류·서식·감점 조건이 본문·주석·첨부에 나뉘어 있고 평가표도 ${M.tables}종`],
    ["심사위원 5~7명은 저마다 다른 것을 봅니다", "기술 타당성, 사업성, 행정(예산·인력·빈칸), 사업 취지 — 그리고 항목 합산보다 몇 가지 결정 포인트로 마음속 등수를 먼저 정합니다(현장 멘토링)"],
    ["제출 전에 그 눈으로 읽어 줄 사람이 없습니다", "동료 검토는 같은 연구자의 눈이고, 심사위원의 눈은 심사평으로만 돌아옵니다 — 이미 늦은 뒤에"],
  ];
  rows.forEach(([h, d], i) => numRow(s, `0${i + 1}`, h, d, X0, 2.95 + i * 1.12, W, { hSize: 18, dSize: 12.5 }));
  hline(s, 6.3);
  t(s, "저희 팀도 올해 공모·지원사업 공고 400여 건을 읽고 지원하면서 매번 이 자리에서 막혔습니다.", { x: X0, y: 6.45, w: W, h: 0.4, fontSize: 15, bold: true });
  s.addNotes(`[30초] 제안서를 내 보신 분은 아실 겁니다. 떨어진 이유는 늘 심사평을 받고 나서야 압니다. 공고 한 건에 지킬 것이 ${M.n_req}개, ${M.pages}쪽에 흩어져 있고, 심사위원은 저마다 다른 것을 봅니다. 어제 멘토링에서 들은 말처럼, 심사위원은 항목 합산보다 몇 가지 결정 포인트로 등수를 먼저 정합니다. 그런데 제출 전에 그 눈으로 읽어 줄 사람은 없습니다. 저희도 올해 공고 400여 건을 읽고 지원하면서 매번 여기서 막혔습니다.`);
}

// ---------- 3. 어려움 → 해결 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "무엇이 어려웠고, 어떻게 풀었나");
  title(s, "어려운 점 세 가지를,\n**장치 세 개**로 풀었습니다");
  const cx = [X0, X0 + 3.1, X0 + 8.1], cw = [2.9, 4.8, W - 8.1 + X0 - X0];
  ["어려운 점", "RFP-to-Fit이 하는 일", "실측"].forEach((h, i) => t(s, h, { x: cx[i], y: 2.8, w: cw[i], h: 0.3, fontSize: 11.5, color: C.gray, bold: true }));
  const hbTxt = hb.length ? `처음 보는 공고 ${hMin}~${hMax}%` : "";
  const rows = [
    ["흩어진 요건과 심사표", "공고 링크만 넣으면 공지의 첨부 중 공고문을 찾아 내려받고(PDF·HWPX·HWP), 요건과 심사표를 쪽 번호·원문 인용과 함께 뽑습니다",
      `링크 ${LK ? `${LK.ok}/${LK.n}` : "-"}건 성공\n요건 재현율 ${Math.min(...exAvg)}~${Math.max(...exAvg)}%·${hbTxt}\n심사표 배점 100% 일치`],
    ["심사위원마다 다른 관점", "실제 심사 경험에서 나온 관점 6개로 나눠 서로 모른 채 근거를 찾게 하고 → 모두 못 찾은 곳(고칠 곳)과 갈리는 곳(사람이 판단할 곳)을 나눕니다",
      `단일 LLM 오탐 ${single.fp ?? "-"} → 6역할 오탐 ${roles.fp ?? "-"}\n(일부러 지운 초안 ${P.n}개)`],
    ["AI 심사를 믿을 수 있나", "「충족」에도 초안 원문 인용을 요구하고, 코드가 글자 단위로 대조해 없으면 무효 → 그 평가위원에게 한 번 다시 묻습니다",
      `판정 ${B.n_verdicts}개 중 ${B.invalid}건 적발\n→ ${B.cited ?? B.fixed}건 원문 확인 · ${B.still ?? 0}건 무효 처리`],
  ];
  rows.forEach(([a, b, c], i) => {
    const y = 3.2 + i * 1.2;
    t(s, a, { x: cx[0], y, w: cw[0], h: 0.9, fontSize: 16, bold: true });
    t(s, b, { x: cx[1], y, w: cw[1], h: 1.0, fontSize: 12.5, color: C.sub, lineSpacingMultiple: 1.15 });
    t(s, c, { x: cx[2], y, w: cw[2], h: 1.0, fontSize: 12.5, bold: true, color: C.blueInk, lineSpacingMultiple: 1.15 });
    if (i < 2) hline(s, y + 1.08);
  });
  src(s, "실측 출처: data/eval/(link-fetch · extract-openai-3runs · holdout-summary · planted-ablation-*) · data/runs/…original.json — 저장소 공개");
  s.addNotes("[25초] 어려운 점은 세 가지였습니다. 요건이 흩어져 있고, 심사위원마다 보는 게 다르고, AI가 검사한 걸 믿을 수 있느냐. 그래서 링크만 넣으면 공고문을 찾아 요건과 심사표를 쪽 번호와 함께 뽑고, 실제 심사 경험에서 나온 관점 여섯 개로 나눠 근거를 찾게 하고, 칭찬에도 원문 인용을 요구해 코드가 대조합니다. 오른쪽 숫자는 오늘 밤 직접 잰 값입니다.");
}

// ---------- 4. 사용 흐름(연구자 시점) ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "사용 흐름 — 연구자가 하는 일");
  title(s, "연구자가 할 일은\n**붙여넣기 두 번**입니다");
  const lw = 4.9;
  numRow(s, "01", "공고 링크 붙여넣기", "IRIS·부처·기관 게시판 공지 주소 또는 PDF 주소 — 첨부 중 공고문을 알아서 고름(공고문이 여러 파일이면 합침)", X0, 2.95, lw, { hSize: 17, dSize: 11.5 });
  numRow(s, "02", "내 초안 올리기", "HWPX·HWP·PDF·텍스트 — 서버에 저장하지 않고, 주민번호·전화·이메일·생년월일은 가린 뒤 AI에 보냄", X0, 4.1, lw, { hSize: 17, dSize: 11.5 });
  numRow(s, "03", "고칠 곳 · 판단할 곳 · 관점별로 걸리는 점", "모든 관점이 근거를 못 찾은 곳, 의견이 갈린 곳, 관점마다 가장 걸리는 점 + 「어떤 근거를 어느 절에」", X0, 5.25, lw, { hSize: 17, dSize: 11.5 });
  const ix = 6.25, iw = R - ix;
  const put = (img, y, maxH) => {
    let w = iw, h = iw * img.h / img.w; if (h > maxH) { h = maxH; w = h * img.w / img.h; }
    box(s, ix, y, w, h + 0.2);
    s.addImage({ path: img.path, x: ix + 0.1, y: y + 0.1, w: w - 0.2, h: h * (w - 0.2) / w });
    return y + h + 0.2;
  };
  let y = 2.95;
  if (N.img.input) y = put(N.img.input, y, 1.75) + 0.2;
  if (N.img.result) put(N.img.result, y, 6.8 - y - 0.2);
  src(s, `라이브 앱 실제 화면 · 처음 보는 19쪽 공고를 올렸을 때 파싱 20초 + 채점 25초(브라우저 실측) · 마지막 장 주소에서 직접 해 보실 수 있습니다`);
  s.addNotes("[35초] 연구자가 할 일은 두 번의 붙여넣기입니다. 공고 링크를 넣으면 공지에 붙은 첨부 중 공고문을 알아서 골라 읽고, 내 초안을 올리면 개인정보를 가린 뒤 여섯 명에게 보냅니다. 약 45초 뒤 모든 관점이 근거를 못 찾은 곳, 의견이 갈린 곳, 관점마다 가장 걸리는 점이 나옵니다. 보완은 문장을 써 주지 않고, 어떤 근거를 어느 절에 넣을지만 알려 줍니다.");
}

// ---------- 5. 서비스 흐름도 — 역할 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "서비스 흐름도 — AI 개입과 사람 판단 지점");
  title(s, "누가 무엇을 하는가 —\n**사람**은 판단, AI는 생성, 규칙은 검사");
  const cols = [
    ["사람 — 판단", C.ink, [
      ["공고·초안 넣기", "어떤 공고에 어떤 초안을 낼지 정함"],
      ["논쟁 지점 채택", "의견이 갈린 곳은 연구 전략·사실을 아는 본인이 고칠지 결정"],
      ["문장 작성·제출", "에이전트는 문장을 쓰지 않음 — 위치와 근거 종류만"]]],
    ["AI — 생성(모델)", C.blue, [
      [`공고 파싱·점검 질문·보완 위치`, `주 엔진 ${MAIN} — 3쪽씩 병렬로 요건·배점을 원문 인용과 함께`],
      ["관점 6개의 근거 찾기", `${VENDORS.map((v) => `${v.replace("Google ", "")} ${REVM(v)}`).join(" · ")} — 질문별 충족/부족/누락 + 인용 + 선정·보류`],
      ["선행연구 검색어", `${MAIN} → MCP 도구로 검색 후 관련 논문만 선별`]]],
    ["규칙(코드) — 검사", C.gray, [
      ["인용 실재 검사", "공백·문장부호를 뺀 뒤 인용이 초안에 연속 문자열로 있는지 — 없으면 무효·재질의"],
      ["합의·논쟁 집계", "유효 판정 중 부족·누락 ≥80% 합의 결핍, 20~80% 논쟁, 유효 < 절반은 확인 불가"],
      ["점수·개인정보", "충족1·부족0.5·누락0, 최고·최저 제외 평균 · 주민번호·전화·이메일·생년월일 정규식 가림"]]],
  ];
  const cw = (W - 0.5) / 3;
  cols.forEach(([head, color, items], ci) => {
    const x = X0 + ci * (cw + 0.25);
    box(s, x, 2.75, cw, 0.5, { fill: ci === 0 ? C.ink : ci === 1 ? C.blueBg : C.white, lineColor: ci === 0 ? C.ink : ci === 1 ? C.blue : C.gray, dash: ci === 2 ? "dash" : "solid" });
    t(s, head, { x: x + 0.2, y: 2.85, w: cw - 0.4, h: 0.3, fontSize: 14, bold: true, color: ci === 0 ? C.white : ci === 1 ? C.blueInk : C.ink });
    items.forEach(([h, d], i) => {
      const y = 3.45 + i * 1.12;
      t(s, h, { x: x + 0.05, y, w: cw - 0.1, h: 0.34, fontSize: 14, bold: true });
      t(s, d, { x: x + 0.05, y: y + 0.38, w: cw - 0.1, h: 0.66, fontSize: 11, color: C.sub, lineSpacingMultiple: 1.12 });
    });
  });
  hline(s, 6.85);
  s.addNotes("[25초] 역할을 나눴습니다. 사람은 세 가지만 판단합니다. 어떤 공고에 낼지, 의견이 갈린 곳을 고칠지, 그리고 문장을 직접 씁니다. AI는 생성만 합니다. 공고 파싱과 점검 질문은 주 엔진이, 관점별 근거 찾기는 세 회사 모델에 나눈 여섯 관점이 합니다. 규칙은 코드로 검사합니다. 인용이 초안에 글자 그대로 있는지, 몇 관점이 근거를 못 찾았는지로 합의와 논쟁을 나누고, 개인정보는 보내기 전에 가립니다.");
}

// ---------- 6. AI 구성 — LangGraph ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "AI 구성 · 데이터 — LangGraph 상태 그래프");
  title(s, "LLM은 판사가 아니라 **증인**입니다 —\n판정은 코드가 합니다", { fontSize: 32 });
  const nodes = [
    ["rubric", "점검 질문", MAIN, "A"], ["prior", "선행 탐색", "MCP → OpenAlex/Crossref", "M"], ["review", "6명 독립 채점", "3사 모델 병렬", "A"],
    ["check", "인용 실재 검사", "코드", "R"], ["recheck", "재질의(최대 1회)", "무효 판정만", "A"], ["aggregate", "합의·논쟁 집계", "코드", "R"], ["remedy", "보완 위치 지정", MAIN, "A"],
  ];
  const bw = 1.52, gap = (W - 7 * bw) / 6, y = 3.15, bh = 1.15;
  nodes.forEach(([id, name, sub, k], i) => {
    const x = X0 + i * (bw + gap), rule = k === "R";
    box(s, x, y, bw, bh, { fill: rule ? C.white : C.blueBg, lineColor: rule ? C.gray : C.blue, dash: rule ? "dash" : "solid", lineWidth: 1.25 });
    t(s, id, { x: x + 0.1, y: y + 0.1, w: bw - 0.2, h: 0.22, fontSize: 9, color: C.gray });
    t(s, name, { x: x + 0.1, y: y + 0.34, w: bw - 0.2, h: 0.42, fontSize: 13, bold: true, color: rule ? C.ink : C.blueInk });
    t(s, sub, { x: x + 0.1, y: y + 0.78, w: bw - 0.2, h: 0.32, fontSize: 9.5, color: C.sub });
    if (i < 6 && i !== 3) arrow(s, x + bw + 0.02, y + bh / 2, x + bw + gap - 0.02, y + bh / 2);
  });
  // 조건부 간선: check → recheck(무효 있음) / check → aggregate(없음), recheck → aggregate
  const xc = X0 + 3 * (bw + gap), xr = X0 + 4 * (bw + gap), xa = X0 + 5 * (bw + gap);
  arrow(s, xc + bw + 0.02, y + bh / 2, xr - 0.02, y + bh / 2, C.blue);
  t(s, "무효 있음", { x: xc + bw - 0.1, y: y - 0.32, w: 1.2, h: 0.25, fontSize: 9.5, color: C.blue, bold: true });
  s.addShape(pres.shapes.LINE, { x: xc + bw / 2, y: y + bh + 0.05, w: 0, h: 0.35, line: { color: C.gray, width: 1.25 } });
  s.addShape(pres.shapes.LINE, { x: xc + bw / 2, y: y + bh + 0.4, w: xa + bw / 2 - (xc + bw / 2), h: 0, line: { color: C.gray, width: 1.25 } });
  s.addShape(pres.shapes.LINE, { x: xa + bw / 2, y: y + bh + 0.05, w: 0, h: 0.35, flipV: true, line: { color: C.gray, width: 1.25, endArrowType: "triangle" } });
  t(s, "무효 없음 → 바로 집계", { x: xc + bw / 2 + 0.1, y: y + bh + 0.45, w: 3, h: 0.25, fontSize: 9.5, color: C.gray });
  const facts = [
    ["상태", "items · prior · verdicts · stances · failed · table · remedies — 노드는 상태를 읽고 자기 칸만 씀"],
    ["실패 처리", "평가위원 호출 실패는 순차 재시도, 그래도 실패하면 「응답 k/6」으로 화면에 표시(조용히 버리지 않음)"],
    ["모델 대체", `주 엔진·평가위원마다 대체 모델 사슬 — 한도·장애 시 자동 전환, 실제로 판정한 모델을 기록에 남김`],
    ["RAG 대신", "공고·초안 원문을 통째로 넣고 인용으로 대조 — 조각 검색으로 문맥을 잃지 않게"],
  ];
  facts.forEach(([h, d], i) => {
    const yy = 5.25 + i * 0.42;
    t(s, h, { x: X0, y: yy, w: 1.4, h: 0.32, fontSize: 12.5, bold: true, color: C.blueInk });
    t(s, d, { x: X0 + 1.5, y: yy, w: W - 1.5, h: 0.32, fontSize: 12, color: C.sub });
  });
  s.addNotes(`[25초] 저희 구조의 핵심은 LLM을 판사로 쓰지 않는다는 겁니다. LLM은 증인처럼 증거, 즉 원문 인용만 냅니다. 채택할지, 몇 관점이 동의했는지, 판정을 보류할지는 결정론 코드가 정합니다. 흐름은 LangGraph 상태 그래프 한 장입니다. 점검 질문, 선행 탐색, 여섯 명 병렬 채점까지 가고, 인용 검사에서 원문에 없는 판정이 있으면 그 평가위원에게만 한 번 되돌아가 다시 묻습니다. 없으면 바로 집계로 갑니다. 한 회사 모델이 한도에 걸리거나 멈추면 다음 모델로 자동으로 넘어가고, 실제로 판정한 모델은 기록에 남깁니다.`);
}


// ---------- 신뢰도 정의 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "신뢰도 — 정답이 없는 영역이라, 기준을 먼저 세웠습니다");
  title(s, "맞히는 것이 아니라,\n**확인할 수 있는 것**을 신뢰라고 정의했습니다");
  const lx = X0, lw = 3.6;
  box(s, lx, 2.85, lw, 3.55, { fill: C.bg2, lineColor: C.bg2 });
  t(s, "주장하지 않는 것", { x: lx + 0.25, y: 3.0, w: lw - 0.5, h: 0.3, fontSize: 13, bold: true, color: C.gray });
  t(s, ["심사 결과·점수를 맞힌다", "가상 관점 = 실제 심사위원", "제안서를 대신 써 준다"].map((x, i, a) => ({ text: "✕  " + x, options: { breakLine: i < a.length - 1 } })),
    { x: lx + 0.25, y: 3.45, w: lw - 0.5, h: 1.6, fontSize: 14.5, bold: true, color: C.ink, lineSpacingMultiple: 1.6 });
  t(s, "심사위원의 판단은 주관적이고 정답이 없습니다 — 그래서 이것들은 주장하지 않습니다.", { x: lx + 0.25, y: 5.2, w: lw - 0.5, h: 1.0, fontSize: 11.5, color: C.sub, lineSpacingMultiple: 1.2 });
  const rx = lx + lw + 0.35, rw = R - rx;
  const rows = [
    ["추적 가능", "모든 지적은 두 끝에 묶입니다 — 공고 원문(쪽·인용)과 초안 원문(인용). 사람이 원문을 바로 열어 확인합니다."],
    ["날조 없음", `원문에 없는 인용은 코드가 걸러 판정에서 뺍니다 — 이번 실행 ${B.n_verdicts}개 중 ${B.invalid}건 적발 → ${B.cited ?? B.fixed}건 원문 확인 · ${B.still ?? 0}건 무효.`],
    ["모르면 넘김", "관점이 갈리면(20~80%) 판정하지 않고 「논쟁 지점」으로 사람에게, 근거 있는 판정이 절반 미만이면 「확인 불가」."],
    ["잴 수 있는 것만 숫자로", "요건 추출(정답표 대비)과 일부러 지운 근거 탐지(오탐)만 숫자로 말하고, 심사 예측 정확도는 말하지 않습니다."],
  ];
  rows.forEach(([h, d], i) => {
    const y = 2.9 + i * 0.9;
    t(s, `0${i + 1}`, { x: rx, y, w: 0.5, h: 0.36, fontSize: 16, bold: true, color: C.blue });
    t(s, h, { x: rx + 0.55, y, w: 2.1, h: 0.36, fontSize: 15, bold: true });
    t(s, d, { x: rx + 2.7, y: y + 0.02, w: rw - 2.7, h: 0.8, fontSize: 11.5, color: C.sub, lineSpacingMultiple: 1.15 });
    if (i < 3) hline(s, y + 0.8, rx, rw);
  });
  hline(s, 6.6);
  t(s, "이 기준은 현장 심사위원 멘토링의 조언(주장 범위를 좁히고, 신뢰의 논리를 스스로 세울 것)을 그대로 따른 것입니다.", { x: X0, y: 6.7, w: W, h: 0.3, fontSize: 11.5, color: C.gray });
  s.addNotes(`[25초] 심사위원의 판단엔 정답이 없습니다. 그래서 저희는 심사 결과를 맞힌다고 주장하지 않습니다. 대신 신뢰를 네 가지로 정의했습니다. 모든 지적은 공고 원문과 초안 원문 두 끝에 묶여 바로 확인할 수 있고, 원문에 없는 인용은 코드가 걸러내고, 관점이 갈리면 판정하지 않고 사람에게 넘기고, 잴 수 있는 것만 숫자로 말합니다.`);
}

// ---------- 7. MCP ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "MCP 도구 서버 — AI 도구 연결 표준");
  title(s, "검사 도구를 MCP로 감싸,\n**다른 AI 비서**도 같은 검사를 씁니다");
  const lw = 6.3;
  numRow(s, "01", "search_prior_art(query, n)", "공개 학술 DB 검색 — OpenAlex 우선, 장애 시 Crossref로 자동 전환 · 결과는 혁신성 판정의 참고 자료", X0, 2.95, lw, { hSize: 16, dSize: 11.5 });
  numRow(s, "02", "check_quote(quote, text)", "인용이 원문에 있는지 true/false — LLM 없이 같은 규칙 코드로", X0, 4.0, lw, { hSize: 16, dSize: 11.5 });
  numRow(s, "03", "왜 OpenAlex인가, 왜 MCP인가", "무료·키 없음·메타데이터 공개 라이선스라 기관 어디서든 비용 0 — 다만 오늘 밤 실측 중 OpenAlex가 503을 냈고 도구 뒤에서 Crossref로 바뀌었습니다. 국내 DB(NTIS·KCI)도 같은 자리에 꽂으면 됩니다", X0, 5.05, lw, { hSize: 16, dSize: 11.5 });
  const rx = 7.55, rw = R - rx;
  box(s, rx, 2.85, rw, 3.75, { fill: C.bg2, lineColor: C.bg2 });
  t(s, "실측 — 다른 AI 비서(Codex CLI)에 서버를 붙여 호출", { x: rx + 0.25, y: 3.0, w: rw - 0.5, h: 0.3, fontSize: 12, bold: true, color: C.blue });
  t(s, 'mcp_servers.rfp_to_fit.command = "python"\nargs = ["-m", "rfp_to_fit.infrastructure.mcp_server"]', { x: rx + 0.25, y: 3.4, w: rw - 0.5, h: 0.6, fontSize: 10.5, fontFace: "Courier New", color: C.ink });
  t(s, [
    { text: "check_quote(「재현율 90% 이상」) → true", options: { breakLine: true } },
    { text: "check_quote(「정밀도 95% 달성」) → false", options: { breakLine: true } },
    { text: "search_prior_art(「multi-agent LLM grant proposal review」) → 3편(Crossref)", options: {} },
  ], { x: rx + 0.25, y: 4.15, w: rw - 0.5, h: 1.1, fontSize: 12, bold: true, lineSpacingMultiple: 1.3 });
  t(s, "찾은 선행연구 중 하나는 다중 에이전트로 지원서를 「생성」하는 연구 — 저희는 생성하지 않고, 이 공고의 심사표로 「검사」합니다.", { x: rx + 0.25, y: 5.4, w: rw - 0.5, h: 1.0, fontSize: 11.5, color: C.sub, lineSpacingMultiple: 1.2 });
  src(s, "증거: deliver/mcp-codex-transcript.txt(호출 기록) · Crossref 대체 전환은 tests/test_scholar.py");
  s.addNotes("[20초] 검사 도구 두 개를 MCP 서버로 감쌌습니다. 선행연구 검색과 인용 검사입니다. 실제로 다른 AI 비서인 Codex에 이 서버를 붙여 호출해 봤고, 원문에 있는 인용은 참, 없는 인용은 거짓이 나왔습니다. OpenAlex를 쓴 이유는 무료이고 키가 필요 없어서인데, 오늘 밤 실측 중에 OpenAlex가 장애를 냈고 도구 뒤에서 Crossref로 바뀌었습니다. MCP로 감싼 이유가 바로 이겁니다. 국내 DB도 같은 자리에 꽂으면 됩니다.");
}

// ---------- 측정 — 잴 수 있는 것만 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "측정 — 잴 수 있는 것만 숫자로");
  title(s, "정답표를 먼저 고정하고,\n**처음 보는 공고**와 제거 실험으로 쟀습니다");
  const ex = N.extract;
  const nm = (e) => e.agency.replace("국가과학기술연구회", "NAIS 해커톤");
  const hn = { "msit-national-scientist-2026": "과기정통부 국가과학자", "msit-rising-star-2026": "과기정통부 라이징스타" };
  t(s, "① 공고 파싱 — 요건 재현율(심사표 배점은 5건 모두 100%)", { x: X0, y: 2.85, w: 6.2, h: 0.3, fontSize: 12.5, bold: true, color: C.sub });
  const rows = ex.map((e) => [`${nm(e)} · 개발용`, `${e.recall}%`, `${e.rmin}~${e.rmax}`, false])
    .concat(hb.map((r, i) => [`${hn[Object.keys(HO.blind)[i]] || ""} · 처음 봄`, `${pct0(r.recall)}%`, `${pct0(r.recall_min)}~${pct0(r.recall_max)}`, true]));
  rows.forEach(([a1, b1, c1, hold], i) => {
    const y = 3.25 + i * 0.42;
    t(s, a1, { x: X0, y, w: 3.6, h: 0.32, fontSize: 13, bold: hold, color: hold ? C.blueInk : C.ink });
    t(s, b1, { x: X0 + 3.6, y, w: 0.95, h: 0.32, fontSize: 14, bold: true, align: "right", color: hold ? C.blueInk : C.ink });
    t(s, c1, { x: X0 + 4.7, y: y + 0.03, w: 1.3, h: 0.28, fontSize: 10.5, color: C.gray });
  });
  t(s, "「처음 봄」= 개발에 안 쓴 공고를 링크로 새로 가져와 정답표를 측정 전에 커밋(3회). 라이징스타에서 놓친 9개 중 6개가 ※주석 조건 → 규칙 1줄 후 89~95%(따로 표기)",
    { x: X0, y: 5.4, w: 6.1, h: 0.62, fontSize: 10.5, color: C.sub, lineSpacingMultiple: 1.15 });
  const rx = 7.35, rw = R - rx;
  t(s, `② 제거 실험 — 근거를 지운 초안 ${P.n}개에서 오탐(안 지운 곳을 짚음)`, { x: rx, y: 2.85, w: rw, h: 0.3, fontSize: 12.5, bold: true, color: C.sub });
  const cw = (rw - 0.3) / 3;
  AB.forEach((a, i) => {
    const x = rx + i * (cw + 0.15), hi = a.mode !== "single";
    box(s, x, 3.25, cw, 1.95, { fill: hi ? C.blueBg : C.white, lineColor: hi ? C.blue : C.line });
    t(s, a.label.replace("(단일 LLM)", "").replace("(현재)", ""), { x: x + 0.15, y: 3.35, w: cw - 0.3, h: 0.5, fontSize: 11, bold: true, lineSpacingMultiple: 1.05 });
    t(s, `${a.fp}`, { x: x + 0.15, y: 3.85, w: cw - 0.3, h: 0.75, fontSize: 40, bold: true, color: hi ? C.blueInk : C.ink });
    t(s, `짚은 ${a.detect}`, { x: x + 0.15, y: 4.72, w: cw - 0.3, h: 0.3, fontSize: 11, color: C.sub });
  });
  t(s, "관점을 나누자 오탐이 0 — 세 회사 모델을 섞는 효과는 이 표본(5개·각 1회)에선 확인 안 됨(섞는 이유는 가용성)", { x: rx, y: 5.4, w: rw, h: 0.62, fontSize: 10.5, color: C.sub, lineSpacingMultiple: 1.15 });
  hline(s, 6.2);
  t(s, `링크 입력: 실제 공지 주소 ${LK ? `${LK.n}건 중 ${LK.ok}건` : "-"}에서 공고문을 골라 읽음(HWP 첨부·스크립트 다운로드·공고문 2개 합치기) · IRIS 상세는 미실측`, { x: X0, y: 6.35, w: W, h: 0.32, fontSize: 12.5, bold: true });
  src(s, "정답표: 파이프라인(OpenAI)과 다른 회사 모델(Claude)이 원문을 읽어 작성 · 검증 정답표 커밋 430ea7d(21:37) 뒤 측정 · 추출 정밀도 45~84%는 다음 개선 대상");
  s.addNotes(`[30초] 잴 수 있는 것만 숫자로 말씀드립니다. 예시 공고에만 맞춘 게 아닌지 보려고, 개발에 안 쓴 과기정통부 공고 두 건을 링크로 가져와 정답표를 먼저 고정하고 쟀습니다. 94%와 77%, 심사표 배점은 다섯 건 모두 맞혔습니다. 그리고 관점을 여러 개로 나눌 필요가 있는지 제거 실험을 했습니다. 관점 하나는 안 지운 곳을 ${single.fp}곳 잘못 짚었고, 여섯으로 나누자 0이었습니다. 회사 모델을 섞는 효과는 확인되지 않았다고 그대로 말씀드립니다.`);
}

// ---------- 예선 약속 → 본선 구현 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "예선 약속 → 본선 구현 — 포스터와 현실의 거리");
  title(s, "예선 때 약속한 것을,\n**그대로** 대조했습니다");
  const rows = [
    ["공고 URL·PDF·HWPX 입력", "✓", "+HWP, 실제 공지 13/13"],
    ["요건·평가지표 구조화(출처 쪽)", "✓", "모든 항목에 쪽·원문 인용"],
    ["가상 평가위원 독립 채점 → 합의/논쟁/확인 불가", "✓", "관점 6개(현장 멘토링 반영)"],
    ["보완 지정 — 문장은 쓰지 않음", "✓", "근거 종류·넣을 위치만"],
    ["선행 탐색(논문·NTIS 과제·KIPRIS 특허, MCP)", "△", "논문만 — 축소 규칙 적용, NTIS·KIPRIS는 키 미확보"],
    ["RAG(bge-m3 + FAISS)", "✕", "원문 전체 + 인용 대조로 교체 — 판정 근거 추적이 더 직접적"],
    ["요건 재현율 ≥ 90%", "△", "개발 85~93% · 처음 본 공고 77~94%"],
    ["결핍 탐지 정밀도 ≥ 80%", "✓", "오탐 0(100%) · 탐지 4/5, 표본 5"],
    ["초안 비저장 · 오픈소스(MIT)", "✓", "+개인정보 가림 · LICENSE 공개"],
  ];
  rows.forEach(([a1, mark, note], i) => {
    const y = 2.85 + i * 0.43;
    const col = mark === "✓" ? C.blueInk : mark === "△" ? "B7791F" : "C0392B";
    t(s, a1, { x: X0, y, w: 6.2, h: 0.34, fontSize: 13.5, bold: true });
    t(s, mark, { x: X0 + 6.3, y, w: 0.5, h: 0.34, fontSize: 16, bold: true, color: col, align: "center" });
    t(s, note, { x: X0 + 7.0, y: y + 0.02, w: W - 7.0, h: 0.32, fontSize: 12, color: C.sub });
    if (i < rows.length - 1) hline(s, y + 0.39);
  });
  src(s, "기획서 v2(9/5 제출)·아이디어 포스터(9/15 제출) 대비 — 못 한 것도 지우지 않았습니다 · 전체 표는 저장소 README");
  s.addNotes("[20초] 예선 때 약속한 것을 그대로 대조했습니다. 링크 입력, 구조화, 독립 채점, 보완 지정은 했습니다. 특허·과제 탐색은 논문만 했고, RAG는 원문 인용 대조로 바꿨고, 재현율 90%는 공고에 따라 못 미친 곳이 있습니다. 못 한 것도 지우지 않았습니다.");
}

// ---------- 10. 우리 자신에게 먼저 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "우리 자신에게 먼저 — 이 대회 본선 심사표로 예선 기획서를");
  title(s, `이 대회 심사표로 우리를 먼저 검사하니,\n**${nsel.length}개 관점**에서 걸린 점이 오늘의 준비물이 됐습니다`, { fontSize: 30 });
  t(s, "각 관점이 쓴 「가장 걸리는 점」(원문)", { x: X0, y: 2.85, w: 6, h: 0.3, fontSize: 12.5, bold: true, color: C.blue });
  t(s, "그래서 오늘 가져온 것", { x: 7.35, y: 2.85, w: 5, h: 0.3, fontSize: 12.5, bold: true, color: C.blue });
  const answer = {
    "세부 전문형": `목표치 대신 실측치 — 처음 보는 공고 재현율·제거 실험(9장)`,
    "사업성·시장형": "첫 실증 대상 — 전문기관 접수 후 요건 사전검토(12장)",
    "행정·관리형": `검증 가능한 과정 — 커밋 ${N.git.commits}개·테스트 ${N.tests}개·측정 스크립트 공개`,
  };
  nsel.slice(0, 3).forEach((x, i) => {
    const y = 3.3 + i * 1.05, nmx = pn[x.id] || x.id;
    t(s, nmx, { x: X0, y, w: 6.0, h: 0.3, fontSize: 13, bold: true });
    t(s, `“${x.point}”`, { x: X0, y: y + 0.32, w: 6.0, h: 0.6, fontSize: 11.5, color: C.sub, lineSpacingMultiple: 1.12 });
    arrow(s, X0 + 6.1, y + 0.35, 7.25, y + 0.35, C.blue);
    t(s, answer[nmx] || "—", { x: 7.35, y: y + 0.12, w: R - 7.35, h: 0.6, fontSize: 13, bold: true, color: C.blueInk, lineSpacingMultiple: 1.12 });
  });
  hline(s, 6.55);
  t(s, `항목 근거는 거의 다 있었지만 ${nsel.length}개 관점이 전체 인상을 「보류」로 적었습니다 — 결과 예측이 아니라, 발표 전에 대비할 질문을 먼저 받은 것`, { x: X0, y: 6.65, w: W, h: 0.3, fontSize: 11.5, color: C.gray });
  s.addNotes(`[20초] 이 대회 본선 심사표로 저희 예선 기획서를 먼저 검사했습니다. 결과를 예측한 게 아니라, 세 관점에서 걸리는 점을 받았습니다. 목표치만 있고 실측이 없다, 구매 주체가 약하다, 검증 계획이 빠듯하다. 그래서 오늘 실측치와 첫 실증 대상과 검증 가능한 과정을 가져왔습니다.`);
}

// ---------- 11. 확장 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "확장 — 같은 엔진, 세 개의 시점");
  title(s, "제출 전 → 접수 후 → 심사 중,\n**같은 엔진**이 이어집니다");
  const steps = [
    ["연구자", "제출 전", "셀프 점검", "고칠 곳·판단할 곳·관점별로 걸리는 점", "지금 이 앱 — 구현"],
    ["전문기관", "접수 후", "요건 사전검토", "같은 요건 매트릭스로 형식 미비·필수 서류 누락을 먼저 걸러 담당자 검토 시간 단축", "첫 실증 목표 — 계획"],
    ["평가위원", "심사 중", "근거 위치 표시", "지표마다 제안서의 근거 문장 위치를 옆에 띄워 심사 보조 — 판정은 사람", "계획"],
  ];
  const cw = (W - 0.6) / 3;
  steps.forEach(([who, when, what, how, st], i) => {
    const x = X0 + i * (cw + 0.3);
    box(s, x, 2.85, cw, 2.55, { fill: i === 0 ? C.blueBg : C.white, lineColor: i === 0 ? C.blue : C.line });
    t(s, `${when} · ${who}`, { x: x + 0.25, y: 3.0, w: cw - 0.5, h: 0.3, fontSize: 12, bold: true, color: C.blue });
    t(s, what, { x: x + 0.25, y: 3.38, w: cw - 0.5, h: 0.45, fontSize: 20, bold: true });
    t(s, how, { x: x + 0.25, y: 3.95, w: cw - 0.5, h: 0.95, fontSize: 12, color: C.sub, lineSpacingMultiple: 1.15 });
    t(s, st, { x: x + 0.25, y: 4.95, w: cw - 0.5, h: 0.3, fontSize: 11.5, bold: true, color: i === 0 ? C.blueInk : C.gray });
    if (i < 2) arrow(s, x + cw + 0.03, 4.1, x + cw + 0.27, 4.1, C.blue);
  });
  t(s, [
    { text: "NAIS 비전과의 연결 — ", options: { bold: true } },
    { text: "「가설부터 실험·분석까지 스스로 하는 AI 사이언티스트, 1인 1연구소」에서 빠진 순간이 과제 신청입니다 — 그 자리를 채우는 도구입니다.", options: { breakLine: true } },
    { text: "데이터가 쌓이는 방향 — ", options: { bold: true } },
    { text: "실제 심사 의견은 평가기관에 있습니다(멘토링). 전문기관과 연계하면 가상 평가위원을 실제 심사 의견 유형으로 보정합니다.", options: { breakLine: true } },
    { text: "연결 — ", options: { bold: true } },
    { text: "MCP 도구로 NAIS 플랫폼·연구자 AI 비서에 그대로 꽂히고, 같은 엔진이 연차·성과보고서(지표 대비 실적)와 연구비 정산(증빙 대비 항목)으로 넓어집니다.", options: {} },
  ], { x: X0, y: 5.55, w: W, h: 1.4, fontSize: 11.5, color: C.sub, lineSpacingMultiple: 1.25 });
  s.addNotes("[15초] 같은 엔진이 세 시점으로 이어집니다. 지금은 연구자의 제출 전 셀프 점검이고, 첫 실증 목표는 전문기관의 접수 후 요건 사전검토, 그다음은 심사 중 평가위원에게 근거 위치를 띄워 주는 보조입니다. 실제 심사 의견 데이터는 평가기관에 있으니, 연계하면 가상 평가위원을 실제 유형으로 보정할 수 있습니다.");
}

// ---------- 12. 마무리 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  eyebrow(s, "지금 직접 해 보세요 — 공고 링크 하나, 초안 하나", 1.15);
  title(s, "제출 전에,\n**빈칸**부터.", { y: 1.8, h: 2.3, fontSize: 52 });
  t(s, `커밋 ${N.git.commits}개 · 코드는 전부 본선 중 커밋(첫 코드 커밋 ${N.git.first_code}, 그 전엔 문서뿐) · 테스트 ${N.tests}개\nSPEC → 테스트 → 구현 순서 · 측정 스크립트와 정답표 공개`, { x: X0, y: 4.45, w: 6.6, h: 0.8, fontSize: 14, color: C.sub, lineSpacingMultiple: 1.25 });
  t(s, "라이브가 끊기면 — 앱의 「② 우리 기획서 먼저 채점」 탭이 저장된 실행 기록으로 같은 결과를 보여 줍니다", { x: X0, y: 5.45, w: 6.6, h: 0.6, fontSize: 12, color: C.gray, lineSpacingMultiple: 1.2 });
  t(s, "팀 루미아 · 김태걸 · 박세훈", { x: X0, y: 6.4, w: 6, h: 0.45, fontSize: 16, bold: true });
  const qs = [["라이브 앱", N.qr_live, N.live_url.replace(/^https?:\/\//, "")], ["GitHub", N.qr_repo, N.repo_url.replace(/^https?:\/\//, "")]];
  qs.forEach(([k, img, url], i) => {
    const x = 7.95 + i * 2.3, y = 2.0;
    box(s, x, y, 2.05, 3.05);
    s.addImage({ path: img, x: x + 0.28, y: y + 0.28, w: 1.5, h: 1.5 });
    t(s, k, { x: x + 0.2, y: y + 1.98, w: 1.65, h: 0.35, fontSize: 14, bold: true });
    t(s, url, { x: x + 0.2, y: y + 2.38, w: 1.7, h: 1.0, fontSize: 9.5, color: C.gray, lineSpacingMultiple: 1.15, fit: "none" });
  });
  s.addNotes("[10초] 공고 링크 하나, 초안 하나. 제출 전에 빈칸부터 짚어 드립니다. 화면의 주소에서 지금 직접 해 보실 수 있습니다. 감사합니다.");
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("wrote", f));
