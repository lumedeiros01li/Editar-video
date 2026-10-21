// Render dos balões R7: escolhe tamanhos, calcula o layout (regra do rosto) e gera os PNGs.
// Uso: node render.mjs job.json
// job = { roteiro: {b:[4], aviso:{n:texto}, capa}, face: {proibida:[x1,y1,x2,y2], zona:[...]} | null, out, fonts }
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

async function loadPlaywright() {
  try { return await import('playwright'); } catch {
    const root = execSync('npm root -g').toString().trim();
    return await import(path.join(root, 'playwright', 'index.mjs'));
  }
}

const job = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const R = job.roteiro, FACE = job.face, OUT = job.out, FD = job.fonts;
fs.mkdirSync(OUT, { recursive: true });

// ---------- constantes de layout (ver SKILL.md) ----------
const LIVRE = !!job.livre;  // --ultrapassar: libera a área segura, olhos e boca continuam proibidos
const AREA = { x1: 50, y1: 258, x2: LIVRE ? 1880 : 893, y2: LIVRE ? 1880 : 1525 };
const CX = 520;            // centro horizontal padrão da pilha e da chamada
const X_MIN = LIVRE ? 10 : 30, X_MAX = LIVRE ? 1070 : 930;   // limite lateral absoluto, sombra incluída
const B1_TOP_MIN = 228;    // título pode passar 30 px acima da área
const STACK_TOP = 270;     // topo da faixa onde a pilha é centralizada
const GAP = 26, GAP_CHIP = 40;
const CHIP = { size: 44, cy: 1500, padV: 16, padH: 28, shadow: 6, bottomMax: LIVRE ? 1900 : 1560, cyMin: 1440, cyMax: LIVRE ? 1850 : 1510, sizeMin: 38 };
const WIDTHS = [800, 750, 700, 650, 600];
const LEVELS = [0, 1, 2, 3, 4];  // 0 = regra normal de fonte, 4 = mínimo (52 / 32)
const SH = { 1: 10, 2: 8, 3: 8, 4: 8 };
const SHC = { 1: '#9966FF', 2: '#000', 3: '#000', 4: '#000' };

const font = (f) => 'file://' + path.join(FD, f);
const css = (maxW) => `
@font-face{font-family:AB;src:url(${font('archivo-black-latin-400-normal.woff2')}) format('woff2');unicode-range:U+0000-00FF,U+2000-206F;}
@font-face{font-family:AB;src:url(${font('archivo-black-latin-ext-400-normal.woff2')}) format('woff2');unicode-range:U+0100-024F;}
@font-face{font-family:JB;font-weight:700;src:url(${font('jetbrains-mono-latin-700-normal.woff2')}) format('woff2');unicode-range:U+0000-00FF,U+2000-206F;}
@font-face{font-family:JB;font-weight:700;src:url(${font('jetbrains-mono-latin-ext-700-normal.woff2')}) format('woff2');unicode-range:U+0100-024F;}
@font-face{font-family:JB;font-weight:400;src:url(${font('jetbrains-mono-latin-400-normal.woff2')}) format('woff2');unicode-range:U+0000-00FF,U+2000-206F;}
@font-face{font-family:JB;font-weight:400;src:url(${font('jetbrains-mono-latin-ext-400-normal.woff2')}) format('woff2');unicode-range:U+0100-024F;}
html,body{margin:0;background:transparent;}
body{width:1080px;height:1920px;position:relative;}
.b{position:absolute;box-sizing:border-box;border:6px solid #000;border-radius:0;padding:28px 36px;text-align:center;color:#000;
   max-width:${maxW}px;width:max-content;text-wrap:balance;overflow-wrap:normal;}
.b1{background:#fff;font-family:AB;text-transform:uppercase;line-height:1.1;}
.bm{background:#fff;font-family:JB;font-weight:700;line-height:1.25;}
.b4{background:#EBFF70;}
.hl{background:#9966FF;color:#fff;white-space:nowrap;padding:0 .12em;}
.av{display:block;font-family:JB;font-weight:400;font-size:24px;line-height:1.3;text-transform:none;margin-top:12px;}
.chip{position:absolute;background:#000;color:#EBFF70;font-family:AB;line-height:1.15;white-space:nowrap;border-radius:0;}
.emo{font-family:'Noto Color Emoji';}
`;
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const hl = (s) => esc(s).replace(/\[\[(.+?)\]\]/g, '<span class="hl">$1</span>');

