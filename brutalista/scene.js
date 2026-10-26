// Morning Call — edição "Vox colagem + Brutalista"
// Render determinístico: window.renderFrame(n) desenha o quadro n (30 fps) no canvas.
const W = 1080, H = 1920, FPS = 30, DUR = 62.3;
const cv = document.getElementById('c'), c = cv.getContext('2d');

// ---------- paleta ----------
const INK = '#111111', PAPER = '#EEE9DE', WHITE = '#FAF8F2', YEL = '#F6E31B', RED = '#FF3B1F', GRAY = '#8A877F';

// ---------- dados ----------
let WORDS = [], CAPS = [], IMG = {};
const S = i => WORDS[i].s, E = i => WORDS[i].e;

// ---------- utilidades ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, p) => a + (b - a) * p;
const prog = (t, t0, d) => clamp((t - t0) / d);
const eOut = p => 1 - Math.pow(1 - p, 3);
const eExpo = p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p);
const eBack = p => { const k = 2.2; return 1 + (k + 1) * Math.pow(p - 1, 3) + k * Math.pow(p - 1, 2); };
const eInOut = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
function rnd(seed) { let t = (seed * 2654435761 + 0x6D2B79F5) >>> 0; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }
let F = 0, T = 0; // quadro e tempo atuais
// "boil" de stop-motion: muda a cada 3 quadros
const boil = (seed, amp = 2) => { const k = Math.floor(F / 3); return { x: (rnd(seed * 97 + k) - .5) * 2 * amp, y: (rnd(seed * 89 + k + 7) - .5) * 2 * amp, r: (rnd(seed * 83 + k + 3) - .5) * amp * 0.006 }; };
const shakeAmt = (seed, amp) => { const k = F; return { x: (rnd(seed * 31 + k) - .5) * 2 * amp, y: (rnd(seed * 37 + k + 1) - .5) * 2 * amp }; };

const FONTS = { AB: "'Archivo Black'", AN: "'Anton'", SM: "'Space Mono'", IS: "'Instrument Serif'" };
function font(f, size) {
  if (f === 'IS') return `italic ${size}px 'Instrument Serif'`;
  if (f === 'SMB') return `700 ${size}px 'Space Mono'`;
  if (f === 'SM') return `400 ${size}px 'Space Mono'`;
  return `${size}px ${FONTS[f]}`;
}
function setFont(f, size, ls = 0) { c.font = font(f, size); c.letterSpacing = ls + 'px'; }
function tw(s, f, size, ls = 0) { setFont(f, size, ls); return c.measureText(s).width; }
function text(s, x, y, f, size, color, align = 'left', ls = 0) {
  setFont(f, size, ls); c.fillStyle = color; c.textAlign = align; c.textBaseline = 'alphabetic'; c.fillText(s, x, y);
}

// transform helper: aplica posição/rotação/escala e chama fn
function at(x, y, rot, sc, fn) { c.save(); c.translate(x, y); if (rot) c.rotate(rot); if (sc !== 1) c.scale(sc, sc); fn(); c.restore(); }

// entrada "slam": escala 1.5 -> 1 com overshoot, aparece duro (sem fade)
function slam(t0, x, y, rot, fn, dur = 0.16, from = 1.6) {
  if (T < t0) return; const p = prog(T, t0, dur);
  const sc = p >= 1 ? 1 : lerp(from, 1, eOut(p));
  at(x, y, rot, sc, fn);
}
// entrada deslizando (dx,dy de origem) com eBack
function slide(t0, x, y, rot, dx, dy, fn, dur = 0.32, ease = eBack) {
  if (T < t0) return; const p = ease(prog(T, t0, dur));
  at(x + dx * (1 - p), y + dy * (1 - p), rot, 1, fn);
}

// ---------- formas de colagem ----------
const tornCache = {};
function tornPts(x, y, w, h, seed, amp = 8, step = 16) {
  const key = [x, y, w, h, seed, amp, step].join(',');
  if (tornCache[key]) return tornCache[key];
  const pts = []; let i = 0;
  const edge = (x0, y0, x1, y1, nx, ny) => {
    const L = Math.hypot(x1 - x0, y1 - y0), n = Math.max(2, Math.round(L / step));
    for (let k = 0; k < n; k++) { const p = k / n, o = (rnd(seed * 1000 + i++) - .5) * 2 * amp; pts.push([lerp(x0, x1, p) + nx * o, lerp(y0, y1, p) + ny * o]); }
  };
  edge(x, y, x + w, y, 0, 1); edge(x + w, y, x + w, y + h, 1, 0); edge(x + w, y + h, x, y + h, 0, 1); edge(x, y + h, x, y, 1, 0);
  return tornCache[key] = pts;
}
function pathPts(pts) { c.beginPath(); c.moveTo(pts[0][0], pts[0][1]); for (let k = 1; k < pts.length; k++) c.lineTo(pts[k][0], pts[k][1]); c.closePath(); }

