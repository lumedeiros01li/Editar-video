// node contato.mjs [--eixo=log|linear] : folhas de contato em out/contact-sheets/<eixo>/
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { AQUI } from './util.mjs';
import { FPS, N_FRAMES } from './modelo.mjs';

const EIXO = process.argv.find((a) => a.startsWith('--eixo='))?.slice(7) === 'linear' ? 'linear' : 'log';
const FR = path.join(AQUI, 'out', 'frames', EIXO), DEST = path.join(AQUI, 'out', 'contact-sheets', EIXO);
fs.mkdirSync(DEST, { recursive: true });
// um quadro por momento do roteiro
const tempos = [0, 0.8, 2.5, 4.5, 6, 8, 9.9, 11, 11.7, 12.9, 14.2, 15.2, 16.15, (N_FRAMES - 1) / FPS];
[tempos.slice(0, 7), tempos.slice(7)].forEach((ts, n) => {
  const args = ['-y', '-hide_banner', '-loglevel', 'error'];
  ts.forEach((t) => args.push('-i', path.join(FR, `f_${String(Math.round(t * FPS)).padStart(4, '0')}.png`)));
  const W = 360, H = 640;
  const esc = ts.map((_, i) => `[${i}:v]scale=${W}:${H}[s${i}]`).join(';');
  const lay = ts.map((_, i) => `${(i % 4) * W}_${Math.floor(i / 4) * H}`).join('|');
  args.push('-filter_complex', `${esc};${ts.map((_, i) => `[s${i}]`).join('')}xstack=inputs=${ts.length}:layout=${lay}:fill=gray[o]`, '-map', '[o]', path.join(DEST, `folha-${n + 1}.png`));
  if (spawnSync('ffmpeg', args, { stdio: 'inherit' }).status !== 0) process.exit(1);
  console.log(`folha-${n + 1}.png:`, ts.map((t) => t.toFixed(2) + 's').join(', '));
});