function balloonHTML(i, size, w) {
  const cls = i === 1 ? 'b b1' : i === 4 ? 'b bm b4' : 'b bm';
  const av = R.aviso && R.aviso[i] ? `<span class="av">${esc(R.aviso[i])}</span>` : '';
  const ws = w ? `;width:${w}px;text-wrap:wrap` : '';
  return `<div id="e${i}" class="${cls}" style="font-size:${size}px${ws}">${hl(R.b[i - 1])}${av}</div>`;
}
const chipHTML = (size) =>
  `<div id="ec" class="chip" style="font-size:${size}px;padding:${CHIP.padV}px ${CHIP.padH}px">LEIA A LEGENDA <span class="emo">👇</span></div>`;

const { chromium } = await loadPlaywright();
let browser;
try { browser = await chromium.launch(); } catch {
  browser = await chromium.launch({ executablePath: process.env.R7_CHROMIUM || '/opt/pw-browsers/chromium' });
}
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
const htmlPath = path.join(OUT, '_layout.html');
let curMaxW = 800;
async function load(body, maxW = curMaxW) {
  fs.writeFileSync(htmlPath, `<!doctype html><html><head><meta charset="utf-8"><style>${css(maxW)}</style></head><body>${body}</body></html>`);
  await page.goto('file://' + htmlPath);
  await page.evaluate(() => document.fonts.ready);
}

// mede um balão: linhas, destaque inteiro, estouro, largura justa
const measureEl = (id) => page.evaluate((id) => {
  const el = document.getElementById(id);
  const cs = getComputedStyle(el);
  const lh = parseFloat(cs.lineHeight);
  const av = el.querySelector('.av');
  const avH = av ? av.getBoundingClientRect().height + 12 : 0;
  const inner = el.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - avH;
  const lines = Math.round(inner / lh);
  const hlOk = [...el.querySelectorAll('.hl')].every((h) => h.getClientRects().length === 1);
  const fits = el.scrollWidth <= el.clientWidth + 1;
  const rects = [];
  const rg = document.createRange(); rg.selectNodeContents(el);
  for (const r of rg.getClientRects()) rects.push(r);
  for (const h of el.querySelectorAll('.hl')) for (const r of h.getClientRects()) rects.push(r);
  const byLine = {};
  for (const r of rects) { if (r.width < 1) continue; const k = Math.round(r.top); (byLine[k] ||= []).push(r); }
  let maxW = 0;
  for (const k in byLine) maxW = Math.max(maxW, Math.max(...byLine[k].map((r) => r.right)) - Math.min(...byLine[k].map((r) => r.left)));
  const er = el.getBoundingClientRect();
  return { lines, hlOk, fits, w: er.width, h: er.height, tight: Math.min(er.width, Math.ceil(maxW + 2 * 36 + 12 + 4)) };
}, id);

const cacheM = new Map();
async function measure(i, size, maxW) {
  const key = `${i}|${size}|${maxW}`;
  if (cacheM.has(key)) return cacheM.get(key);
  await load(balloonHTML(i, size), maxW);
  const m = await measureEl('e' + i);
  if (m.hlOk && m.fits) {
    await load(balloonHTML(i, size, m.tight), maxW);
    const m2 = await measureEl('e' + i);
    if (m2.lines === m.lines && m2.hlOk) Object.assign(m, { w: m2.w, h: m2.h });
    else m.tight = Math.round(m.w);
  }
  const res = { ...m, size, width: Math.ceil(m.hlOk && m.fits ? m.tight : m.w), h: Math.round(m.h) };
  cacheM.set(key, res);
  return res;
}

// tamanho de um balão para um nível de redução
async function sizeBalloon(i, maxW, level) {
  const [start, min, maxLines, abs] = i === 1 ? [64, 54, 3, 52] : [40, 34, 2, 32];
  let base = null;
  for (let s = start; s >= min; s--) {
    const m = await measure(i, s, maxW);
    if (m.hlOk && m.fits) { base = m; if (m.lines <= maxLines) break; }
  }
  if (!base) { // destaque não coube nem no mínimo da regra: desce até o absoluto
    for (let s = min - 1; s >= abs; s--) { const m = await measure(i, s, maxW); if (m.hlOk && m.fits) { base = m; break; } }
  }
  if (!base) return null;
  if (level === 0) return base;
  const target = Math.round(base.size - (base.size - abs) * level / 4);
  for (let s = target; s >= abs; s--) { const m = await measure(i, s, maxW); if (m.hlOk && m.fits) return m; }
  return null;
}
const cacheS = new Map();
async function metrics(level, maxW) {
  const key = level + '|' + maxW;
  if (cacheS.has(key)) return cacheS.get(key);
  const ms = [];
  for (let i = 1; i <= 4; i++) ms.push(await sizeBalloon(i, maxW, level));
  const res = ms.every(Boolean) ? ms : null;
  cacheS.set(key, res);
  return res;
}
const cacheC = new Map();
async function chipMetrics(size) {
  if (cacheC.has(size)) return cacheC.get(size);
  await load(chipHTML(size));
  const r = await page.evaluate(() => { const b = document.getElementById('ec').getBoundingClientRect(); return { w: Math.round(b.width), h: Math.round(b.height) }; });
  cacheC.set(size, r);
  return r;
}