function cover(img, x, y, w, h, zoom = 1, fx = .5, fy = .5) {
  const s = Math.max(w / img.width, h / img.height) * zoom, iw = img.width * s, ih = img.height * s;
  c.drawImage(img, x + (w - iw) * fx, y + (h - ih) * fy, iw, ih);
}
// pedaço de papel rasgado com foto dentro (centro cx,cy)
function photoPiece(img, cx, cy, w, h, rot, seed, o = {}) {
  at(cx, cy, rot, 1, () => {
    c.save(); c.shadowColor = 'rgba(0,0,0,0.35)'; c.shadowBlur = 24; c.shadowOffsetX = 8; c.shadowOffsetY = 14;
    pathPts(tornPts(-w / 2, -h / 2, w, h, seed, 9, 18)); c.fillStyle = o.edge || WHITE; c.fill(); c.restore();
    c.save(); pathPts(tornPts(-w / 2 + 12, -h / 2 + 12, w - 24, h - 24, seed + 3, 4, 12)); c.clip();
    if (o.draw) o.draw(-w / 2 + 12, -h / 2 + 12, w - 24, h - 24); else cover(img, -w / 2, -h / 2, w, h, o.zoom || 1, o.fx ?? .5, o.fy ?? .5);
    c.restore();
  });
}
// recorte (png com borda branca) com sombra dura brutalista
function cutout(img, cx, cy, w, rot, o = {}) {
  const h = img.height * w / img.width;
  at(cx, cy, rot, 1, () => {
    if (o.hard !== false) { c.save(); c.globalAlpha = .9; c.filter = 'brightness(0)'; c.drawImage(img, -w / 2 + 14, -h / 2 + 16, w, h); c.restore(); }
    c.drawImage(img, -w / 2, -h / 2, w, h);
  });
  return h;
}
function tape(cx, cy, w, rot, seed = 1) {
  at(cx, cy, rot, 1, () => {
    const h = 46; c.beginPath(); c.moveTo(-w / 2, -h / 2);
    for (let k = 0; k <= 6; k++) c.lineTo(-w / 2 + (k % 2 ? 6 : 0), -h / 2 + k * h / 6);
    for (let k = 6; k >= 0; k--) c.lineTo(w / 2 - (k % 2 ? 6 : 0), -h / 2 + k * h / 6);
    c.closePath(); c.fillStyle = 'rgba(232,222,190,0.82)'; c.fill();
    c.strokeStyle = 'rgba(0,0,0,0.06)'; c.lineWidth = 2; c.stroke();
  });
}
// bloco de texto invertido (slab) — reveal horizontal
function slab(s, x, y, f, size, fg, bg, p = 1, padX = 18, padY = 12, ls = -2, align = 'left') {
  const w = tw(s, f, size, ls), hh = size * 0.78;
  const x0 = align === 'center' ? x - w / 2 : x;
  const bw = (w + padX * 2) * eExpo(p);
  c.fillStyle = bg; c.fillRect(x0 - padX, y - hh - padY, bw, hh + padY * 2);
  c.save(); c.beginPath(); c.rect(x0 - padX, y - hh - padY - 40, bw, hh + padY * 2 + 80); c.clip();
  text(s, x0, y, f, size, fg, 'left', ls); c.restore();
  return w;
}
// marca-texto amarelo por trás
function highlight(x, y, w, size, p, color = YEL) {
  if (p <= 0) return; const hh = size * 0.62;
  c.save(); c.fillStyle = color; c.beginPath();
  const ww = (w + 24) * eOut(p);
  c.moveTo(x - 12, y - hh + 4); c.lineTo(x - 12 + ww, y - hh - 2); c.lineTo(x - 12 + ww, y + 10); c.lineTo(x - 12, y + 14); c.closePath(); c.fill(); c.restore();
}
// círculo de caneta vermelha desenhado progressivamente
function scribbleCircle(cx, cy, rx, ry, p, seed = 1, color = RED, lw = 10) {
  if (p <= 0) return; const n = 90, loops = 1.18, pts = [];
  for (let k = 0; k <= n; k++) { const a = -2.2 + k / n * Math.PI * 2 * loops, j = 1 + (rnd(seed * 50 + Math.floor(k / 6)) - .5) * 0.08 + k / n * 0.06;
    pts.push([cx + Math.cos(a) * rx * j, cy + Math.sin(a) * ry * j]); }
  const m = Math.max(2, Math.floor(pts.length * eOut(p)));
  c.save(); c.strokeStyle = color; c.lineWidth = lw; c.lineCap = 'round'; c.lineJoin = 'round'; c.beginPath(); c.moveTo(pts[0][0], pts[0][1]);
  for (let k = 1; k < m; k++) c.lineTo(pts[k][0], pts[k][1]); c.stroke(); c.restore();
}
// seta de caneta
function scribbleArrow(pts0, p, color = RED, lw = 10, head = 34) {
  if (p <= 0) return; const pts = [];
  const [a, b, d] = pts0; for (let k = 0; k <= 40; k++) { const u = k / 40; pts.push([(1 - u) * (1 - u) * a[0] + 2 * (1 - u) * u * b[0] + u * u * d[0], (1 - u) * (1 - u) * a[1] + 2 * (1 - u) * u * b[1] + u * u * d[1]]); }
  const m = Math.max(2, Math.floor(pts.length * clamp(p / .8)));
  c.save(); c.strokeStyle = color; c.lineWidth = lw; c.lineCap = 'round'; c.lineJoin = 'round'; c.beginPath(); c.moveTo(pts[0][0], pts[0][1]);
  for (let k = 1; k < m; k++) c.lineTo(pts[k][0], pts[k][1]); c.stroke();
  if (p > .8) { const q = eOut((p - .8) / .2), e = pts[pts.length - 1], s = pts[pts.length - 5], ang = Math.atan2(e[1] - s[1], e[0] - s[0]);
    c.beginPath(); c.moveTo(e[0] - Math.cos(ang - .5) * head * q, e[1] - Math.sin(ang - .5) * head * q); c.lineTo(e[0], e[1]);
    c.lineTo(e[0] - Math.cos(ang + .5) * head * q, e[1] - Math.sin(ang + .5) * head * q); c.stroke(); }
  c.restore();
}
// carimbo
const stampCache = {};
function stamp(s, cx, cy, rot, size, t0, color = RED) {
  if (T < t0) return; const p = prog(T, t0, .14);
  const key = s + size + color;
  if (!stampCache[key]) {
    const w = tw(s, 'AB', size, 2) + size * 0.9, h = size * 1.55, o = document.createElement('canvas'); o.width = w + 20; o.height = h + 20; const g = o.getContext('2d');
    g.strokeStyle = color; g.lineWidth = 8; g.strokeRect(10, 10, w, h); g.lineWidth = 3; g.strokeRect(22, 22, w - 24, h - 24);
    g.font = font('AB', size); g.letterSpacing = '2px'; g.fillStyle = color; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 10 + w / 2, 10 + h / 2 + size * 0.04);
    g.globalCompositeOperation = 'destination-out';
    for (let k = 0; k < w * h / 90; k++) { g.globalAlpha = rnd(k * 3 + s.length) * .9; g.beginPath(); g.arc(rnd(k * 7 + 1) * o.width, rnd(k * 11 + 2) * o.height, rnd(k * 13 + 3) * 3.2, 0, 7); g.fill(); }
    stampCache[key] = o;
  }
  const o = stampCache[key], sc = lerp(2.2, 1, eOut(p));
  at(cx, cy, rot, sc, () => { c.globalAlpha = clamp(p * 3) * .92; c.drawImage(o, -o.width / 2, -o.height / 2); c.globalAlpha = 1; });
}
function downArrow(cx, cy, s, color) { // seta bloco ↓
  c.fillStyle = color; c.beginPath(); c.moveTo(cx - s * .22, cy - s * .5); c.lineTo(cx + s * .22, cy - s * .5); c.lineTo(cx + s * .22, cy); c.lineTo(cx + s * .5, cy);
  c.lineTo(cx, cy + s * .5); c.lineTo(cx - s * .5, cy); c.lineTo(cx - s * .22, cy); c.closePath(); c.fill();
}
function hatch(x, y, w, h, color, gap = 16, lw = 5) {
  c.save(); c.beginPath(); c.rect(x, y, w, h); c.clip(); c.strokeStyle = color; c.lineWidth = lw;
  for (let k = -h; k < w + h; k += gap) { c.beginPath(); c.moveTo(x + k, y + h); c.lineTo(x + k + h, y); c.stroke(); } c.restore();
}
function rule(x, y, w, p = 1, lw = 8, color = INK) { c.fillStyle = color; c.fillRect(x, y - lw / 2, w * eExpo(p), lw); }

