// node audio.mjs
// Trilha 100% sintetizada em código, determinística (ruído com semente mulberry32).
// Saída: out/audio/mix-final.wav (48 kHz, estéreo, -14 LUFS integrado, true peak < -1 dBTP)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { construir, DUR, T_FIM, T_CTA } from './modelo.mjs';

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

const mus = [new Float64Array(N), new Float64Array(N)]; // trilha
const fx = [new Float64Array(N), new Float64Array(N)];  // efeitos
const TAU = Math.PI * 2;
const hz = (semi) => 440 * Math.pow(2, semi / 12); // semitons a partir de A4

// soma uma voz mono em um barramento com pan (-1..1)
function voz(bus, t0, dur, gerador, ganho, pan = 0) {
  const i0 = Math.round(t0 * SR), n = Math.round(dur * SR);
  const gl = ganho * Math.cos(((pan + 1) * Math.PI) / 4), gr = ganho * Math.sin(((pan + 1) * Math.PI) / 4);
  for (let i = 0; i < n; i++) {
    const k = i0 + i;
    if (k < 0 || k >= N) continue;
    const v = gerador(i / SR, i);
    bus[0][k] += v * gl;
    bus[1][k] += v * gr;
  }
}

const env = (t, a, d, tau) => Math.min(t / a, 1) * Math.exp(-t / tau) * (t < d ? 1 : 0);

// ---------- música: Am | F | C | Em, 90 BPM ----------
const BPM = 90, BEAT = 60 / BPM, BAR = BEAT * 4;
const acordes = [
  { raiz: -24, notas: [-12, -5, 0, 3] },     // Am: A3 E4 A4 C5
  { raiz: -28, notas: [-16, -9, -4, 0] },    // F:  F3 C4 F4 A4 (relativo a A4)
  { raiz: -21, notas: [-9, -2, 3, 7] },      // C:  C4 G4 C5 E5 (raiz C3)
  { raiz: -17, notas: [-5, 2, 7, 10] },      // Em: E3.. notas G4 B4 E5 G5
];
const nBarras = Math.ceil(DUR / BAR) + 1;
for (let b = 0; b < nBarras; b++) {
  const ac = acordes[b % acordes.length], t0 = b * BAR;
  // pad: quatro notas, ataque lento, leve desafino para abrir o estéreo
  ac.notas.forEach((s, j) => {
    const f = hz(s - 12);
    voz(mus, t0 - 0.2, BAR + 0.9, (t) => {
      const e = Math.min(t / 0.7, 1) * Math.min((BAR + 0.9 - t) / 0.8, 1);
      return e * (Math.sin(TAU * f * t) + 0.5 * Math.sin(TAU * f * 1.004 * t) + 0.18 * Math.sin(TAU * f * 2 * t));
    }, 0.035, (j - 1.5) * 0.3);
  });
  // nota-raiz suave (sem batida)
  const fr = hz(ac.raiz);
  voz(mus, t0, BAR + 0.3, (t) => Math.sin(TAU * fr * t) * Math.min(t / 0.5, 1) * Math.min((BAR + 0.3 - t) / 0.6, 1), 0.07, 0);
  // arpejo em colcheias
  const padrao = [0, 2, 1, 3, 2, 3, 1, 2];
  for (let q = 0; q < 8; q++) {
    const tn = t0 + q * (BEAT / 2);
    if (tn >= DUR) break;
    const f = hz(ac.notas[padrao[q]]);
    voz(mus, tn, 0.9, (t) => {
      const e = Math.min(t / 0.004, 1) * Math.exp(-t / 0.2);
      return e * (Math.sin(TAU * f * t) + 0.35 * Math.sin(TAU * 2 * f * t) * Math.exp(-t / 0.08));
    }, 0.05, q % 2 ? 0.35 : -0.35);
  }
}
// eco da trilha (colcheia pontuada, com filtro passa-baixa no laço)
{
  const d = Math.round(BEAT * 0.75 * SR);
  for (let c = 0; c < 2; c++) {
    let lp = 0;
    const b = mus[c];
    for (let i = d; i < N; i++) {
      lp += 0.35 * (b[i - d] * 0.32 - lp);
      b[i] += lp;
    }
  }
}
// entrada e saída suaves da trilha
for (let c = 0; c < 2; c++) for (let i = 0; i < N; i++) {
  const t = i / SR;
  mus[c][i] *= Math.min(t / 0.4, 1) * Math.min((DUR - t) / 1.2, 1);
}

// ---------- efeitos ----------
const penta = [0, 3, 5, 7, 10]; // A menor pentatônica
const escala = [];
for (let o = 0; o < 2; o++) for (const s of penta) escala.push(s + 12 * o); // A4..G6
const brFinal = M.serie.BRA[M.P_MAX];
const eventos = { ticks: [], whoosh: [], ping: [], assentamento: T_FIM, clique: T_CTA };

// tick de ano: um por ano de dado, tom sobe com o índice do Brasil
for (const tk of M.ticks) {
  const norm = (tk.brasil - 100) / (brFinal - 100);
  const grau = Math.min(escala.length - 1, Math.floor(norm * escala.length));
  const f = hz(escala[grau]);
  eventos.ticks.push({ ano: tk.ano, t: tk.t, freq: f });
  voz(fx, tk.t, 0.3, (t) => Math.min(t / 0.002, 1) * Math.exp(-t / 0.05) * (Math.sin(TAU * f * t) + 0.3 * Math.sin(TAU * 2 * f * t)),
    0.2, ((tk.k % 5) - 2) * 0.08);
}

