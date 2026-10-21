// Pad calmo sintetizado, 84 BPM, um acorde por compasso, sem batida. Uso: node synth.mjs saida.wav [segundos]
import fs from 'fs';
const SR = 48000, DUR = +(process.argv[3] || 7), N = Math.round(SR * DUR), BAR = 240 / 84, XF = 0.6;
const midi = (n) => 440 * Math.pow(2, (n - 69) / 12);
const CHORDS = [[48, 55, 59, 64, 62], [45, 52, 55, 60, 59], [41, 48, 52, 57, 55], [43, 50, 55, 59, 62]]; // Cmaj9 Am9 Fmaj9 G6
const L = new Float32Array(N), R = new Float32Array(N);
const nChords = Math.ceil(DUR / BAR);
for (let c = 0; c < nChords; c++) {
  const t0 = c * BAR, t1 = t0 + BAR, last = c === nChords - 1;
  CHORDS[c % 4].forEach((note, vi) => {
    for (const det of [-0.08, 0.08]) {
      const f = midi(note) * Math.pow(2, det / 12), ph = (vi * 1.7 + det * 10) % 6.28;
      const pan = 0.5 + (vi % 2 ? 0.25 : -0.25) * Math.sign(det);
      const i0 = Math.max(0, Math.floor(t0 * SR)), i1 = Math.min(N, Math.ceil((last ? DUR : t1 + XF) * SR));
      for (let i = i0; i < i1; i++) {
        const t = i / SR;
        let a = c === 0 ? Math.min(1, t / 0.03) : Math.min(1, (t - t0) / XF);   // primeiro acorde já começa cheio
        if (!last && t > t1) a *= Math.max(0, 1 - (t - t1) / XF);
        const lfo = 1 + 0.15 * Math.sin(2 * Math.PI * 0.25 * t + vi);
        const w = Math.sin(2 * Math.PI * f * t + ph) + 0.25 * Math.sin(4 * Math.PI * f * t + ph) + 0.08 * Math.sin(6 * Math.PI * f * t);
        const v = w * a * lfo * (vi === 0 ? 0.9 : 0.5);
        L[i] += v * (1 - pan); R[i] += v * pan;
      }
    }
  });
}
let pl = 0, pr = 0; for (let i = 0; i < N; i++) { pl += 0.08 * (L[i] - pl); pr += 0.08 * (R[i] - pr); L[i] = pl; R[i] = pr; }
let pk = 1e-9; for (let i = 0; i < N; i++) pk = Math.max(pk, Math.abs(L[i]), Math.abs(R[i]));
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVEfmt ', 8); buf.writeUInt32LE(16, 16);
buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 4, 28);
buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) { buf.writeInt16LE(Math.round(L[i] / pk * 16000), 44 + i * 4); buf.writeInt16LE(Math.round(R[i] / pk * 16000), 46 + i * 4); }
fs.writeFileSync(process.argv[2], buf);