// ---------- fundo, grão e HUD ----------
let GRAIN = [];
function makeGrain() {
  for (let v = 0; v < 4; v++) { const o = document.createElement('canvas'); o.width = 540; o.height = 960; const g = o.getContext('2d'); const d = g.createImageData(540, 960);
    for (let k = 0; k < d.data.length; k += 4) { const n = rnd(k + v * 99991) * 255; d.data[k] = d.data[k + 1] = d.data[k + 2] = n; d.data[k + 3] = 255; }
    g.putImageData(d, 0, 0); GRAIN.push(o); }
}
function bg(theme) {
  if (theme === 'paper') { c.drawImage(IMG.paper, 0, 0, W, H); }
  else { c.fillStyle = theme === 'dark' ? '#0F0F0F' : YEL; c.fillRect(0, 0, W, H); c.save(); c.globalAlpha = .18; c.globalCompositeOperation = 'multiply'; c.drawImage(IMG.paper, 0, 0, W, H); c.restore(); }
  // grade brutalista exposta
  c.save(); c.strokeStyle = theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.055)'; c.lineWidth = 2;
  for (let x = 60; x < W; x += 120) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, H); c.stroke(); }
  for (let y = 0; y < H; y += 120) { c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
  c.restore();
}
function grain() {
  c.save(); c.globalAlpha = .07; c.globalCompositeOperation = 'overlay'; c.drawImage(GRAIN[Math.floor(F / 2) % 4], 0, 0, W, H); c.restore();
}
const SCENE_NAMES = ['ABERTURA', 'ELEIÇÃO', 'RESULTADO', 'MERCADO', 'LÁ FORA', 'CONTAS', 'CONGRESSO', 'SUPREMO', 'IMPRENSA', 'JUROS', 'RECADO', 'FIM'];
function hud(theme, idx) {
  const fg = theme === 'dark' ? WHITE : INK, bgc = theme === 'dark' ? WHITE : INK, inv = theme === 'dark' ? INK : (theme === 'yellow' ? YEL : PAPER);
  c.fillStyle = bgc; c.fillRect(40, 52, tw('MORNING CALL', 'AB', 26, 1) + 28, 46);
  text('MORNING CALL', 54, 85, 'AB', 26, inv, 'left', 1);
  text('SEG 26.10.26', 70 + tw('MORNING CALL', 'AB', 26, 1) + 28, 84, 'SMB', 24, fg);
  const tc = `${String(Math.floor(T / 60)).padStart(2, '0')}:${String(Math.floor(T % 60)).padStart(2, '0')}:${String(F % 30).padStart(2, '0')}`;
  text(tc, W - 40, 84, 'SM', 24, fg, 'right');
  text(`[${String(idx + 1).padStart(2, '0')}/12] ${SCENE_NAMES[idx]}`, W - 40, 128, 'SMB', 20, theme === 'dark' ? '#bbb' : '#555', 'right');
  c.fillStyle = fg; c.fillRect(40, 108, 300, 4);
  // marcas de corte nos cantos
  c.strokeStyle = fg; c.lineWidth = 3; const m = 24, L = 30;
  for (const [x, y, sx, sy] of [[m, H - m, 1, -1], [W - m, H - m, -1, -1]]) { c.beginPath(); c.moveTo(x, y + sy * L); c.lineTo(x, y); c.lineTo(x + sx * L, y); c.stroke(); }
}

// ---------- legendas ----------
function captions(theme) {
  const ci = CAPS.findIndex(k => T >= k.s && T < k.e); if (ci < 0) return;
  const k = CAPS[ci], size = 56, padX = 14, gap = 10, lineH = 84, maxW = 920;
  const words = k.words.map(w => ({ ...w, u: w.w.toUpperCase() }));
  setFont('AB', size, -1);
  const lines = [[]]; let lw = 0;
  for (const w of words) { const ww = c.measureText(w.u).width + padX * 2; if (lw + ww > maxW && lines[lines.length - 1].length) { lines.push([]); lw = 0; } lines[lines.length - 1].push({ ...w, ww }); lw += ww + gap; }
  const cy = 1545 - (lines.length - 1) * lineH / 2, rot = (rnd(ci * 7) - .5) * 0.05;
  at(540, cy, rot, 1, () => {
    lines.forEach((ln, li) => {
      const total = ln.reduce((a, w) => a + w.ww, 0) + gap * (ln.length - 1); let x = -total / 2; const y = li * lineH;
      for (const w of ln) {
        if (T >= w.s - 0.04) {
          const p = prog(T, w.s - 0.04, .12), sc = lerp(.55, 1, eBack(p)), active = T < w.e + 0.05 && T >= w.s - 0.04;
          const bgc = active ? YEL : (theme === 'dark' ? WHITE : INK), fg = active ? INK : (theme === 'dark' ? INK : WHITE);
          at(x + w.ww / 2, y, active ? -0.03 : 0, sc, () => {
            c.fillStyle = 'rgba(0,0,0,0.9)'; if (theme !== 'dark') c.fillRect(-w.ww / 2 + 7, -size * .62 + 8, w.ww, size * 1.24);
            c.fillStyle = bgc; c.fillRect(-w.ww / 2, -size * .62, w.ww, size * 1.24);
            text(w.u, 0, size * .36, 'AB', size, fg, 'center', -1);
          });
        }
        x += w.ww + gap;
      }
    });
  });
}

// ---------- texto "recorte de jornal" (ransom note) ----------
function ransom(str, x, y, size, t0, t1, seed) {
  const chars = [...str]; let cx = x; const n = chars.filter(ch => ch !== ' ').length; let i = 0;
  const styles = [[INK, WHITE, 'AB'], [WHITE, INK, 'AN'], [YEL, INK, 'AB'], ['#d8d3c6', INK, 'IS'], [INK, YEL, 'AN'], [WHITE, INK, 'SMB'], [RED, WHITE, 'AB']];
  for (const ch of chars) {
    if (ch === ' ') { cx += size * .45; continue; }
    const st = styles[Math.floor(rnd(seed * 31 + i) * styles.length)], f = st[2], fs = size * (f === 'IS' ? 1.25 : f === 'SMB' ? 1.0 : f === 'AN' ? 1.08 : .92);
    const w = Math.max(tw(ch, f, fs), size * .5) + 18, ti = lerp(t0, t1, i / Math.max(1, n - 1));
    const rot = (rnd(seed * 17 + i) - .5) * .22, dy = (rnd(seed * 13 + i) - .5) * 14, b = boil(seed * 50 + i, 1.5);
    slam(ti, cx + w / 2 + b.x, y + dy + b.y, rot + b.r, () => {
      c.save(); c.shadowColor = 'rgba(0,0,0,.3)'; c.shadowBlur = 6; c.shadowOffsetY = 4;
      pathPts(tornPts(-w / 2, -size * .62, w, size * 1.22, seed * 100 + i, 3, 10)); c.fillStyle = st[0]; c.fill(); c.restore();
      text(ch, 0, size * .36, f, fs, st[1], 'center');
    }, .1, 1.8);
    cx += w + 4; i++;
  }
}