// ---------- geometria ----------
const P = FACE ? FACE.proibida : null, Z = FACE ? FACE.zona : null;
const hit = (r, box) => box && r[0] < box[2] && r[2] > box[0] && r[1] < box[3] && r[3] > box[1];
const overlapArea = (r, box) => !box ? 0 : Math.max(0, Math.min(r[2], box[2]) - Math.max(r[0], box[0])) * Math.max(0, Math.min(r[3], box[3]) - Math.max(r[1], box[1]));
const shadowRect = (p, sh) => [p.x, p.y, p.x + p.w + sh, p.y + p.h + sh];

function place(m, cx, tops) { // tops[i] = topo de cada balão
  const pos = {};
  for (let i = 1; i <= 4; i++) pos[i] = { x: Math.round(cx - m[i - 1].width / 2), y: Math.round(tops[i]), w: m[i - 1].width, h: m[i - 1].h };
  return pos;
}
function stackTops(m, top) { const t = {}; let y = top; for (let i = 1; i <= 4; i++) { t[i] = y; y += m[i - 1].h + GAP; } return t; }
const stackH = (m, from = 1) => m.slice(from - 1).reduce((a, b) => a + b.h, 0) + (4 - from) * GAP;

function evaluate(pos, chip) {
  // limites
  for (let i = 1; i <= 4; i++) {
    const r = shadowRect(pos[i], SH[i]);
    if (r[0] < X_MIN || r[2] > X_MAX) return null;
    if (i === 1 ? r[1] < B1_TOP_MIN : r[1] < AREA.y1) return null;
    if (r[3] > AREA.y2) return null;
    if (hit(r, P)) return null;
  }
  for (let i = 1; i < 4; i++) if (pos[i].y + pos[i].h > pos[i + 1].y) return null;
  const cr = shadowRect(chip, CHIP.shadow);
  if (cr[0] < X_MIN || cr[2] > X_MAX || cr[3] > CHIP.bottomMax || hit(cr, P)) return null;
  if (pos[4].y + pos[4].h > chip.y - GAP_CHIP) return null;
  let margin = 0; const margemIds = [];
  for (const k of [1, 2, 3, 4]) { const a = overlapArea(shadowRect(pos[k], SH[k]), Z); if (a > 0) { margin += a; margemIds.push(String(k)); } }
  const ca = overlapArea(cr, Z); if (ca > 0) { margin += ca; margemIds.push('chamada'); }
  return { margin, margemIds };
}

function cxCandidates(m, shift) {
  const wmax = Math.max(...m.map((b) => b.width));
  const lo = Math.ceil(X_MIN + wmax / 2), hi = Math.floor(X_MAX - 10 - wmax / 2);
  const base = Math.min(Math.max(CX, lo), hi);
  if (!shift || !P) return [base];
  const dir = (P[0] + P[2]) / 2 < CX ? 1 : -1;  // lado oposto ao rosto
  const out = [];
  for (let cx = base; cx >= lo && cx <= hi; cx += 5 * dir) out.push(cx);
  return out;
}
function chipCandidates(step5) {
  const out = [{ size: CHIP.size, cy: CHIP.cy }];
  if (!step5) return out;
  for (let s = CHIP.size; s >= CHIP.sizeMin; s -= 2) for (let cy = CHIP.cyMax; cy >= CHIP.cyMin; cy -= 5) out.push({ size: s, cy });
  return out;
}