// whoosh curto: ruído com semente passando por filtro passa-banda em varredura
function whoosh(t0, seed, dur = 0.42, ganho = 0.16) {
  for (let c = 0; c < 2; c++) {
    const rnd = mulberry32(seed + c * 977);
    let low = 0, band = 0;
    const n = Math.round(dur * SR), i0 = Math.round(t0 * SR);
    for (let i = 0; i < n; i++) {
      const t = i / SR, u = t / dur;
      const fc = 350 * Math.pow(3200 / 350, u);
      const f = 2 * Math.sin((Math.PI * fc) / SR), q = 0.35;
      const x = rnd() * 2 - 1;
      low += f * band;
      const high = x - low - q * band;
      band += f * high;
      const e = Math.pow(Math.sin(Math.PI * Math.min(u, 1)), 2);
      const k = i0 + i;
      if (k >= 0 && k < N) fx[c][k] += band * e * ganho * 3;
    }
  }
  eventos.whoosh.push(t0);
}
whoosh(0.28, 101);                     // entrada do título
for (const m of M.marcos) whoosh(m.t - 0.06, 200 + m.limiar, 0.3, 0.12); // chip de marco

// ping suave em cada marco do Brasil
for (const m of M.marcos) {
  const f = hz(19); // E6
  eventos.ping.push(m.t + 0.12);
  voz(fx, m.t + 0.12, 1.4, (t) => Math.min(t / 0.003, 1) * Math.exp(-t / 0.35) * (Math.sin(TAU * f * t) + 0.25 * Math.sin(TAU * f * 2.01 * t)), 0.13, 0.15);
}

// pluck de assentamento, sem grave
[[-12, 0], [-5, 0.045], [0, 0.09]].forEach(([s, atraso], j) => {
  const f = hz(s);
  voz(fx, T_FIM + atraso, 2, (t) => Math.min(t / 0.004, 1) * Math.exp(-t / 0.55) * (Math.sin(TAU * f * t) + 0.3 * Math.sin(TAU * 2 * f * t) * Math.exp(-t / 0.2)), 0.1, (j - 1) * 0.25);
});

// clique seco na entrada do CTA
{
  const rnd = mulberry32(777);
  let prev = 0;
  voz(fx, T_CTA, 0.05, (t) => {
    const x = rnd() * 2 - 1, hp = x - prev; prev = x;
    return (hp * Math.exp(-t / 0.004) * 0.6 + Math.sin(TAU * 1800 * t) * Math.exp(-t / 0.006) * 0.5);
  }, 0.35, 0);
}

// níveis relativos antes da normalização (a trilha precisa ficar abaixo dos efeitos)
const rms = (b) => 20 * Math.log10(Math.sqrt(b[0].reduce((s, x) => s + x * x, 0) / N) + 1e-12);
const pico = (b) => 20 * Math.log10(b[0].reduce((m, x) => Math.max(m, Math.abs(x)), 0) + 1e-12);
console.log(`trilha: rms ${rms(mus).toFixed(1)} dB, pico ${pico(mus).toFixed(1)} dB | efeitos: rms ${rms(fx).toFixed(1)} dB, pico ${pico(fx).toFixed(1)} dB`);

// ---------- mixagem e arquivo ----------
const mix = [new Float32Array(N), new Float32Array(N)];
for (let c = 0; c < 2; c++) for (let i = 0; i < N; i++) mix[c][i] = mus[c][i] * 0.9 + fx[c][i];

function escreverWav(arq, canais, sr) {
  const n = canais[0].length, buf = Buffer.alloc(44 + n * 2 * 4);
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + n * 8, 4); buf.write('WAVEfmt ', 8);
  buf.writeUInt32LE(16, 16); buf.writeUInt16LE(3, 20); buf.writeUInt16LE(2, 22);
  buf.writeUInt32LE(sr, 24); buf.writeUInt32LE(sr * 8, 28); buf.writeUInt16LE(8, 32); buf.writeUInt16LE(32, 34);
  buf.write('data', 36); buf.writeUInt32LE(n * 8, 40);
  for (let i = 0; i < n; i++) { buf.writeFloatLE(canais[0][i], 44 + i * 8); buf.writeFloatLE(canais[1][i], 48 + i * 8); }
  fs.writeFileSync(arq, buf);
}
const bruto = path.join(OUT, 'mix-bruto.wav'), final = path.join(OUT, 'mix-final.wav');
escreverWav(bruto, mix, SR);

// loudnorm em dois passos: -14 LUFS integrado, true peak -1,5 dBTP
const alvo = 'I=-14:TP=-1.5:LRA=11';
const p1 = spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', bruto, '-af', `loudnorm=${alvo}:print_format=json`, '-f', 'null', '-'], { encoding: 'utf8' });
const j = JSON.parse(p1.stderr.slice(p1.stderr.lastIndexOf('{'), p1.stderr.lastIndexOf('}') + 1));
const af = `loudnorm=${alvo}:measured_I=${j.input_i}:measured_TP=${j.input_tp}:measured_LRA=${j.input_lra}:measured_thresh=${j.input_thresh}:offset=${j.target_offset}:linear=true:print_format=summary`;
const p2 = spawnSync('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-i', bruto, '-af', af, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', final], { encoding: 'utf8' });
if (p2.status !== 0) { console.error(p2.stderr); process.exit(1); }
fs.writeFileSync(path.join(OUT, 'eventos.json'), JSON.stringify(eventos, null, 2));
console.log(`áudio ok: medido ${j.input_i} LUFS / ${j.input_tp} dBTP antes, alvo -14 LUFS, ${eventos.ticks.length} ticks`);