// =====================================================================
// CENAS
// =====================================================================
const SC = [];
// 1 ABERTURA 0 – 1.62  "Bom dia."
SC.push({ s: 0, e: 1.62, theme: 'paper', draw() {
  const b1 = boil(1, 2), b2 = boil(2, 2), b3 = boil(3, 2);
  slide(0.25, 560 + b1.x, 1060 + b1.y, -0.04 + b1.r, 0, 900, () => {
    photoPiece(IMG.lucas, 0, 0, 600, 720, 0, 11, { fy: .3 });
    tape(-220, -350, 190, -0.5); tape(230, -350, 190, 0.45);
    text('com', -250, 330, 'IS', 44, INK); slab('LUCAS MEDEIROS', -175, 336, 'AB', 40, WHITE, INK, 1, 12, 8, 0);
  }, .4, eExpo);
  slam(0.02, 70, 420, -0.03, () => text('MORNING', 0, 0, 'AB', 186, INK, 'left', -8), .14);
  slam(0.16, 90, 610, 0.02, () => slab('CALL', 0, 0, 'AB', 190, YEL, INK, prog(T, .16, .2), 26, 18, -6), .14);
  slam(0.5, 830 + b2.x, 610 + b2.y, 0.14, () => {
    c.save(); c.shadowColor = 'rgba(0,0,0,.3)'; c.shadowBlur = 14; c.shadowOffsetY = 8; c.fillStyle = YEL; c.fillRect(-120, -110, 240, 220); c.restore();
    text('SEGUNDA', 0, -40, 'SMB', 30, INK, 'center'); text('26/10', 0, 60, 'AN', 110, INK, 'center');
  });
  slide(0.55, 900 + b3.x, 1500 + b3.y, -0.08, 400, 0, () => cutout(IMG.bull, 0, 0, 330, 0), .35);
  slam(0.0, 70, 205, 0, () => text('EP. 26.10.2026 / MERCADO + POLÍTICA', 0, 0, 'SMB', 26, INK), .1, 1);
  scribbleCircle(820, 610, 175, 150, prog(T, .7, .5), 4);
} });

// 2 ELEIÇÃO 1.62 – 4.5
SC.push({ s: 1.62, e: 4.5, theme: 'paper', draw() {
  const z = 1 + (T - 1.62) * 0.02, b = boil(5, 1.5);
  photoPiece(IMG.congresso_lilas, 540 + b.x, 1010 + b.y, 1000, 860, -0.02 + b.r, 21, { zoom: z, fy: .7 });
  slam(S(3) - .05, 60, 255, 0, () => text('O Brasil escolheu', 0, 0, 'IS', 64, INK), .12, 1.2);
  slam(S(5), 60, 370, 0, () => text('O PRESIDENTE', 0, 0, 'AB', 104, INK, 'left', -4), .14);
  slam(S(7), 60, 480, 0, () => text('DOS PRÓXIMOS', 0, 0, 'AB', 104, INK, 'left', -4), .14);
  slam(S(9), 250, 980, -0.06, () => {
    c.fillStyle = INK; c.fillRect(-160 + 16, -250 + 18, 320, 430); c.fillStyle = YEL; c.fillRect(-160, -250, 320, 430);
    text('4', 0, 140, 'AN', 420, INK, 'center');
  }, .16, 2);
  slam(S(10), 640, 1010, 0.04, () => slab('ANOS', 0, 0, 'AB', 150, WHITE, INK, prog(T, S(10), .18), 22, 16, -5), .14);
  scribbleCircle(250, 960, 230, 270, prog(T, S(9) + .2, .45), 7);
} });

// 3 RESULTADO 4.5 – 12.2
SC.push({ s: 4.5, e: 12.2, theme: 'paper', draw() {
  text('2º TURNO // VOTOS VÁLIDOS', 60, 200, 'SMB', 28, INK);
  slam(S(11), 60, 330, 0, () => text('LULA FOI', 0, 0, 'AB', 120, INK, 'left', -5), .14);
  if (T >= S(13)) slab('REELEITO', 60, 470, 'AB', 130, YEL, INK, prog(T, S(13), .25), 22, 16, -5);
  const bl = boil(8, 1.5), bf = boil(9, 1.5);
  slide(S(11) + .1, 290 + bl.x, 840 + bl.y, -0.05 + bl.r, -700, 0, () => cutout(IMG.lula, 0, 0, 470, 0), .35);
  slide(S(13) + .3, 800 + bf.x, 860 + bf.y, 0.045 + bf.r, 700, 0, () => cutout(IMG.flavio, 0, 0, 450, 0), .35);
  tape(290, 610, 170, -0.3); if (T > S(13) + .5) tape(810, 640, 170, 0.35);
  scribbleCircle(290, 820, 260, 250, prog(T, S(13) + .1, .5), 12);
  // números
  const pl = eOut(prog(T, S(15), E(17) - S(15))), pf = eOut(prog(T, S(22), E(23) - S(22) + .05));
  const vl = (51.8 * pl).toFixed(1).replace('.', ','), vf = (48.2 * pf).toFixed(1).replace('.', ',');
  if (T >= S(14)) {
    text('LULA', 60, 1150, 'SMB', 30, INK); text(vl + '%', 52, 1310, 'AN', 170, INK, 'left', -2);
    text('FLÁVIO BOLSONARO', 1020, 1150, 'SMB', 30, INK, 'right');
    c.save(); setFont('AN', 170, -2); c.textAlign = 'right'; c.lineWidth = 4; c.strokeStyle = INK; c.strokeText(vf + '%', 1028, 1310);
    if (pf > 0) { c.fillStyle = GRAY; c.globalAlpha = .5; c.fillText(vf + '%', 1028, 1310); } c.restore();
    // barra
    const y = 1345, bw = 960;
    c.fillStyle = INK; c.fillRect(60, y, bw * .518 * pl, 56);
    hatch(60 + bw - bw * .482 * pf, y, bw * .482 * pf, 56, INK);
    c.strokeStyle = INK; c.lineWidth = 5; c.strokeRect(60, y, bw, 56);
    c.setLineDash([10, 8]); c.lineWidth = 3; c.beginPath(); c.moveTo(540, y - 20); c.lineTo(540, y + 76); c.stroke(); c.setLineDash([]);
  }
  if (T > S(26)) text('FONTE: TSE, 25/10/2026', 60, 1440, 'SM', 22, INK);
} });

// 4 MERCADO 12.2 – 15.45 (fundo escuro + vídeo do gráfico)
const FOOT = { chart: { s: 12.2, e: 15.45, n: 91 }, nyse: { s: 43.05, e: 48.15, n: 100 } };
const footK = name => { const f = FOOT[name]; return clamp(Math.round((T - f.s) / (f.e - f.s) * (f.n - 1)) + 1, 1, f.n); };
function footFrame(name) { return IMG[`${name}_${footK(name)}`]; }
function marquee(str, y, rot, speed, size, fg, bgc, t0) {
  if (T < t0) return; const p = eExpo(prog(T, t0, .3));
  at(540, y, rot, 1, () => {
    c.fillStyle = bgc; c.fillRect(-700, -size * .9, 1400 * p, size * 1.6);
    c.save(); c.beginPath(); c.rect(-700, -size, 1400 * p, size * 2); c.clip();
    const unit = tw(str, 'AB', size, 0); let off = ((T * speed) % unit + unit) % unit;
    for (let x = -700 - off; x < 700; x += unit) text(str, x, size * .36, 'AB', size, fg);
    c.restore();
  });
}
SC.push({ s: 12.2, e: 15.45, theme: 'dark', draw() {
  const b = boil(12, 2), img = footFrame('chart');
  photoPiece(null, 540 + b.x, 830 + b.y, 1010, 740, 0.025 + b.r, 31, { draw: (x, y, w, h) => { const s = w / img.width * 1.05; c.drawImage(img, x - 20, y - 40, img.width * s, img.height * s); } });
  marquee('MERCADO ▲▼ MERCADO ▲▼ ', 430, -0.06, 260, 54, INK, YEL, 12.25);
  slam(S(28), 60, 300, 0, () => text('O RESULTADO', 0, 0, 'AB', 96, WHITE, 'left', -4), .12);
  if (T >= S(30)) { const sh = shakeAmt(3, 5); slam(S(30), 60 + sh.x, 1390 + sh.y, -0.03, () => slab('MEXE', 0, 0, 'AB', 150, INK, WHITE, prog(T, S(30), .15), 20, 16, -6), .12); }
  slam(S(31), 600, 1320, 0, () => text('com o', 0, 0, 'IS', 60, WHITE), .1, 1);
  slam(S(33), 600, 1400, 0, () => text('MERCADO', 0, 0, 'AB', 68, YEL, 'left', -3), .12);
  scribbleArrow([[150, 980], [520, 560], [930, 1010]], prog(T, S(33), .5), RED, 12, 44);
  marquee('SEMANA AGITADA ✱ SEMANA AGITADA ✱ ', 1215, 0.05, -320, 50, WHITE, RED, S(36));
} });