async function solve() {
  // passos cumulativos: 0 padrão, 1 deslocar na horizontal, 2 largura, 3 fonte, 4 vertical, 5 chamada, 6 dividido
  // no modo livre o layout dividido vem primeiro: estoura menos a base da área segura
  const order = LIVRE && P ? [6, 0, 1, 2, 3, 4, 5] : [0, 1, 2, 3, 4, 5, 6];
  for (const step of order) {
    const widths = step >= 2 ? WIDTHS : [800];
    const levels = step >= 3 ? LEVELS : [0];
    const chips = chipCandidates(step >= 5);
    const pool = [];  // no passo 6 a busca é global: sem margem primeiro, depois maiores fontes
    for (const level of levels) for (const maxW of widths) {
      const m = await metrics(level, maxW);
      if (!m) continue;
      const cands = step === 6 ? pool : [];
      for (const cc of chips) {
        const cm = await chipMetrics(cc.size);
        for (const cx of cxCandidates(m, step >= 1)) {
          const chip = { x: Math.round(cx - cm.w / 2), y: Math.round(cc.cy - cm.h / 2), w: cm.w, h: cm.h, size: cc.size };
          const zoneBottom = chip.y - GAP_CHIP;
          if (step < 6) {
            const H = stackH(m);
            const centered = Math.max(B1_TOP_MIN, Math.round((STACK_TOP + zoneBottom) / 2 - H / 2));
            const topsList = step >= 4 ? Array.from({ length: Math.max(1, Math.floor((zoneBottom - H - B1_TOP_MIN) / 4) + 1) }, (_, k) => B1_TOP_MIN + 4 * k) : [centered];
            for (const top of topsList) {
              const pos = place(m, cx, stackTops(m, top));
              const ev = evaluate(pos, chip);
              if (ev) cands.push({ pos, chip, ev, cx, score: (ev.margin > 0 ? 1e6 : 0) + Math.abs(cx - CX) * 2 + Math.abs(top - centered) + Math.abs(CHIP.cy - cc.cy) * 3 + (CHIP.size - cc.size) * 20 });
            }
          } else if (P) {
            // layout dividido: balão 1 acima do rosto, 2 a 4 empilhados abaixo
            const h1 = m[0].h;
            const topLimit1 = P[1] - SH[1] - h1 - 1;
            if (topLimit1 < B1_TOP_MIN) continue;
            const z1 = Z[1] - SH[1] - h1 - 1;
            const t1 = z1 >= B1_TOP_MIN ? Math.round((B1_TOP_MIN + z1) / 2) : B1_TOP_MIN;
            const H = stackH(m, 2);
            for (const startMin of [Z[3] + 1, P[3] + 1]) {
              if (startMin + H > zoneBottom) continue;
              const t2 = Math.round((startMin + zoneBottom) / 2 - H / 2);
              const tops = { 1: t1 }; let y = t2; for (let i = 2; i <= 4; i++) { tops[i] = y; y += m[i - 1].h + GAP; }
              const pos = place(m, cx, tops);
              const ev = evaluate(pos, chip);
              if (ev) { cands.push({ pos, chip, ev, cx, split: true, score: (ev.margin > 0 ? 1e6 : 0) + Math.abs(cx - CX) * 2 + Math.abs(CHIP.cy - cc.cy) * 3 + (CHIP.size - cc.size) * 20 }); break; }
            }
          }
        }
      }
      if (step === 6) { for (const c of cands) if (!c.m) Object.assign(c, { m, level, maxW, score: c.score - m.reduce((a, b) => a + b.size, 0) * 50 }); continue; }
      if (cands.length) return pick(cands, m, level, maxW, step);
    }
    if (step === 6 && pool.length) { const c = pool.sort((a, b) => a.score - b.score)[0]; return pick([c], c.m, c.level, c.maxW, step); }
  }
  return null;
}

function pick(cands, m, level, maxW, step) {
        cands.sort((a, b) => a.score - b.score);
        const c = cands[0];
        const applied = [];
        if (c.cx !== CX) applied.push(1);
        if (maxW < 800) applied.push(2);
        if (level > 0) applied.push(3);
        if (step >= 4 && !c.split) {
          const H = stackH(m); const centered = Math.max(B1_TOP_MIN, Math.round((STACK_TOP + c.chip.y - GAP_CHIP) / 2 - H / 2));
          if (c.pos[1].y !== centered) applied.push(4);
        }
        if (c.chip.size !== CHIP.size || c.chip.y !== Math.round(CHIP.cy - c.chip.h / 2)) applied.push(5);
        if (c.split) applied.push(6);
        return { ...c, m, level, maxW, applied };
}

const sol = await solve();
if (!sol) {
  // falha: registra o layout padrão para o quadro de problema
  const m = await metrics(4, 800);
  const cm = await chipMetrics(CHIP.size);
  const chip = { x: Math.round(CX - cm.w / 2), y: Math.round(CHIP.cy - cm.h / 2), w: cm.w, h: cm.h };
  const H = m ? stackH(m) : 0;
  const pos = m ? place(m, CX, stackTops(m, Math.max(B1_TOP_MIN, Math.round((STACK_TOP + chip.y - GAP_CHIP) / 2 - H / 2)))) : {};
  fs.writeFileSync(path.join(OUT, 'falha.json'), JSON.stringify({ motivo: 'nenhum layout evita olhos e boca após os 6 passos', pos, chip, alturaPilhaMin: H }, null, 2));
  await browser.close();
  console.log(JSON.stringify({ ok: false }));
  process.exit(2);
}

