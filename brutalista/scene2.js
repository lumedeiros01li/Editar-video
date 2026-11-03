// Morning Call 03/11 — edição "Vox colagem + Brutalista" (imagens em cores)
// Render determinístico: window.renderFrame(n) desenha o quadro n (30 fps) no canvas.
const W = 1080, H = 1920, FPS = 30, DUR = 52.1;
const cv = document.getElementById('c'), c = cv.getContext('2d');

// ---------- paleta ----------
const INK = '#111111', PAPER = '#EEE9DE', WHITE = '#FAF8F2', YEL = '#F6E31B', RED = '#FF3B1F', GRAY = '#8A877F', TEAL = '#0C2C38';

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
  else { if (theme === 'dark') { const g = c.createRadialGradient(540, 700, 80, 540, 900, 1300); g.addColorStop(0, '#16505F'); g.addColorStop(1, TEAL); c.fillStyle = g; } else c.fillStyle = YEL; c.fillRect(0, 0, W, H); c.save(); c.globalAlpha = .18; c.globalCompositeOperation = 'multiply'; c.drawImage(IMG.paper, 0, 0, W, H); c.restore(); }
  // grade brutalista exposta
  c.save(); c.strokeStyle = theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.055)'; c.lineWidth = 2;
  for (let x = 60; x < W; x += 120) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, H); c.stroke(); }
  for (let y = 0; y < H; y += 120) { c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
  c.restore();
}
function grain() {
  c.save(); c.globalAlpha = .07; c.globalCompositeOperation = 'overlay'; c.drawImage(GRAIN[Math.floor(F / 2) % 4], 0, 0, W, H); c.restore();
}
function hud(theme, idx) {
  const fg = theme === 'dark' ? WHITE : INK, bgc = theme === 'dark' ? WHITE : INK, inv = theme === 'dark' ? INK : (theme === 'yellow' ? YEL : PAPER);
  c.fillStyle = bgc; c.fillRect(40, 52, tw('MORNING CALL', 'AB', 26, 1) + 28, 46);
  text('MORNING CALL', 54, 85, 'AB', 26, inv, 'left', 1);
  text('TER 03.11.26', 70 + tw('MORNING CALL', 'AB', 26, 1) + 28, 84, 'SMB', 24, fg);
  const tc = `${String(Math.floor(T / 60)).padStart(2, '0')}:${String(Math.floor(T % 60)).padStart(2, '0')}:${String(F % 30).padStart(2, '0')}`;
  text(tc, W - 40, 84, 'SM', 24, fg, 'right');
  text(`[${String(idx + 1).padStart(2, '0')}/15] ${SC[idx].name}`, W - 40, 128, 'SMB', 20, theme === 'dark' ? '#bbb' : '#555', 'right');
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
// VÍDEO 2 — palavras (tempos da narração), helpers e cenas
// =====================================================================
const norm = s => s.toLowerCase().replace(/[.,?!:;"]/g, '');
function wd(str, after = 0) {
  const n = norm(str), w = WORDS.find(w => w.s >= after - 0.01 && norm(w.w) === n);
  if (!w) throw new Error('palavra não encontrada: ' + str + ' após ' + after); return w;
}
const ws = (s, a = 0) => wd(s, a).s, we = (s, a = 0) => wd(s, a).e;

// ---------- peças novas ----------
function marquee(str, y, rot, speed, size, fg, bgc, t0, t1 = 999) {
  if (T < t0 || T > t1) return; const p = eExpo(prog(T, t0, .3));
  at(540, y, rot, 1, () => {
    c.fillStyle = bgc; c.fillRect(-700, -size * .9, 1400 * p, size * 1.6);
    c.save(); c.beginPath(); c.rect(-700, -size, 1400 * p, size * 2); c.clip();
    const unit = tw(str, 'AB', size, 0); const off = ((T * speed) % unit + unit) % unit;
    for (let x = -700 - off; x < 700; x += unit) text(str, x, size * .36, 'AB', size, fg);
    c.restore();
  });
}
function check(cx, cy, s, color = RED, lw = 12, p = 1) {
  if (p <= 0) return; c.save(); c.strokeStyle = color; c.lineWidth = lw; c.lineCap = 'round'; c.lineJoin = 'round'; c.beginPath();
  const a = [cx - s * .5, cy], b = [cx - s * .15, cy + s * .38], d = [cx + s * .55, cy - s * .45];
  const q1 = clamp(p * 2), q2 = clamp(p * 2 - 1);
  c.moveTo(a[0], a[1]); c.lineTo(lerp(a[0], b[0], q1), lerp(a[1], b[1], q1)); if (q2 > 0) c.lineTo(lerp(b[0], d[0], q2), lerp(b[1], d[1], q2)); c.stroke(); c.restore();
}
function upArrow(cx, cy, s, color) { at(cx, cy, Math.PI, 1, () => downArrow(0, 0, s, color)); }
function tagBox(label, x, y, rot, t0, size = 50, o = {}) {   // etiqueta com caixa e sombra dura
  slam(t0, x, y, rot, () => {
    const w = tw(label, 'SMB', size) + (o.check ? 130 : 60), h = size * 1.7;
    c.fillStyle = INK; c.fillRect(10, -h / 2 + 10, w, h); c.fillStyle = o.bg || WHITE; c.fillRect(0, -h / 2, w, h);
    c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(0, -h / 2, w, h);
    if (o.check) { c.strokeRect(22, -size * .36, size * .72, size * .72); check(22 + size * .36, 0, size * .55, RED, 9, prog(T, t0 + .15, .2)); }
    text(label, o.check ? 22 + size * .72 + 20 : 30, size * .34, 'SMB', size, o.fg || INK);
  }, .14, 1.7);
}
function calTag(cx, cy, rot, dow, day, t0, sc = 1) {
  slam(t0, cx, cy, rot, () => at(0, 0, 0, sc, () => {
    c.fillStyle = INK; c.fillRect(-120 + 12, -140 + 14, 240, 280); c.fillStyle = WHITE; c.fillRect(-120, -140, 240, 280);
    c.fillStyle = RED; c.fillRect(-120, -140, 240, 82); c.strokeStyle = INK; c.lineWidth = 7; c.strokeRect(-120, -140, 240, 280);
    text(dow, 0, -80, 'AB', 50, WHITE, 'center', 3); text(day, 0, 80, 'AN', 120, INK, 'center');
  }), .16, 1.9);
}
function sticky(cx, cy, w, rot, t0, lines) {
  slam(t0, cx, cy, rot, () => {
    c.save(); c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 16; c.shadowOffsetY = 12; c.fillStyle = YEL; c.fillRect(-w / 2, -w / 2, w, w); c.restore();
    c.fillStyle = 'rgba(0,0,0,.08)'; c.beginPath(); c.moveTo(w / 2, w / 2 - 70); c.lineTo(w / 2 - 70, w / 2); c.lineTo(w / 2, w / 2); c.fill();
    lines.forEach(([s, f, sz, dy]) => text(s, 0, dy, f, sz, INK, 'center'));
  }, .16, 2);
}
function bubble(cx, cy, w, h, rot, t0, label, tailDir = 1) {
  slam(t0, cx, cy, rot, () => {
    c.fillStyle = INK; c.fillRect(-w / 2 + 10, -h / 2 + 10, w, h); c.fillStyle = WHITE; c.fillRect(-w / 2, -h / 2, w, h);
    c.beginPath(); c.moveTo(tailDir * w * .18, h / 2); c.lineTo(tailDir * w * .34, h / 2 + 50); c.lineTo(tailDir * w * .34 + tailDir * -50, h / 2); c.closePath(); c.fillStyle = WHITE; c.fill();
    c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(-w / 2, -h / 2, w, h);
    text(label, 0, 14, 'AB', 54, INK, 'center');
    for (let i = 0; i < 3; i++) { const on = (Math.floor((T - t0) * 6) % 4) > i; c.fillStyle = on ? INK : '#bbb'; c.beginPath(); c.arc(-34 + i * 34, 52, 8, 0, 7); c.fill(); }
  }, .14, 1.6);
}

// gráfico em degraus da Selic (desenhado em canvas)
function selicChart(x, y, w, h, p, o = {}) {
  const lv = [[0, .02], [.08, .22], [.15, .45], [.22, .7], [.28, 1], [.55, .88], [.63, .77], [.70, .66], [.77, .55], [.84, .46]];
  const X = u => x + u * w * .88, Y = v => y + h - v * h;
  const pts = [], at_ = []; // at_[i] = índice do ponto do degrau i
  for (let i = 0; i < lv.length; i++) { if (i > 0) pts.push([X(lv[i][0]), Y(lv[i - 1][1])]); pts.push([X(lv[i][0]), Y(lv[i][1])]); at_[i] = pts.length - 1; }
  pts.push([X(.9), Y(lv[lv.length - 1][1])]); at_.push(pts.length - 1);
  const cum = [0]; for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const L = cum[cum.length - 1] * clamp(p);
  // base e rótulos
  c.fillStyle = INK; c.fillRect(x, y + h + 34, w, 6);
  text('2025', X(.2), y + h + 80, 'SMB', 26, INK, 'center'); text('2026', X(.62), y + h + 80, 'SMB', 26, INK, 'center');
  text('TAXA SELIC (META)', x, y - 24, 'SMB', 26, INK);
  c.fillStyle = INK; for (const u of [.2, .62]) c.fillRect(X(u) - 2, y + h + 34, 4, 18);
  // linha
  c.save(); c.strokeStyle = INK; c.lineWidth = 13; c.lineJoin = 'miter'; c.lineCap = 'butt'; c.beginPath(); c.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) { if (cum[i] <= L) c.lineTo(pts[i][0], pts[i][1]); else { const q = (L - cum[i - 1]) / (cum[i] - cum[i - 1]); if (q > 0) c.lineTo(lerp(pts[i - 1][0], pts[i][0], q), lerp(pts[i - 1][1], pts[i][1], q)); break; } }
  c.stroke(); c.restore();
  // pontos amarelos dos cortes
  for (let i = 5; i < lv.length; i++) { const k = at_[i]; if (cum[k] <= L) { const born = (cum[k] / cum[cum.length - 1]); const sc = o.static ? 1 : eBack(clamp((p - born) / .06));
    at(pts[k][0], pts[k][1], 0, sc, () => { c.fillStyle = YEL; c.beginPath(); c.arc(0, 0, 22, 0, 7); c.fill(); c.strokeStyle = INK; c.lineWidth = 7; c.stroke(); }); } }
  const last = pts[at_[lv.length - 1]];
  if (p >= .999 && o.label !== false) { slam(o.labelT ?? T - 1, last[0] - 10, last[1] - 70, -0.04, () => slab('13,75%', 0, 0, 'AB', 54, WHITE, INK, 1, 12, 8, -1), .15, 1.6); }
  // projeção: queda "atrasada"
  if (o.proj) {
    const pr = o.proj; const ex = X(.97), ey = Y(.30);
    c.save(); c.setLineDash([14, 12]); c.lineWidth = 7; c.strokeStyle = INK; c.globalAlpha = .6 * (1 - clamp(o.cancel || 0) * .6);
    c.beginPath(); c.moveTo(last[0], last[1]); c.lineTo(lerp(last[0], ex, clamp(pr)), lerp(last[1], ey, clamp(pr))); c.stroke(); c.restore();
    if (o.cancel) { const q = eBack(clamp(o.cancel)); at(ex, ey, 0, q, () => { c.strokeStyle = RED; c.lineWidth = 14; c.lineCap = 'round'; c.beginPath(); c.moveTo(-30, -30); c.lineTo(30, 30); c.moveTo(30, -30); c.lineTo(-30, 30); c.stroke(); }); }
    if (o.flat) { c.save(); c.setLineDash([14, 12]); c.lineWidth = 8; c.strokeStyle = INK; const fx = lerp(last[0] + 140, X(.99), clamp(o.flat)); c.beginPath(); c.moveTo(last[0] + 140, last[1]); c.lineTo(fx, last[1]); c.stroke(); c.restore();
      if (o.flat > .98) { c.fillStyle = WHITE; c.beginPath(); c.arc(X(.99), last[1], 20, 0, 7); c.fill(); c.strokeStyle = INK; c.lineWidth = 7; c.stroke(); } }
  }
}

// fundo de números rolando (dark)
function tickerBG() {
  const cols = [[90, 1.0, 66], [380, 1.55, 90], [690, .8, 62], [940, 1.3, 78]];
  c.save(); c.textAlign = 'center';
  cols.forEach(([x, sp, sz], ci) => {
    const row = sz * 1.9, N = Math.ceil(H / row) + 3, total = N * row;
    for (let k = 0; k < N; k++) {
      const yy = ((k * row - T * sp * 150) % total + total) % total - row;
      const val = Math.floor(rnd(ci * 977 + k * 13 + Math.floor(((k * row - T * sp * 150) / total)) * 7) * 9e6 + 1e4);
      const s = val.toLocaleString('pt-BR'), a = .1 + rnd(ci * 31 + k) * .35;
      c.globalAlpha = a; setFont('SM', sz); c.fillStyle = rnd(k + ci) > .86 ? YEL : '#9fd6e6'; c.fillText(s, x, yy);
    }
  });
  c.restore();
}

// urna de votação + cédula
function ballotBox(cx, cy, t0) {
  at(cx, cy, 0, 1, () => {
    const q = clamp((T - t0) / .5), drop = eInOut(q);
    c.fillStyle = INK; c.fillRect(-100 + 10, -20 + 10, 200, 140); c.fillStyle = RED; c.fillRect(-100, -20, 200, 140); c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(-100, -20, 200, 140);
    c.fillStyle = INK; c.fillRect(-60, -20, 120, 14);
    if (q > 0 && q < 1) { c.save(); c.beginPath(); c.rect(-80, -140, 160, 126); c.clip(); c.fillStyle = WHITE; c.fillRect(-45, -120 + drop * 110, 90, 120); c.strokeStyle = INK; c.lineWidth = 5; c.strokeRect(-45, -120 + drop * 110, 90, 120); c.restore(); }
    text('VOTO', 0, 90, 'AB', 40, WHITE, 'center', 2);
  });
}
function refreshArrows(cx, cy, r, t0) {
  if (T < t0) return; const p = eOut(prog(T, t0, .3)), rot = (T - t0) * 3.2;
  at(cx, cy, rot, p, () => { c.strokeStyle = RED; c.lineWidth = 22; c.lineCap = 'butt';
    for (const a0 of [0.3, Math.PI + 0.3]) { c.beginPath(); c.arc(0, 0, r, a0, a0 + 2.3); c.stroke(); const ae = a0 + 2.3, ex = Math.cos(ae) * r, ey = Math.sin(ae) * r;
      c.fillStyle = RED; at(ex, ey, ae + Math.PI / 2, 1, () => { c.beginPath(); c.moveTo(-32, 0); c.lineTo(32, 0); c.lineTo(0, 46); c.closePath(); c.fill(); }); } });
}
function coins(t0, t1, x0, y0) {
  for (let i = 0; i < 9; i++) {
    const t = t0 + i * .1; if (T < t || T > t1) continue; const q = (T - t) / .9, x = x0 + (rnd(i * 7) - .5) * 360, y = y0 - q * 380;
    c.save(); c.globalAlpha = 1 - q * .6; at(x, y, q * 3, 1, () => { c.fillStyle = YEL; c.beginPath(); c.arc(0, 0, 34, 0, 7); c.fill(); c.strokeStyle = INK; c.lineWidth = 6; c.stroke(); text('$', 0, 14, 'AB', 40, INK, 'center'); }); c.restore();
  }
}

// ---------- cenas ----------
const SC = [];

// 1 ABERTURA 0 – 4.25
SC.push({ s: 0, e: 4.25, theme: 'paper', name: 'ABERTURA', draw() {
  const cyR = 1250;
  for (let i = 5; i >= 1; i--) { const pr = eOut(prog(T, .15 + (5 - i) * .06, .5)), r = (i * 104 + Math.sin(T * 3 + i) * 5) * pr;
    c.fillStyle = i % 2 ? YEL : '#F9EE74'; c.beginPath(); c.arc(540, cyR, r, 0, 7); c.fill(); c.strokeStyle = INK; c.lineWidth = 4; c.stroke(); }
  const b = boil(1, 2);
  slide(.3, 540 + b.x, 1135 + b.y, b.r, 0, 800, () => cutout(IMG.lucas_busto, 0, 0, 620, 0), .5, eExpo);
  c.fillStyle = INK; c.fillRect(0, 1428, W, 54); if (T > .6) text('MORNING CALL  //  TERÇA 03.11  //  MORNING CALL  //  TERÇA 03.11', -((T * 120) % 600), 1465, 'SMB', 28, YEL);
  slam(ws('Bom'), 70, 330, -0.02, () => text('BOM', 0, 0, 'AB', 210, INK, 'left', -9), .14);
  if (T >= ws('dia')) slab('DIA.', 70, 520, 'AB', 210, YEL, INK, prog(T, ws('dia'), .22), 24, 16, -8);
  slam(.95, 70, 650, 0, () => text('Morning Call', 0, 0, 'IS', 118, INK), .12, 1.2);
  slam(1.2, 76, 708, 0, () => slab('COM LUCAS MEDEIROS', 0, 0, 'SMB', 30, WHITE, INK, 1, 14, 8, 0), .1, 1.2);
  if (T >= ws('Terça-feira')) slab('TERÇA-FEIRA DE DECISÕES,', 60, 805, 'AB', 50, WHITE, INK, prog(T, ws('Terça-feira'), .25), 16, 10, -1);
  if (T >= ws('aqui', 2.5)) slab('AQUI E LÁ FORA.', 60, 885, 'AB', 64, INK, YEL, prog(T, ws('aqui', 2.5), .25), 18, 12, -2);
} });

// 2 BANCO CENTRAL 4.25 – 6.3
SC.push({ s: 4.25, e: 6.3, theme: 'paper', name: 'BANCO CENTRAL', draw() {
  const b = boil(5, 1.5);
  slam(ws('Aqui', 4), 60, 240, 0, () => text('Aqui no Brasil,', 0, 0, 'IS', 78, INK), .1, 1.15);
  slide(4.3, 540 + b.x, 775 + b.y, -0.025 + b.r, -900, 0, () => photoPiece(IMG.bc, 0, 0, 980, 930, 0, 61, { fy: .3 }), .4);
  tape(190, 320, 200, -0.4); tape(900, 300, 200, 0.4);
  calTag(880, 400, 0.1, 'QUA', '04/11', ws('quarta', 4), .8);
  slam(ws('quarta', 4), 60, 1325, 0, () => text('A QUARTA É DIA DO', 0, 0, 'AB', 76, INK, 'left', -3), .12);
  if (T >= ws('Banco', 5)) slab('BANCO CENTRAL', 60, 1440, 'AB', 104, YEL, INK, prog(T, ws('Banco', 5), .22), 20, 14, -4);
  scribbleCircle(470, 970, 190, 270, prog(T, ws('Central', 5), .5), 8);
} });

// 3 CONGRESSO / JUROS 6.3 – 8.3
SC.push({ s: 6.3, e: 8.3, theme: 'paper', name: 'DECISÃO', draw() {
  const b = boil(6, 1.5);
  slam(ws('decidir'), 60, 275, 0, () => text('DECIDIR O QUE', 0, 0, 'AB', 90, INK, 'left', -4), .12);
  slam(ws('fazer'), 60, 375, 0, () => text('FAZER COM OS', 0, 0, 'AB', 90, INK, 'left', -4), .12);
  slide(6.35, 540 + b.x, 870 + b.y, 0.02 + b.r, 900, 0, () => photoPiece(IMG.cong, 0, 0, 900, 880, 0, 71, { fy: .45 }), .4);
  tape(190, 440, 190, -0.3);
  const tj = ws('juros', 7), sh = T >= tj && T < tj + .35 ? shakeAmt(4, 7) : { x: 0, y: 0 };
  if (T >= tj) slam(tj, 70 + sh.x, 1360 + sh.y, -0.03, () => slab('JUROS', 0, 0, 'AB', 250, YEL, INK, prog(T, tj, .2), 26, 18, -10), .16, 2.2);
  if (T >= tj + .15) at(900, 640, 0.2, eBack(prog(T, tj + .15, .2)), () => { c.fillStyle = RED; c.beginPath(); for (let i = 0; i < 24; i++) { const r = i % 2 ? 100 : 150, a = i / 24 * Math.PI * 2; c.lineTo(Math.cos(a) * r, Math.sin(a) * r); } c.closePath(); c.fill(); c.strokeStyle = INK; c.lineWidth = 7; c.stroke(); text('%', 0, 38, 'AB', 130, WHITE, 'center'); });
} });

// 4 APOSTA (esplanada) 8.3 – 11.0
SC.push({ s: 8.3, e: 11.0, theme: 'dark', name: 'APOSTA', draw() {
  const b = boil(7, 1.5);
  slam(ws('maioria'), 60, 290, 0, () => text('A MAIORIA', 0, 0, 'AB', 104, WHITE, 'left', -4), .12);
  slam(ws('mercado'), 60, 395, 0, () => text('DO MERCADO', 0, 0, 'AB', 104, WHITE, 'left', -4), .12);
  slam(ws('aposta'), 60, 490, 0, () => text('aposta que ele vai', 0, 0, 'IS', 78, YEL), .1, 1.15);
  slide(8.4, 540 + b.x, 900 + b.y, -0.02 + b.r, 0, 800, () => photoPiece(IMG.esp, 0, 0, 940, 640, 0, 81, { fy: .55 }), .4);
  tape(150, 590, 180, -0.35);
  const tm = ws('manter', 9);
  tagBox('CORTAR', 60, 1300, -0.02, ws('mercado'), 56, { bg: WHITE });
  if (T >= tm - .05) { const q = prog(T, tm, .2); c.save(); c.strokeStyle = RED; c.lineWidth = 12; c.beginPath(); c.moveTo(40, 1300); c.lineTo(40 + 330 * eOut(q), 1300); c.stroke(); c.restore(); }
  slam(tm, 520, 1300, 0.02, () => { const w = 480, h = 150; c.fillStyle = '#000'; c.fillRect(10, -h / 2 + 10, w, h); c.fillStyle = YEL; c.fillRect(0, -h / 2, w, h); c.strokeStyle = INK; c.lineWidth = 7; c.strokeRect(0, -h / 2, w, h);
    text('MANTER', 30, 30, 'AB', 82, INK, 'left', -2); check(w - 70, -2, 90, INK, 16, prog(T, tm + .15, .25)); }, .16, 1.8);
  if (T >= we('como', 10)) slam(ws('como', 10), 540, 1415, -0.03, () => text('como está', 0, 0, 'IS', 66, WHITE), .1, 1.15);
} });

// 5 SELIC (cortes) 11.0 – 12.7
SC.push({ s: 11.0, e: 12.7, theme: 'paper', name: 'SELIC', draw() {
  slam(ws('depois'), 60, 290, 0, () => text('depois de', 0, 0, 'IS', 82, INK), .1, 1.15);
  slam(ws('vários'), 60, 450, 0, () => text('VÁRIOS', 0, 0, 'AB', 170, INK, 'left', -8), .14);
  if (T >= ws('cortes')) slab('CORTES SEGUIDOS.', 60, 590, 'AB', 88, YEL, INK, prog(T, ws('cortes'), .22), 20, 14, -3);
  selicChart(70, 800, 940, 470, prog(T, 11.05, 1.45), { labelT: 12.55 });
} });

// 6 RENDA FIXA (números) 12.7 – 16.1
SC.push({ s: 12.7, e: 16.1, theme: 'dark', name: 'RENDA FIXA', draw() {
  tickerBG();
  slam(ws('Para'), 60, 300, 0, () => text('Para você,', 0, 0, 'IS', 92, WHITE), .1, 1.15);
  slam(ws('isso'), 60, 410, 0, () => text('ISSO IMPORTA:', 0, 0, 'AB', 100, WHITE, 'left', -4), .12);
  const tj = ws('juro', 13.5), ta = ws('alto', 13.9);
  if (T >= tj) slab('JURO', 60, 640, 'AB', 190, YEL, INK, prog(T, tj, .2), 24, 16, -8);
  if (T >= ta) slab('ALTO', 60, 830, 'AB', 190, WHITE, INK, prog(T, ta, .2), 24, 16, -8);
  if (T >= ta + .1) upArrow(900, 740, 230, YEL);
  slam(ws('faz'), 60, 990, 0, () => text('FAZ A RENDA FIXA', 0, 0, 'AB', 78, WHITE, 'left', -3), .12);
  const tr = ws('render', 14.5);
  if (T >= tr) slab('RENDER MAIS', 60, 1150, 'AB', 112, INK, YEL, prog(T, tr, .2), 22, 14, -5);
  coins(tr, 16.1, 760, 1300);
  stamp('RENDA FIXA', 790, 1345, 0.08, 46, ws('renda'));
} });

// 7 DÓLAR NERVOSO (gráfico) 16.1 – 19.7
SC.push({ s: 16.1, e: 19.7, theme: 'paper', name: 'DÓLAR', draw() {
  const td = ws('dólar', 16), sh = T >= td ? shakeAmt(9, 5) : { x: 0, y: 0 };
  slam(ws('E', 16), 60, 255, 0, () => text('e o', 0, 0, 'IS', 76, INK), .1, 1.15);
  if (T >= td) slam(td, 60 + sh.x, 385 + sh.y, 0, () => text('DÓLAR', 0, 0, 'AB', 150, INK, 'left', -7), .12);
  if (T >= ws('nervoso')) slam(ws('nervoso'), 60 + sh.x * 1.3, 520 + sh.y, 0, () => text('NERVOSO', 0, 0, 'AB', 150, RED, 'left', -7), .12);
  // moeda tremendo
  const mc = shakeAmt(5, 8); if (T >= td) at(900 + mc.x, 300 + mc.y, .12, eBack(prog(T, td, .25)), () => { c.fillStyle = YEL; c.beginPath(); c.arc(0, 0, 90, 0, 7); c.fill(); c.strokeStyle = INK; c.lineWidth = 9; c.stroke(); text('$', 0, 40, 'AB', 120, INK, 'center'); c.fillStyle = '#4aa8ff'; for (const [dx, dy] of [[-110, -40], [112, -10], [90, 64]]) { c.beginPath(); c.arc(dx, dy + Math.sin(T * 14 + dx) * 6, 9, 0, 7); c.fill(); } });
  slam(ws('dos', 16.5), 60, 610, 0, () => text('dos últimos dias', 0, 0, 'IS', 60, INK), .1, 1.1);
  if (T >= ws('pode')) slab('PODE ATRASAR', 60, 740, 'AB', 104, YEL, INK, prog(T, ws('pode'), .22), 20, 14, -4);
  slam(ws('queda'), 60, 840, 0, () => text('A QUEDA DESSE JURO.', 0, 0, 'AB', 64, INK, 'left', -2), .1, 1.2);
  selicChart(70, 1010, 940, 330, 1, { static: true, proj: prog(T, ws('pode'), .4), cancel: prog(T, ws('atrasar'), .3), flat: prog(T, ws('queda'), .9), labelT: 16.5 });
} });

// 8 PETRÓLEO respirou 19.7 – 21.8
SC.push({ s: 19.7, e: 21.8, theme: 'paper', name: 'PETRÓLEO', draw() {
  const b = boil(8, 1.5), tr = ws('respirada');
  slam(ws('Lá', 19.5), 60, 330, 0, () => text('LÁ FORA,', 0, 0, 'AB', 150, INK, 'left', -7), .12);
  slam(ws('petróleo'), 60, 450, 0, () => text('O PETRÓLEO', 0, 0, 'AB', 104, INK, 'left', -4), .12);
  slam(ws('deu'), 60, 545, 0, () => text('deu uma', 0, 0, 'IS', 84, INK), .1, 1.15);
  if (T >= tr) slab('RESPIRADA.', 60, 690, 'AB', 138, YEL, INK, prog(T, tr, .22), 22, 14, -6);
  const br = T < tr ? 1 - .03 * eOut(prog(T, 19.8, .6)) : 1 + .05 * Math.sin((T - tr) * 7) * Math.exp(-(T - tr) * 1.2) + .01;
  slide(19.75, 540 + b.x, 1080 + b.y, -0.015 + b.r, 0, 900, () => at(0, 0, 0, br, () => photoPiece(IMG.oil, 0, 0, 940, 690, 0, 91, { fy: .35 })), .4);
  tape(160, 760, 190, -0.3); tape(920, 760, 190, 0.3);
  if (T >= tr) for (let i = 0; i < 3; i++) { const q = clamp((T - tr - i * .12) / .8); if (q <= 0) continue; c.save(); c.globalAlpha = (1 - q) * .9; text('PHHH', 790 + q * 120 + i * 20, 560 - q * 90 + i * 36, 'AB', 48 + i * 8, RED, 'left', 3); c.restore(); }
} });

// 9 ORMUZ 21.8 – 25.8
const ROUTE = [[60, 720], [190, 655], [365, 580], [480, 540], [665, 595], [755, 775], [890, 1025]];
function routePoint(u) {
  const L = []; let tot = 0; for (let i = 1; i < ROUTE.length; i++) { const d = Math.hypot(ROUTE[i][0] - ROUTE[i - 1][0], ROUTE[i][1] - ROUTE[i - 1][1]); L.push(d); tot += d; }
  let r = u * tot; for (let i = 0; i < L.length; i++) { if (r <= L[i]) { const q = r / L[i]; return [lerp(ROUTE[i][0], ROUTE[i + 1][0], q), lerp(ROUTE[i][1], ROUTE[i + 1][1], q)]; } r -= L[i]; }
  return ROUTE[ROUTE.length - 1];
}
SC.push({ s: 21.8, e: 25.8, theme: 'dark', name: 'ORMUZ', draw() {
  const b = boil(9, 1.5);
  slam(ws('Na', 21.5), 60, 250, 0, () => text('Na segunda, ele', 0, 0, 'IS', 78, WHITE), .1, 1.15);
  slide(21.85, 540 + b.x, 760 + b.y, 0.015 + b.r, 0, 900, () => photoPiece(IMG.mapa, 0, 0, 1000, 880, 0, 101, { fy: .3, zoom: 1 }), .4);
  // rota tracejada + navio
  const u = clamp((T - 22.0) / 3.5), n = 80;
  c.save(); c.strokeStyle = WHITE; c.lineWidth = 8; c.setLineDash([22, 16]); c.beginPath(); for (let i = 0; i <= n * u; i++) { const p = routePoint(i / n); i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); } c.stroke(); c.restore();
  const sp = routePoint(eInOut(u)); at(sp[0], sp[1], Math.sin(T * 3) * .04, 1, () => { c.drawImage(IMG.ship, -135, -95, 270, 270 * IMG.ship.height / IMG.ship.width); });
  slam(22.4, 80, 380, -0.03, () => slab('ESTREITO DE ORMUZ', 0, 0, 'SMB', 32, WHITE, INK, 1, 14, 8, 0), .1, 1.2);
  const tc = ws('caiu');
  if (T >= tc) slam(tc, 60, 1130, -0.03, () => { const p = prog(T, tc, .2); slab('CAIU FORTE', 0, 0, 'AB', 118, WHITE, RED, p, 22, 14, -4); }, .16, 2);
  if (T >= ws('forte')) { const q = eBack(prog(T, ws('forte'), .25)); at(950, 1190 + Math.sin((T - tc) * 8) * 6, 0, q, () => downArrow(0, 0, 190, RED)); }
  tagBox('ESTADOS UNIDOS', 60, 1290, -0.02, ws('Estados'), 46, { bg: WHITE });
  tagBox('IRÃ', 650, 1290, 0.025, ws('Irã'), 46, { bg: WHITE });
  if (T >= ws('Irã')) text('e', 600, 1305, 'IS', 62, WHITE, 'center');
  bubble(250, 860, 250, 120, -0.05, ws('sentar'), 'EUA', 1); bubble(820, 560, 230, 120, 0.05, ws('conversar') - .05, 'IRÃ', -1);
  if (T >= ws('sentar')) slab('PODEM SENTAR PRA CONVERSAR', 60, 1400, 'AB', 52, INK, YEL, prog(T, ws('sentar'), .25), 16, 10, -1);
} });

// 10 COMBUSTÍVEL 25.8 – 31.0
SC.push({ s: 25.8, e: 31.0, theme: 'paper', name: 'COMBUSTÍVEL', draw() {
  const b = boil(10, 1.5);
  slide(25.85, 540 + b.x, 470 + b.y, 0.015 + b.r, 0, -900, () => photoPiece(IMG.tanker, 0, 0, 960, 640, 0, 111, { fy: .5 }), .4);
  tape(150, 170, 190, -0.4); tape(930, 180, 190, 0.4);
  slam(ws('Petróleo', 25.5), 60, 930, 0, () => text('PETRÓLEO', 0, 0, 'AB', 126, INK, 'left', -6), .12);
  if (T >= ws('barato')) slab('MAIS BARATO', 60, 1050, 'AB', 118, YEL, INK, prog(T, ws('barato'), .22), 22, 14, -5);
  // etiqueta de preço despencando
  const tb = ws('barato'); if (T >= tb) { const q = eOut(clamp((T - tb) / .5)), sh = shakeAmt(8, 3 * (1 - q)); at(880 + sh.x, 520 + q * 170 + sh.y, .15, 1, () => { c.fillStyle = INK; c.fillRect(-70 + 8, -50 + 8, 140, 100); c.fillStyle = WHITE; c.fillRect(-70, -50, 140, 100); c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(-70, -50, 140, 100); downArrow(0, 0, 70, RED); }); }
  slam(ws('alivia'), 60, 1135, 0, () => text('alivia', 0, 0, 'IS', 70, INK), .1, 1.15);
  tagBox('COMBUSTÍVEL', 60, 1225, -0.02, ws('combustível'), 44, { check: true });
  tagBox('PREÇOS', 640, 1225, 0.025, ws('preços'), 44, { check: true });
  slam(ws('mas'), 60, 1330, 0, () => text('mas ele muda', 0, 0, 'IS', 62, INK), .1, 1.1);
  if (T >= ws('notícia')) slab('A CADA NOTÍCIA.', 60, 1430, 'AB', 88, WHITE, INK, prog(T, ws('notícia'), .22), 18, 12, -3);
  const flash = Math.floor(F / 4) % 2; marquee('ÚLTIMA HORA ▲▼  ', 765, -0.04, 260, 46, flash ? WHITE : INK, flash ? RED : YEL, ws('cada'), 31);
} });

// 11 ELEIÇÃO EUA 31.0 – 35.8
SC.push({ s: 31.0, e: 35.8, theme: 'paper', name: 'ELEIÇÃO EUA', draw() {
  const b = boil(11, 1.5);
  slam(ws('E', 30.9), 60, 250, 0, () => text('e hoje os americanos', 0, 0, 'IS', 70, INK), .1, 1.15);
  if (T >= ws('votam')) slam(ws('votam'), 60, 380, 0, () => text('VOTAM', 0, 0, 'AB', 140, INK, 'left', -7), .12);
  ballotBox(900, 330, ws('votam'));
  slide(31.05, 540 + b.x, 840 + b.y, -0.015 + b.r, 0, 900, () => photoPiece(IMG.capitolio, 0, 0, 960, 780, 0, 121, { fy: .3 }), .4);
  stamp('HOJE', 200, 560, -0.12, 70, ws('hoje'));
  refreshArrows(850, 960, 100, ws('renovam'));
  slam(ws('nas'), 60, 1330, 0, () => text('NAS ELEIÇÕES DE', 0, 0, 'AB', 72, INK, 'left', -3), .12);
  if (T >= ws('meio')) slab('MEIO DE MANDATO,', 60, 1430, 'AB', 84, YEL, INK, prog(T, ws('meio'), .25), 18, 12, -3);
} });

// 12 EMPREGO (Fed + multidão) 35.8 – 40.2
SC.push({ s: 35.8, e: 40.2, theme: 'paper', name: 'EMPREGO', draw() {
  const b = boil(12, 1.5);
  slide(35.85, 540 + b.x, 450 + b.y, -0.015 + b.r, 0, -900, () => photoPiece(IMG.fed, 0, 0, 940, 580, 0, 131, { fy: .4 }), .4);
  tape(150, 170, 190, -0.4);
  calTag(900, 700, 0.1, 'SEX', '06/11', ws('sexta'), .7);
  slam(ws('sexta'), 60, 830, 0, () => text('Na sexta', 0, 0, 'IS', 70, INK), .1, 1.15);
  slam(ws('saem'), 60, 920, 0, () => text('SAEM OS DADOS', 0, 0, 'AB', 80, INK, 'left', -3), .12);
  if (T >= ws('emprego')) slab('DE EMPREGO', 60, 1020, 'AB', 90, YEL, INK, prog(T, ws('emprego'), .22), 20, 12, -3);
  slide(37.45, 540 + b.x, 1290 + b.y, 0.02 + b.r, 700, 0, () => photoPiece(IMG.crowd_a, 0, 0, 900, 350, 0, 141, { fy: .45 }), .35);
  slam(ws('de', 37.3), 60, 1085, 0, () => text('de lá, que também mexem com o', 0, 0, 'IS', 56, INK), .1, 1.1);
  const td = ws('dólar', 38.5);
  if (T >= td) slam(td, 540, 1440, -0.03, () => slab('DÓLAR AQUI.', 0, 0, 'AB', 112, YEL, INK, prog(T, td, .22), 22, 14, -4, 'center'), .16, 2);
} });

// 13 TRÊS ASSUNTOS 40.2 – 44.5
SC.push({ s: 40.2, e: 44.5, theme: 'dark', name: '3 ASSUNTOS', draw() {
  const cards = [[IMG.bc, 'JUROS', ws('Juros', 40), 200, -0.05, .65], [IMG.mapa, 'PETRÓLEO', ws('petróleo', 40), 540, 0.03, .3], [IMG.capitolio, 'ELEIÇÃO\nAMERICANA', ws('eleição'), 880, -0.025, .2]];
  cards.forEach(([img, label, t0, cx, rot, fy], i) => {
    const bb = boil(20 + i, 1.5);
    slide(t0 - .05, cx + bb.x, 640 + bb.y, rot + bb.r, 0, 900, () => { photoPiece(img, 0, 0, 310, 560, 0, 150 + i, { fy, zoom: 1.0 }); tape(0, -285, 120, .1 * (i - 1)); }, .4);
    slam(t0, cx - 120, 450 - 0, 0, () => 0);
    slam(t0 + .05, cx - 130, 380, rot, () => text('0' + (i + 1), 0, 0, 'AN', 130, YEL, 'left'), .12, 1.8);
    label.split('\n').forEach((ln, k) => slam(t0 + .1, cx, 1000 + k * 60, rot, () => text(ln, 0, 0, 'AB', 50, WHITE, 'center', -1), .12, 1.3));
  });
  slam(ws('esses'), 60, 1230, 0, () => text('esses são os três assuntos', 0, 0, 'IS', 72, WHITE), .1, 1.1);
  if (T >= ws('semana', 43)) slab('DA SEMANA.', 60, 1370, 'AB', 130, INK, YEL, prog(T, ws('semana', 43), .22), 24, 14, -5);
  scribbleArrow([[960, 1040], [1010, 1160], [960, 1260]], prog(T, ws('assuntos'), .4), YEL, 10, 34);
} });

// 14 PLANO 44.5 – 47.0
SC.push({ s: 44.5, e: 47.0, theme: 'paper', name: 'PLANO', draw() {
  slam(ws('Um'), 60, 330, 0, () => text('UM PLANO', 0, 0, 'AB', 160, INK, 'left', -8), .12);
  slam(ws('bem'), 60, 500, 0, () => text('BEM FEITO', 0, 0, 'AB', 160, INK, 'left', -8), .12);
  if (T >= ws('feito')) { const p = prog(T, ws('feito'), .35); c.strokeStyle = RED; c.lineWidth = 12; c.lineCap = 'round'; c.beginPath(); c.moveTo(60, 545); for (let x = 60; x < 60 + 940 * eOut(p); x += 30) c.lineTo(x, 545 + Math.sin(x * .05) * 8); c.stroke(); }
  slam(ws('vale'), 60, 650, 0, () => text('vale em', 0, 0, 'IS', 92, INK), .1, 1.15);
  if (T >= ws('qualquer')) slab('QUALQUER', 60, 810, 'AB', 130, WHITE, INK, prog(T, ws('qualquer'), .2), 22, 14, -5);
  if (T >= ws('cenário')) slab('CENÁRIO.', 60, 970, 'AB', 130, INK, YEL, prog(T, ws('cenário'), .2), 22, 14, -5);
  [[IMG.bc, -0.05, .65], [IMG.mapa, 0.03, .3], [IMG.capitolio, -0.02, .2]].forEach(([img, rot, fy], i) => {
    const t0 = ws('qualquer') + i * .18, bb = boil(30 + i, 1.5);
    slam(t0, 190 + i * 350 + bb.x, 1220 + bb.y, rot + bb.r, () => { photoPiece(img, 0, 0, 290, 340, 0, 160 + i, { fy }); check(70, 70, 90, RED, 14, prog(T, t0 + .2, .25)); }, .16, 1.8);
  });
} });

// 15 RECADO FINAL 47.0 – 52.1
SC.push({ s: 47.0, e: 52.2, theme: 'paper', name: 'RECADO', draw() {
  const b = boil(33, 2);
  slam(ws('Ficou'), 60, 245, 0, () => text('Ficou com alguma', 0, 0, 'IS', 68, INK), .1, 1.15);
  slam(ws('dúvida'), 60, 350, 0, () => text('DÚVIDA SOBRE A SUA', 0, 0, 'AB', 74, INK, 'left', -3), .12);
  if (T >= ws('carteira')) slab('CARTEIRA?', 60, 485, 'AB', 126, YEL, INK, prog(T, ws('carteira'), .22), 22, 14, -5);
  slide(47.05, 450 + b.x, 960 + b.y, -0.04 + b.r, 0, 1000, () => { photoPiece(IMG.lucas, 0, 0, 720, 660, 0, 171, { fy: .3 }); tape(0, -330, 220, 0.03); slab('LUCAS MEDEIROS', -330, 395, 'AB', 44, WHITE, INK, 1, 14, 10, -1); }, .45, eExpo);
  sticky(850, 760, 330, 0.1, ws('Me'), [['ME', 'AB', 80, -40], ['CHAMA', 'AB', 80, 40], ['aqui', 'IS', 90, 130]]);
  scribbleArrow([[880, 1010], [940, 1180], [760, 1230]], prog(T, ws('aqui', 49), .45), RED, 11, 38);
  const to = ws('Ótima');
  if (T >= to) {
    slam(to, 540, 1400, -0.04, () => slab('ÓTIMA TERÇA!', 0, 0, 'AB', 110, YEL, INK, prog(T, to, .2), 26, 16, -4, 'center'), .16, 2);
    for (let k = 0; k < 26; k++) { const tt = T - to; if (tt < 0) break; const a = rnd(k) * Math.PI * 2, v = 500 + rnd(k + 9) * 900;
      const x = 540 + Math.cos(a) * v * tt, y = 1400 + Math.sin(a) * v * tt + 900 * tt * tt; const col = [YEL, RED, INK, WHITE][k % 4];
      at(x, y, tt * 6 * (rnd(k + 3) - .5), 1, () => { c.fillStyle = col; c.fillRect(-14, -9, 28, 18); }); }
  }
} });

// ---------- transições ----------
const TRANS = [
  { t: 4.25, type: 'torn' }, { t: 6.3, type: 'slab', color: YEL }, { t: 8.3, type: 'flash' }, { t: 11.0, type: 'slab', color: INK },
  { t: 12.7, type: 'flash' }, { t: 16.1, type: 'slab', color: YEL }, { t: 19.7, type: 'torn' }, { t: 21.8, type: 'slab', color: RED },
  { t: 25.8, type: 'torn' }, { t: 31.0, type: 'slab', color: INK }, { t: 35.8, type: 'torn' }, { t: 40.2, type: 'slab', color: YEL },
  { t: 44.5, type: 'flash' }, { t: 47.0, type: 'torn' },
];
const sceneIdx = t => { for (let i = SC.length - 1; i >= 0; i--) if (t >= SC[i].s) return i; return 0; };
function drawScene(i) { const sc = SC[i]; c.save(); bg(sc.theme); sc.draw(); c.restore(); }

window.renderFrame = async function (n) {
  F = n; T = n / FPS;
  const i = sceneIdx(T), sc = SC[i];
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.filter = 'none';
  const tr = TRANS.find(k => T >= k.t - .25 && T < k.t + .35);
  if (tr && tr.type === 'torn' && T >= tr.t && T < tr.t + .32 && i > 0) {
    const keepT = T; T = tr.t - 1 / FPS; drawScene(i - 1); T = keepT;
    const p = eExpo(prog(T, tr.t, .32)), y0 = H * (1 - p);
    c.save(); c.beginPath(); c.moveTo(0, H); c.lineTo(0, y0);
    for (let x = 0; x <= W; x += 30) c.lineTo(x, y0 + (rnd(x + tr.t * 100) - .5) * 40); c.lineTo(W, H); c.closePath();
    c.shadowColor = 'rgba(0,0,0,.5)'; c.shadowBlur = 30; c.fillStyle = WHITE; c.fill(); c.restore();
    c.save(); c.beginPath(); c.moveTo(0, H); c.lineTo(0, y0 + 14);
    for (let x = 0; x <= W; x += 30) c.lineTo(x, y0 + 14 + (rnd(x + 7 + tr.t * 100) - .5) * 24); c.lineTo(W, H); c.closePath(); c.clip();
    drawScene(i); c.restore();
  } else drawScene(i);
  hud(sc.theme, i);
  captions(sc.theme);
  if (tr && tr.type === 'slab') {
    const d = .2; let x0 = 0, x1 = 0;
    if (T < tr.t) { const p = eInOut(prog(T, tr.t - d, d)); x1 = W * p * 1.15; } else { const p = eInOut(prog(T, tr.t, d)); x0 = W * p * 1.15; x1 = W * 1.15; }
    if (x1 > x0) { c.save(); c.fillStyle = tr.color; c.beginPath(); c.moveTo(x0 - 120, 0); c.lineTo(x1, 0); c.lineTo(x1 - 120, H); c.lineTo(x0 - 240, H); c.closePath(); c.fill();
      c.fillStyle = INK; c.fillRect(x1 - 60, 0, 10, H); c.restore(); }
  }
  if (tr && tr.type === 'flash' && T >= tr.t && T < tr.t + 2.5 / FPS) { c.save(); c.globalCompositeOperation = 'difference'; c.fillStyle = '#fff'; c.fillRect(0, 0, W, H); c.restore(); }
  grain();
};

function loadImg(src) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(src); im.src = src; }); }
(async () => {
  WORDS = await (await fetch('build/words2_fixed.json')).json();
  CAPS = await (await fetch('build/captions2.json')).json();
  const names = ['paper.jpg', 'bc.jpg', 'cong.jpg', 'esp.jpg', 'oil.jpg', 'mapa.jpg', 'tanker.jpg', 'capitolio.jpg', 'fed.jpg', 'crowd_a.jpg', 'lucas.jpg', 'lucas_busto.png', 'ship.png'];
  await Promise.all(names.map(async n => IMG[n.split('.')[0]] = await loadImg('build2/img/' + n)));
  await Promise.all(['40px "Archivo Black"', '40px Anton', '400 40px "Space Mono"', '700 40px "Space Mono"', 'italic 40px "Instrument Serif"'].map(f => document.fonts.load(f, 'ÁÉÍÓÚÃÕÇáéíóúãõç?')));
  makeGrain();
  window.READY = true;
})();