// 5 LÁ FORA (mercados) 15.45 – 22.5
SC.push({ s: 15.45, e: 22.5, theme: 'paper', draw() {
  slam(S(39), 60, 230, 0, () => text('Ainda no domingo à noite,', 0, 0, 'IS', 62, INK), .1, 1.15);
  slam(S(44), 60, 305, 0, () => text('nas negociações lá fora', 0, 0, 'IS', 62, INK), .1, 1.15);
  // lua pictograma
  slam(S(41), 930, 255, 0, () => { c.fillStyle = INK; c.beginPath(); c.arc(0, 0, 62, 0, 7); c.fill(); c.fillStyle = PAPER; c.beginPath(); c.arc(28, -18, 56, 0, 7); c.fill(); });
  rule(60, 380, 960, prog(T, S(45), .4), 10);
  const fall = T >= S(56) ? eBack(prog(T, S(56), .3)) * 26 : 0;
  // linha REAL
  if (T >= S(49)) {
    slam(S(49), 60, 560 + fall, 0, () => text('REAL', 0, 0, 'AB', 170, INK, 'left', -6), .12);
    const p = prog(T, S(49) + .05, .3); at(880, 470 + fall + (1 - eBack(p)) * -160, 0, 1, () => { if (p > 0) downArrow(0, 0, 190, RED); });
  }
  rule(60, 640, 960, prog(T, S(49), .3), 6);
  if (T >= S(52)) {
    slam(S(52), 60, 750 + fall, 0, () => text('FUNDOS DE AÇÕES', 0, 0, 'AB', 84, INK, 'left', -3), .12);
    slam(S(55), 60, 835 + fall, 0, () => text('BRASILEIRAS LÁ FORA', 0, 0, 'AB', 62, INK, 'left', -2), .12);
    const p = prog(T, S(52) + .05, .3); at(965, 770 + fall + (1 - eBack(p)) * -160, 0, 1, () => { if (p > 0) downArrow(0, 0, 130, RED); });
  }
  rule(60, 900, 960, prog(T, S(52), .3), 6);
  stamp('CAÍRAM', 600, 690, -0.16, 92, S(56));
  // bloco HOJE
  if (T >= S(57)) {
    const p = eExpo(prog(T, S(57), .3)); c.fillStyle = INK; c.fillRect(0, 990, W * p, 380);
    if (T >= S(58)) slam(S(58), 60, 1130, 0, () => text('A BOLSA DAQUI', 0, 0, 'AB', 100, WHITE, 'left', -4), .12);
    if (T >= S(60)) slam(S(60), 60, 1290, 0, () => text('REAGE', 0, 0, 'AB', 130, WHITE, 'left', -5), .12);
    if (T >= S(61)) slam(S(61), 560, 1300, -0.05, () => slab('HOJE', 0, 0, 'AB', 150, INK, YEL, prog(T, S(61), .15), 20, 14, -5), .14, 2);
  }
} });

// 6 CONTAS 22.5 – 27.05
SC.push({ s: 22.5, e: 27.05, theme: 'paper', draw() {
  slam(S(62), 760, 1000, 0.14, () => { text('?', 0, 0, 'AN', 1150, YEL, 'center'); }, .18, 1.3);
  slam(S(63), 60, 250, 0, () => text('A dúvida principal:', 0, 0, 'IS', 70, INK), .1, 1.15);
  slam(S(66), 60, 370, 0, () => text('COMO VÃO FICAR', 0, 0, 'AB', 92, INK, 'left', -4), .12);
  if (T >= S(69)) { highlight(60, 510, tw('AS CONTAS', 'AB', 150, -6), 150, prog(T, S(70), .25), WHITE); slam(S(69), 60, 510, 0, () => text('AS CONTAS', 0, 0, 'AB', 150, INK, 'left', -6), .12); }
  if (T >= S(71)) slab('PÚBLICAS', 60, 680, 'AB', 150, YEL, INK, prog(T, S(71), .22), 20, 16, -6);
  const sw = Math.sin((T - 22.5) * 3.2) * 0.07, bs = boil(14, 1.5);
  slide(S(64), 790 + bs.x, 1080 + bs.y, sw, 600, 0, () => cutout(IMG.scales, 0, 0, 430, 0), .4);
  const tags = [['GASTO', S(72)], ['DÍVIDA', S(73)], ['META FISCAL', S(75)]];
  tags.forEach(([s, t0], i) => slam(t0, 70, 900 + i * 150, (i % 2 ? .03 : -.03), () => {
    const w = tw(s, 'SMB', 52) + 120; c.fillStyle = INK; c.fillRect(10, -50 + 10, w, 92); c.fillStyle = WHITE; c.fillRect(0, -50, w, 92);
    c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(0, -50, w, 92); c.strokeRect(22, -24, 40, 40);
    if (T > t0 + .15) { c.strokeStyle = RED; c.lineWidth = 8; c.beginPath(); c.moveTo(26, -6); c.lineTo(40, 12); c.lineTo(70, -36); c.stroke(); }
    text(s, 84, 14, 'SMB', 52, INK);
  }, .14, 1.8));
} });