// ---------- PNGs ----------
const { pos, chip, m } = sol;
curMaxW = sol.maxW;
const shots = [];
const ease = (f) => 1 - Math.pow(1 - f / 6, 3);
for (const k of [1, 2, 3, 4, 'c']) {
  const p = k === 'c' ? chip : pos[k];
  const d = k === 'c' ? CHIP.shadow : SH[k];
  const col = k === 'c' ? '#9966FF' : SHC[k];
  const states = k === 1 ? [1] : [0, 1, 2, 3, 4, 5].map(ease).concat([1]);
  for (let si = 0; si < states.length; si++) {
    const e = states[si];
    const sd = +(d * e).toFixed(2);
    await load(k === 'c' ? chipHTML(chip.size) : balloonHTML(k, m[k - 1].size, m[k - 1].width));
    await page.evaluate(({ id, p, col, sd }) => {
      const el = document.getElementById(id);
      el.style.left = p.x + 'px'; el.style.top = p.y + 'px';
      el.style.boxShadow = sd > 0 ? `${sd}px ${sd}px 0 0 ${col}` : 'none';
    }, { id: k === 'c' ? 'ec' : 'e' + k, p, col, sd });
    const clip = { x: p.x, y: p.y, width: Math.min(p.w + 12, 1080 - p.x), height: p.h + 12 };
    const final = k === 1 || si === states.length - 1;
    const name = final ? `${k}_final.png` : `${k}_f${si}.png`;
    await page.screenshot({ path: path.join(OUT, name), omitBackground: true, clip });
    shots.push({ k: String(k), si, name, e, x: clip.x, y: clip.y, final });
  }
}

// ---------- capa: balão estilo 1, 120 a 96 px, centro x 540, dentro de y 285..1635, regra do rosto ----------
let capa = null;
for (let s = 120; s >= 96 && !capa; s -= 2) {
  await load(`<div id="cv" class="b b1" style="font-size:${s}px;line-height:1.05">${esc(R.capa)}</div>`, 960);
  const mm = await measureEl('cv');
  if (!mm.fits) continue;
  const w = mm.tight, h = Math.round(mm.h);
  const regions = [[285 + 20, 1635 - 20]];
  if (P) regions.push([Z[3] + 1, 1635 - 20], [P[3] + 1, 1635 - 20], [285 + 20, Z[1] - 1], [285 + 20, P[1] - 1]);
  for (const [a, b] of regions) {
    if (b - a < h + 10) continue;
    const y = Math.round((a + b) / 2 - (h + 10) / 2);
    const r = [Math.round(540 - w / 2), y, Math.round(540 - w / 2) + w + 10, y + h + 10];
    if (hit(r, P)) continue;
    capa = { size: s, x: r[0], y, w, h, margem: overlapArea(r, Z) > 0 };
    break;
  }
}
if (capa) {
  await load(`<div id="cv" class="b b1" style="font-size:${capa.size}px;line-height:1.05;width:${capa.w}px;text-wrap:wrap;left:${capa.x}px;top:${capa.y}px;box-shadow:10px 10px 0 0 #9966FF">${esc(R.capa)}</div>`, 960);
  await page.screenshot({ path: path.join(OUT, 'capa_balao.png'), omitBackground: true, clip: { x: 0, y: 0, width: 1080, height: 1920 } });
}
await browser.close();
fs.unlinkSync(htmlPath);

const result = {
  ok: true,
  fontes: Object.fromEntries([1, 2, 3, 4].map((i) => [i, m[i - 1].size])),
  larguras: Object.fromEntries([1, 2, 3, 4].map((i) => [i, m[i - 1].width])),
  linhas: Object.fromEntries([1, 2, 3, 4].map((i) => [i, m[i - 1].lines])),
  chamada: { fonte: chip.size, centroY: Math.round(chip.y + chip.h / 2) },
  centroX: sol.cx, larguraMax: sol.maxW, nivelFonte: sol.level,
  passos: sol.applied, margem: sol.ev.margemIds, pos, chip, shots, capa,
};
fs.writeFileSync(path.join(OUT, 'layout.json'), JSON.stringify(result, null, 2));
console.log(JSON.stringify({ ok: true, fontes: result.fontes, larguras: result.larguras, chamada: result.chamada, passos: result.passos, margem: result.margem, capa }));
