// node audio.mjs
// Trilha 100% sintetizada em código, determinística (ruído com semente mulberry32).
// Saída: out/audio/mix-final.wav (48 kHz, estéreo, -14 LUFS integrado, true peak < -1 dBTP)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { construir, DUR, T_CONGELA, T_REVELA, T_RANKING, T_VOLTA } from './modelo.mjs';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(AQUI, 'out', 'audio');
fs.mkdirSync(OUT, { recursive: true });

const SR = 48000;
const N = Math.round(SR * DUR);
const dados = JSON.parse(fs.readFileSync(path.join(AQUI, 'dados.json'), 'utf8'));
const M = construir(dados);

function mulberry32(a) {
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const mus = [new Float64Array(N), new Float64Array(N)];
const fx = [new Float64Array(N), new Float64Array(N)];
const TAU = Math.PI * 2;
const hz = (semi) => 440 * Math.pow(2, semi / 12); // semitons a partir de A4

function voz(bus, t0, dur, gerador, ganho, pan = 0) {
  const i0 = Math.round(t0 * SR), n = Math.round(dur * SR);
  const gl = ganho * Math.cos(((pan + 1) * Math.PI) / 4), gr = ganho * Math.sin(((pan + 1) * Math.PI) / 4);
  for (let i = 0; i < n; i++) {
    const k = i0 + i;
    if (k < 0 || k >= N) continue;
    const v = gerador(i / SR);
    bus[0][k] += v * gl;
    bus[1][k] += v * gr;
  }
}
const pluck = (f, tau, brilho = 0.35) => (t) => Math.min(t / 0.004, 1) * Math.exp(-t / tau) *
  (Math.sin(TAU * f * t) + brilho * Math.sin(TAU * 2 * f * t) * Math.exp(-t / (tau * 0.4)));

// ---------- música: Am | F | C | Em, 120 BPM (batida de 0,5 s) ----------
const BEAT = 0.5, BAR = BEAT * 4;
const acordes = [
  { raiz: -24, notas: [-12, -5, 0, 3] },  // Am
  { raiz: -28, notas: [-16, -9, -4, 0] }, // F
  { raiz: -21, notas: [-9, -2, 3, 7] },   // C
  { raiz: -17, notas: [-5, 2, 7, 10] },   // Em
];
const lento = (t) => (t >= 5 && t < 6) || (t >= 8.5 && t < 9.5);   // câmera lenta: arpejo em semínimas
const silencioArp = (t) => t >= T_CONGELA && t < T_REVELA;          // suspense: só o pad
for (let b = 0; b * BAR < DUR; b++) {
  const ac = acordes[b % acordes.length], t0 = b * BAR;
  ac.notas.forEach((s, j) => {
    const f = hz(s - 12);
    voz(mus, t0 - 0.15, BAR + 0.6, (t) => {
      const e = Math.min(t / 0.4, 1) * Math.min((BAR + 0.6 - t) / 0.5, 1);
      return e * (Math.sin(TAU * f * t) + 0.5 * Math.sin(TAU * f * 1.004 * t) + 0.15 * Math.sin(TAU * f * 2 * t));
    }, 0.03, (j - 1.5) * 0.3);
  });
  const fr = hz(ac.raiz);
  voz(mus, t0, BAR + 0.2, (t) => Math.sin(TAU * fr * t) * Math.min(t / 0.3, 1) * Math.min((BAR + 0.2 - t) / 0.4, 1), 0.06, 0);
  const padrao = [0, 2, 1, 3, 2, 3, 1, 2];
  for (let q = 0; q < 8; q++) {
    const tn = t0 + q * (BEAT / 2);
    if (tn >= DUR || silencioArp(tn) || (lento(tn) && q % 2)) continue;
    voz(mus, tn, 0.8, pluck(hz(ac.notas[padrao[q]]), lento(tn) ? 0.35 : 0.16), lento(tn) ? 0.055 : 0.045, q % 2 ? 0.35 : -0.35);
  }
  // shaker leve nas colcheias (pulso sem bumbo)
  for (let q = 0; q < 8; q++) {
    const tn = t0 + q * (BEAT / 2);
    if (tn >= DUR || silencioArp(tn) || lento(tn)) continue;
    const rnd = mulberry32(5000 + b * 8 + q);
    let ant = 0;
    voz(mus, tn, 0.06, (t) => { const x = rnd() * 2 - 1, h = x - ant; ant = x; return h * Math.exp(-t / 0.012); }, q % 2 ? 0.025 : 0.04, 0.2);
  }
}
// eco com filtro no laço
{
  const d = Math.round(BEAT * 0.75 * SR);
  for (let c = 0; c < 2; c++) {
    let lp = 0;
    for (let i = d; i < N; i++) { lp += 0.35 * (mus[c][i - d] * 0.3 - lp); mus[c][i] += lp; }
  }
}
// bordas curtas (o reel repete em loop)
for (let c = 0; c < 2; c++) for (let i = 0; i < N; i++) {
  const t = i / SR;
  mus[c][i] *= Math.min(t / 0.03, 1) * Math.min((DUR - t) / 0.03, 1);
}

// ---------- efeitos ----------
const penta = [0, 3, 5, 7, 10];
const escala = [];
for (let o = 0; o < 2; o++) for (const s of penta) escala.push(s + 12 * o);
const eventos = { ticks: [], flashes: [], revelacoes: [], riser: T_CONGELA, assentamento: T_RANKING, volta: T_VOLTA };

// tick por troca de ano; o tom sobe com o maior valor já atingido (escala log)
const topo = Math.log(Math.max(...M.ids.map((id) => Math.max(...M.serie[id]))) / 100);
let acum = 100;
for (const tk of M.ticks) {
  acum = Math.max(acum, M.lider(tk.k + 1));
  const grau = Math.min(escala.length - 1, Math.floor((Math.log(acum / 100) / topo) * escala.length));
  const f = hz(escala[grau]);
  eventos.ticks.push({ ano: tk.ano, t: tk.t, freq: f });
  voz(fx, tk.t, 0.25, (t) => Math.min(t / 0.002, 1) * Math.exp(-t / 0.045) * (Math.sin(TAU * f * t) + 0.3 * Math.sin(TAU * 2 * f * t)), 0.17, ((tk.k % 5) - 2) * 0.08);
}

function varredura(t0, seed, dur, ganho, de, ate) {
  for (let c = 0; c < 2; c++) {
    const rnd = mulberry32(seed + c * 977);
    let low = 0, band = 0;
    const n = Math.round(dur * SR), i0 = Math.round(t0 * SR);
    for (let i = 0; i < n; i++) {
      const u = i / n, fc = de * Math.pow(ate / de, u);
      const f = 2 * Math.sin((Math.PI * fc) / SR), x = rnd() * 2 - 1;
      low += f * band; const high = x - low - 0.35 * band; band += f * high;
      const k = i0 + i;
      if (k >= 0 && k < N) fx[c][k] += band * Math.pow(Math.sin(Math.PI * u), 2) * ganho * 3;
    }
  }
}
// flashes: whoosh curto + ping
for (const fl of M.flashes) {
  eventos.flashes.push({ t: fl.t, texto: fl.texto });
  varredura(fl.t - 0.08, Math.round(fl.t * 100), 0.3, 0.11, 400, 3200);
  const f = hz(19);
  voz(fx, fl.t + 0.06, 1.2, pluck(f, 0.32, 0.25), 0.12, 0.15);
}
// suspense: subida de ruído filtrado até a primeira revelação
varredura(T_CONGELA, 4242, T_REVELA - T_CONGELA, 0.07, 250, 2400);
// revelações do último ao primeiro, subindo na escala; o vencedor ganha um acorde
const notasRevela = [3, 5, 7, 10, 12];
M.ordemFinal.forEach((id, k) => {
  const t0 = M.revela[id];
  eventos.revelacoes.push({ id, t: t0 });
  voz(fx, t0, 1.2, pluck(hz(notasRevela[k]), 0.3), 0.15, (k - 2) * 0.15);
  if (id === M.vencedor) [0, 7, 12].forEach((s, j) => voz(fx, t0 + 0.03 * j, 1.8, pluck(hz(s), 0.6), 0.09, (j - 1) * 0.3));
});
// assentamento do ranking, sem grave
[[-12, 0], [-5, 0.045], [0, 0.09]].forEach(([s, a], j) => voz(fx, T_RANKING + a, 1.5, pluck(hz(s), 0.5, 0.3), 0.08, (j - 1) * 0.25));
// rebobinagem para o loop: varredura descendo
varredura(T_VOLTA, 9090, 0.32, 0.1, 3000, 300);

const rms = (b) => 20 * Math.log10(Math.sqrt(b[0].reduce((s, x) => s + x * x, 0) / N) + 1e-12);
const pico = (b) => 20 * Math.log10(b[0].reduce((m, x) => Math.max(m, Math.abs(x)), 0) + 1e-12);
console.log(`trilha: rms ${rms(mus).toFixed(1)} dB, pico ${pico(mus).toFixed(1)} dB | efeitos: rms ${rms(fx).toFixed(1)} dB, pico ${pico(fx).toFixed(1)} dB`);

// ---------- mixagem ----------
const mix = [new Float32Array(N), new Float32Array(N)];
for (let c = 0; c < 2; c++) for (let i = 0; i < N; i++) mix[c][i] = mus[c][i] * 0.9 + fx[c][i];
function escreverWav(arq, canais, sr) {
  const n = canais[0].length, buf = Buffer.alloc(44 + n * 8);
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + n * 8, 4); buf.write('WAVEfmt ', 8);
  buf.writeUInt32LE(16, 16); buf.writeUInt16LE(3, 20); buf.writeUInt16LE(2, 22);
  buf.writeUInt32LE(sr, 24); buf.writeUInt32LE(sr * 8, 28); buf.writeUInt16LE(8, 32); buf.writeUInt16LE(32, 34);
  buf.write('data', 36); buf.writeUInt32LE(n * 8, 40);
  for (let i = 0; i < n; i++) { buf.writeFloatLE(canais[0][i], 44 + i * 8); buf.writeFloatLE(canais[1][i], 48 + i * 8); }
  fs.writeFileSync(arq, buf);
}
const bruto = path.join(OUT, 'mix-bruto.wav'), final = path.join(OUT, 'mix-final.wav');
escreverWav(bruto, mix, SR);
const alvo = 'I=-14:TP=-1.5:LRA=11';
const p1 = spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', bruto, '-af', `loudnorm=${alvo}:print_format=json`, '-f', 'null', '-'], { encoding: 'utf8' });
const j = JSON.parse(p1.stderr.slice(p1.stderr.lastIndexOf('{'), p1.stderr.lastIndexOf('}') + 1));
const af = `loudnorm=${alvo}:measured_I=${j.input_i}:measured_TP=${j.input_tp}:measured_LRA=${j.input_lra}:measured_thresh=${j.input_thresh}:offset=${j.target_offset}:linear=true:print_format=summary`;
const p2 = spawnSync('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-i', bruto, '-af', af, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', final], { encoding: 'utf8' });
if (p2.status !== 0) { console.error(p2.stderr); process.exit(1); }
fs.writeFileSync(path.join(OUT, 'eventos.json'), JSON.stringify(eventos, null, 2));
console.log(`áudio ok: medido ${j.input_i} LUFS / ${j.input_tp} dBTP antes, ${eventos.ticks.length} ticks, ${eventos.revelacoes.length} revelações`);