// 7 CONGRESSO 27.05 – 31.4
let splitPts = null;
SC.push({ s: 27.05, e: 31.4, theme: 'paper', draw() {
  const sp = eBack(prog(T, S(80), .45)), gap = 70 * sp, rot = .06 * sp, b = boil(16, 1.5);
  if (!splitPts) { splitPts = []; for (let y = -500; y <= 500; y += 25) splitPts.push([(rnd(y + 999) - .5) * 40, y]); }
  const half = (side) => {
    at(540 + side * gap + b.x, 860 + b.y, side * rot * .5, 1, () => {
      c.save(); c.beginPath();
      if (side < 0) { c.moveTo(-500, -480); splitPts.forEach(p => c.lineTo(p[0], p[1])); c.lineTo(-500, 480); }
      else { c.moveTo(500, -480); splitPts.forEach(p => c.lineTo(p[0], p[1])); c.lineTo(500, 480); }
      c.closePath(); c.shadowColor = 'rgba(0,0,0,.35)'; c.shadowBlur = 20; c.shadowOffsetY = 12; c.fillStyle = WHITE; c.fill(); c.restore();
      c.save(); c.beginPath();
      if (side < 0) { c.moveTo(-488, -468); splitPts.forEach(p => c.lineTo(p[0] - 8, p[1])); c.lineTo(-488, 468); }
      else { c.moveTo(488, -468); splitPts.forEach(p => c.lineTo(p[0] + 8, p[1])); c.lineTo(488, 468); }
      c.closePath(); c.clip(); cover(IMG.congresso_azul, -500, -480, 1000, 960, 1.05 + (T - 27) * .01, .5, .45); c.restore();
    });
  };
  half(-1); half(1);
  slam(S(77), 60, 290, 0, () => text('COM UM', 0, 0, 'AB', 92, INK, 'left', -4), .12);
  slam(S(79), 60, 390, 0, () => text('CONGRESSO', 0, 0, 'AB', 120, INK, 'left', -5), .12);
  if (T >= S(80)) slam(S(80), 540, 930, -0.07, () => slab('DIVIDIDO,', 0, 0, 'AB', 140, INK, YEL, prog(T, S(80), .2), 22, 16, -5, 'center'), .16, 2.2);
  slam(S(81), 60, 1420, 0, () => text('cada proposta vai depender de', 0, 0, 'IS', 62, INK), .1, 1.1);
  if (T >= S(86)) {
    slam(S(86), 540, 1200, -0.02, () => {
      const s = 'NEGOCIAÇÃO', w = tw(s, 'SMB', 64) + 60; c.fillStyle = INK; c.fillRect(-w / 2 + 10, -60, w, 100); c.fillStyle = WHITE; c.fillRect(-w / 2, -70, w, 100);
      c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(-w / 2, -70, w, 100); text(s, 0, 0, 'SMB', 64, INK, 'center');
    }, .14, 1.6);
  }
} });

// 8 SUPREMO 31.4 – 35.7
SC.push({ s: 31.4, e: 35.7, theme: 'paper', draw() {
  const b = boil(18, 1.5);
  photoPiece(IMG.stf, 540 + b.x, 560 + b.y, 1000, 760, 0.02 + b.r, 41, { zoom: 1.05 + (T - 31.4) * .015, fx: .7, fy: .22 });
  slam(S(87), 60, 1030, 0, () => text('E no novo mandato,', 0, 0, 'IS', 64, INK), .1, 1.15);
  for (let i = 0; i < 4; i++) {
    const t0 = lerp(S(96) - .05, E(97) - .25, i / 3);
    slam(t0, 160 + i * 253, 1180, (rnd(i + 3) - .5) * .12, () => {
      c.fillStyle = INK; c.fillRect(-105 + 12, -105 + 14, 210, 210); c.fillStyle = i === 3 ? YEL : INK; c.fillRect(-105, -105, 210, 210);
      if (i === 3) { c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(-105, -105, 210, 210); }
      text(String(i + 1), 0, 75, 'AN', 200, i === 3 ? INK : WHITE, 'center');
    }, .12, 2);
  }
  stamp('ATÉ', 150, 1080, -0.2, 54, S(95));
  if (T >= S(97)) slam(S(97), 60, 1390, 0, () => text('INDICAÇÕES AO', 0, 0, 'AB', 64, INK, 'left', -3), .12);
  const sx = 60 + tw('INDICAÇÕES AO', 'AB', 64, -3) + 34;
  if (T >= S(99)) slam(S(99), sx, 1390, -0.03, () => slab('SUPREMO', 0, 0, 'AB', 64, INK, YEL, prog(T, S(99), .15), 14, 10, -3), .12);
} });

// 9 IMPRENSA 35.7 – 43.05
SC.push({ s: 35.7, e: 43.05, theme: 'paper', draw() {
  slam(S(100), 60, 340, 0, () => text('LÁ FORA', 0, 0, 'AB', 150, INK, 'left', -6), .14);
  const bn = boil(20, 2); slide(S(103), 900 + bn.x, 250 + bn.y, 0.1 + bn.r, 500, -200, () => cutout(IMG.news, 0, 0, 290, 0), .35);
  slam(S(102), 60, 440, 0, () => text('a imprensa internacional destacou', 0, 0, 'IS', 56, INK), .1, 1.1);
  ransom('O 4º MANDATO', 70, 580, 90, S(106), E(108) - .1, 3);
  ransom('E O DESAFIO', 70, 705, 90, S(109), S(111) + .2, 5);
  ransom('FISCAL', 70, 830, 90, S(112) - .05, E(112) - .1, 9);
  rule(60, 935, 960, prog(T, S(113), .35), 8);
  const bg2 = boil(22, 2), wob = Math.sin((T - 40) * 2) * .05;
  slide(S(115), 800 + bg2.x, 1160 + bg2.y, wob, 600, 0, () => cutout(IMG.globe, 0, 0, 360, 0), .4);
  scribbleCircle(830, 1110, 95, 120, prog(T, S(117) + .1, .4), 23);
  slam(S(115), 60, 1050, 0, () => text('OS VIZINHOS', 0, 0, 'AB', 84, INK, 'left', -3), .12);
  slam(S(116), 60, 1140, 0, () => text('DA AMÉRICA', 0, 0, 'AB', 84, INK, 'left', -3), .12);
  slam(S(118), 60, 1230, 0, () => slab('LATINA', 0, 0, 'AB', 84, WHITE, INK, prog(T, S(118), .15), 14, 10, -3), .12);
  stamp('JÁ PARABENIZARAM ✓', 500, 1330, -0.08, 46, S(119) + .1);
} });

// 10 JUROS 43.05 – 48.15
SC.push({ s: 43.05, e: 48.15, theme: 'paper', draw() {
  const b = boil(24, 1.5), img = footFrame('nyse');
  photoPiece(null, 540 + b.x, 470 + b.y, 1010, 640, -0.02 + b.r, 51, { draw: (x, y, w, h) => { const s = w / img.width * 1.02; c.drawImage(img, x - 10, y - 60, img.width * s, img.height * s); } });
  // calendário
  if (T >= S(121)) {
    const days = ['SEG', 'TER', 'QUA', 'QUI', 'SEX'], p = prog(T, S(121), .3);
    for (let i = 0; i < 5; i++) { if (p * 5 < i) continue; const x = 60 + i * 192, y = 830;
      c.fillStyle = i === 2 ? YEL : WHITE; c.fillRect(x, y, 180, 110); c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(x, y, 180, 110);
      text(days[i], x + 90, y + 72, 'SMB', 44, INK, 'center'); }
    scribbleCircle(60 + 2 * 192 + 90, 885, 120, 80, prog(T, S(122), .4), 25);
  }
  slam(S(124), 60, 1060, 0, () => text('O BANCO CENTRAL', 0, 0, 'AB', 78, INK, 'left', -3), .12);
  slam(S(126), 60, 1150, 0, () => text('AMERICANO', 0, 0, 'AB', 76, INK, 'left', -3), .12);
  slam(S(127), 60, 1265, 0, () => text('decide os', 0, 0, 'IS', 86, INK), .1, 1.15);
  slam(S(129), 620, 1330, -0.05, () => slab('JUROS', 0, 0, 'AN', 170, INK, YEL, prog(T, S(129), .15), 20, 14, 0), .16, 2);
  const bd = boil(26, 2);
  slide(S(136) - .1, 720 + bd.x, 620 + bd.y, -0.12 + bd.r, 700, -100, () => cutout(IMG.dollars, 0, 0, 520, 0), .35);
  stamp('DÓLAR AQUI', 290, 690, -0.1, 46, S(137));
} });

// 11 RECADO 48.15 – 56.7 (três batidas)
SC.push({ s: 48.15, e: 51.45, theme: 'dark', draw() {
  slam(S(138), 60, 330, 0, () => text('PREÇO DE ATIVO', 0, 0, 'AB', 104, WHITE, 'left', -4), .12);
  slam(S(141), 60, 460, 0, () => text('NÃO ESCOLHE', 0, 0, 'AB', 104, WHITE, 'left', -4), .12);
  if (T >= S(143)) slab('LADO.', 60, 600, 'AB', 120, INK, WHITE, prog(T, S(143), .15), 20, 14, -4);
  // ← → riscado
  if (T >= S(142)) {
    const p = prog(T, S(142), .25); c.save(); c.globalAlpha = clamp(p * 3);
    c.fillStyle = WHITE; const y = 790;
    c.beginPath(); c.moveTo(120, y); c.lineTo(250, y - 90); c.lineTo(250, y - 40); c.lineTo(450, y - 40); c.lineTo(450, y + 40); c.lineTo(250, y + 40); c.lineTo(250, y + 90); c.closePath(); c.fill();
    c.beginPath(); c.moveTo(960, y); c.lineTo(830, y - 90); c.lineTo(830, y - 40); c.lineTo(630, y - 40); c.lineTo(630, y + 40); c.lineTo(830, y + 40); c.lineTo(830, y + 90); c.closePath(); c.fill(); c.restore();
    const q = prog(T, S(143) + .05, .25); c.strokeStyle = RED; c.lineWidth = 22; c.lineCap = 'round';
    if (q > 0) { c.beginPath(); c.moveTo(380, 640); c.lineTo(380 + 320 * eOut(clamp(q * 2)), 640 + 300 * eOut(clamp(q * 2))); c.stroke(); }
    if (q > .5) { c.beginPath(); c.moveTo(700, 640); c.lineTo(700 - 320 * eOut(clamp(q * 2 - 1)), 640 + 300 * eOut(clamp(q * 2 - 1))); c.stroke(); }
  }
  slam(S(144), 60, 1070, 0, () => text('só reflete', 0, 0, 'IS', 92, WHITE), .1, 1.15);
  if (T >= S(147)) slam(S(147), 540, 1215, -0.03, () => slab('EXPECTATIVA', 0, 0, 'AB', 104, INK, YEL, prog(T, S(147), .2), 22, 16, -4, 'center'), .14, 1.8);
} });
SC.push({ s: 51.45, e: 54.0, theme: 'yellow', draw() {
  const sh = T >= S(149) && T < S(150) + .2 ? shakeAmt(9, 7) : { x: 0, y: 0 };
  at(sh.x, sh.y, 0, 1, () => {
    slam(S(148), 60, 380, -0.02, () => text('SEMANA', 0, 0, 'AB', 170, INK, 'left', -7), .12);
    if (T >= S(149)) { let x = 60; [...'AGITADA'].forEach((ch, i) => { const j = shakeAmt(40 + i, 6); text(ch, x + j.x, 560 + j.y, 'AB', 170, INK, 'left', 0); x += tw(ch, 'AB', 170, 0) - 6; }); }
  });
  slam(S(150), 60, 740, 0, () => text('NÃO É HORA', 0, 0, 'AB', 96, INK, 'left', -4), .12);
  slam(S(153), 60, 850, 0, () => text('DE DECIDIR', 0, 0, 'AB', 96, INK, 'left', -4), .12);
  if (T >= S(155)) { const sh2 = T < S(156) + .25 ? shakeAmt(11, 10) : { x: 0, y: 0 }; slam(S(155), 540 + sh2.x, 1080 + sh2.y, 0.04, () => slab('NO SUSTO.', 0, 0, 'AB', 160, YEL, INK, prog(T, S(155), .15), 26, 18, -6, 'center'), .12, 2.2); }
  const bb = boil(30, 3); slide(S(149), 830 + bb.x, 1330 + bb.y, -0.05, 600, 0, () => cutout(IMG.bull, 0, 0, 360, 0), .3);
} });
SC.push({ s: 54.0, e: 56.7, theme: 'paper', draw() {
  slam(S(157), 60, 350, 0, () => text('O PLANO', 0, 0, 'AB', 160, INK, 'left', -7), .12);
  slam(S(159), 60, 520, 0, () => text('BEM FEITO', 0, 0, 'AB', 160, INK, 'left', -7), .12);
  if (T >= S(160)) { const p = prog(T, S(160), .35); c.strokeStyle = RED; c.lineWidth = 12; c.lineCap = 'round'; c.beginPath(); c.moveTo(60, 560); for (let x = 60; x < 60 + 900 * eOut(p); x += 30) c.lineTo(x, 560 + Math.sin(x * .05) * 8); c.stroke(); }
  slam(S(161), 60, 690, 0, () => text('vale com', 0, 0, 'IS', 90, INK), .1, 1.15);
  if (T >= S(163)) slab('QUALQUER', 60, 850, 'AB', 130, WHITE, INK, prog(T, S(163), .18), 22, 14, -5);
  if (T >= S(164)) slab('RESULTADO.', 60, 1010, 'AB', 130, INK, YEL, prog(T, S(164), .18), 22, 14, -5);
  [['CENÁRIO A', 0], ['CENÁRIO B', 1]].forEach(([s, i]) => {
    const t0 = S(163) + i * .25; slam(t0, 60 + i * 500, 1200, (i ? .03 : -.03), () => {
      c.fillStyle = WHITE; c.fillRect(0, -50, 440, 100); c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(0, -50, 440, 100); c.strokeRect(24, -26, 52, 52);
      text(s, 100, 20, 'SMB', 48, INK);
      const q = prog(T, S(164) + .1 + i * .15, .2); if (q > 0) { c.strokeStyle = RED; c.lineWidth = 11; c.beginPath(); c.moveTo(26, -2); c.lineTo(26 + 18 * eOut(clamp(q * 2)), 22 * eOut(clamp(q * 2))); if (q > .5) c.lineTo(26 + 18 + 40 * eOut(clamp(q * 2 - 1)), 22 - 62 * eOut(clamp(q * 2 - 1))); c.stroke(); }
    }, .12, 1.7);
  });
} });

// 12 FIM 56.7 – 62.3
SC.push({ s: 56.7, e: 62.4, theme: 'paper', draw() {
  slam(S(165), 60, 250, 0, () => text('Ficou com alguma dúvida', 0, 0, 'IS', 66, INK), .1, 1.15);
  slam(S(169), 60, 360, 0, () => text('SOBRE A SUA', 0, 0, 'AB', 100, INK, 'left', -4), .12);
  if (T >= S(172)) slab('CARTEIRA?', 60, 490, 'AB', 120, INK, YEL, prog(T, S(172), .2), 20, 14, -5);
  const b = boil(33, 2);
  slide(56.8, 430 + b.x, 960 + b.y, -0.04 + b.r, 0, 1000, () => {
    photoPiece(IMG.lucas, 0, 0, 560, 640, 0, 61, { fy: .3 });
    tape(0, -320, 220, 0.03);
    text('com', -230, 290, 'IS', 42, INK); slab('LUCAS MEDEIROS', -160, 296, 'AB', 38, WHITE, INK, 1, 12, 8, 0);
  }, .45, eExpo);
  const bc = boil(34, 2); slide(57.2, 120 + bc.x, 1340 + bc.y, 0.2, -400, 200, () => cutout(IMG.coffee, 0, 0, 300, 0, { hard: false }), .4);
  slam(S(173), 850 + b.x, 830, 0.1, () => {
    c.save(); c.shadowColor = 'rgba(0,0,0,.35)'; c.shadowBlur = 16; c.shadowOffsetY = 10; c.fillStyle = YEL; c.fillRect(-150, -150, 300, 300); c.restore();
    text('ME', 0, -60, 'AB', 70, INK, 'center'); text('CHAMA', 0, 15, 'AB', 70, INK, 'center'); text('aqui', 0, 100, 'IS', 80, INK, 'center');
  }, .16, 2);
  scribbleArrow([[930, 1060], [960, 1200], [760, 1240]], prog(T, S(175), .45), RED, 11, 38);
  if (T >= S(180)) {
    const p = prog(T, S(180), .2);
    slam(S(180), 540, 1330, -0.04, () => slab('BOA SEMANA!', 0, 0, 'AB', 120, YEL, INK, p, 26, 18, -5, 'center'), .16, 2);
    for (let k = 0; k < 26; k++) { // confete de papel
      const tt = T - S(180); if (tt < 0) break; const a = rnd(k) * Math.PI * 2, v = 500 + rnd(k + 9) * 900;
      const x = 540 + Math.cos(a) * v * tt, y = 1330 + Math.sin(a) * v * tt + 900 * tt * tt; const col = [YEL, RED, INK, WHITE][k % 4];
      at(x, y, tt * 6 * (rnd(k + 3) - .5), 1, () => { c.fillStyle = col; c.fillRect(-14, -9, 28, 18); });
    }
  }
} });

// ---------- transições ----------
// tipo: 'torn' (folha sobe), 'slab' (bloco varre), 'flash' (inversão de 2 quadros)
const TRANS = [
  { t: 1.62, type: 'torn' }, { t: 4.5, type: 'slab', color: YEL }, { t: 12.2, type: 'flash' }, { t: 15.45, type: 'slab', color: INK },
  { t: 22.5, type: 'torn' }, { t: 27.05, type: 'slab', color: YEL }, { t: 31.4, type: 'torn' }, { t: 35.7, type: 'slab', color: RED },
  { t: 43.05, type: 'torn' }, { t: 48.15, type: 'flash' }, { t: 51.45, type: 'flash' }, { t: 54.0, type: 'slab', color: INK }, { t: 56.7, type: 'torn' },
];
const sceneIdx = t => { for (let i = SC.length - 1; i >= 0; i--) if (t >= SC[i].s) return i; return 0; };
const HUDIDX = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 11];
function drawScene(i) { const sc = SC[i]; c.save(); bg(sc.theme); sc.draw(); c.restore(); }

window.renderFrame = async function (n) {
  F = n; T = n / FPS;
  const i = sceneIdx(T), sc = SC[i];
  if (sc.s === 12.2) await need('chart'); if (sc.s === 43.05) await need('nyse');
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.filter = 'none';
  const tr = TRANS.find(k => T >= k.t - .25 && T < k.t + .35);
  if (tr && tr.type === 'torn' && T >= tr.t && T < tr.t + .32 && i > 0) {
    // cena anterior por baixo, nova sobe numa folha rasgada
    const keepT = T; T = tr.t - 1 / FPS; drawScene(i - 1); T = keepT;
    const p = eExpo(prog(T, tr.t, .32)), y0 = H * (1 - p);
    c.save(); c.beginPath(); c.moveTo(0, H); c.lineTo(0, y0);
    for (let x = 0; x <= W; x += 30) c.lineTo(x, y0 + (rnd(x + tr.t * 100) - .5) * 40); c.lineTo(W, H); c.closePath();
    c.shadowColor = 'rgba(0,0,0,.5)'; c.shadowBlur = 30; c.fillStyle = WHITE; c.fill(); c.restore();
    c.save(); c.beginPath(); c.moveTo(0, H); c.lineTo(0, y0 + 14);
    for (let x = 0; x <= W; x += 30) c.lineTo(x, y0 + 14 + (rnd(x + 7 + tr.t * 100) - .5) * 24); c.lineTo(W, H); c.closePath(); c.clip();
    drawScene(i); c.restore();
  } else drawScene(i);
  hud(sc.theme, HUDIDX[i] ?? 11);
  captions(sc.theme);
  if (tr && tr.type === 'slab') {
    const d = .2; let x0 = 0, x1 = 0;
    if (T < tr.t) { const p = eInOut(prog(T, tr.t - d, d)); x1 = W * p * 1.15; } else { const p = eInOut(prog(T, tr.t, d)); x0 = W * p * 1.15; x1 = W * 1.15; }
    if (x1 > x0) { c.save(); c.fillStyle = tr.color; c.beginPath(); c.moveTo(x0 - 120, 0); c.lineTo(x1, 0); c.lineTo(x1 - 120, H); c.lineTo(x0 - 240, H); c.closePath(); c.fill();
      c.fillStyle = INK; c.fillRect(x1 - 60, 0, 10, H); c.restore(); }
  }
  if (tr && tr.type === 'flash' && T >= tr.t && T < tr.t + 2.5 / FPS) {
    c.save(); c.globalCompositeOperation = 'difference'; c.fillStyle = '#fff'; c.fillRect(0, 0, W, H); c.restore();
  }
  grain();
};

// carregamento sob demanda dos quadros de vídeo (halftone)
async function need(name) {
  const k = footK(name), key = `${name}_${k}`;
  if (IMG[key]) return; for (const kk in IMG) if (kk.startsWith(name + '_')) delete IMG[kk];
  IMG[key] = await loadImg(`build/foot/${name}/${String(k).padStart(4, '0')}.jpg`);
}
function loadImg(src) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(src); im.src = src; }); }

(async () => {
  WORDS = await (await fetch('build/words_raw.json')).json();
  CAPS = await (await fetch('build/captions.json')).json();
  const names = ['paper.jpg', 'lula.png', 'flavio.png', 'scales.png', 'news.png', 'globe.png', 'dollars.png', 'bull.png', 'coffee.png', 'lucas.jpg', 'congresso_lilas.jpg', 'congresso_azul.jpg', 'stf.jpg'];
  await Promise.all(names.map(async n => IMG[n.split('.')[0]] = await loadImg('build/img/' + n)));
  await Promise.all(['40px "Archivo Black"', '40px Anton', '400 40px "Space Mono"', '700 40px "Space Mono"', 'italic 40px "Instrument Serif"'].map(f => document.fonts.load(f, 'ÁÉÍÓÚÃÕÇáéíóúãõç?')));
  makeGrain();
  window.READY = true;
})();
